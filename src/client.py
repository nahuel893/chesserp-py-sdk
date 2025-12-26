import requests
import logging
import re
import os
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urljoin
from dotenv import load_dotenv

# Local imports 
from src.config.settings import Settings, get_settings
from src.exceptions import AuthError, ApiError, ChessError
from src.models.sales import Sale
from src.models.inventory import Articulo, StockFisico
from src.models.clients import Cliente
from src.models.orders import Pedido
from src.models.routes import RutaVenta
from src.models.staff import PersonalComercial
from src.models.marketing import JerarquiaMkt
from src.logger import get_logger

# Configure logger
logger = get_logger(__name__)

load_dotenv()
class ChessClient:
    """
    Cliente principal para la API de ChessERP.
    Maneja autenticación y llamadas a endpoints.
    """

    def __init__(self, settings: Optional[Settings] = None, instance: str = 'b'):
        """
        Inicializa el cliente.
        
        Args:
            settings: Instancia de configuración (opcional).
            instance: 'b' o 's' para seleccionar la instancia configurada en .env
        """
        self.settings = settings or get_settings()
        self.config = self.settings.get_instance_config(instance)
        
        # No usamos requests.Session para tener control explícito sobre las cookies en cada request
        self.base_headers = {}

        self.base_url = str(self.config.api_url) + self.settings.api_path
        self.auth_url = str(self.config.api_url) + self.settings.api_path_login
        self._session_id: Optional[str] = None
        self.cookies = None

    def login(self) -> str:
        """
        Realiza el login y almacena el sessionId.
        """
        credentials = {
            "usuario": self.config.username,
            "password": self.config.password
        }
        logger.info(f"Authenticating as {self.config.username}...")
        
        try:
            # Usar requests.post directamente, no una sesión persistente
            response = requests.post(self.auth_url, json=credentials)
            
            if response.status_code != 200:
                raise AuthError(f"Login failed: {response.status_code} - {response.text}")
            data = response.json()
            logger.debug(f"Cookies post login {response.cookies}")
            self.cookies = response.cookies
            session_id = data.get('sessionId')
            logger.debug(f"Response data: {data}")

            if not session_id:
                raise AuthError("No sessionId returned from API")
            self._session_id = session_id
            logger.info("Authentication successful.")

            # Construimos el header para todas las request
            self.base_headers = {
                "Cookie": self._session_id}

            return self._session_id
            
        except requests.RequestException as e:
            raise AuthError(f"Connection error during login: {str(e)}")

    def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """
        Realiza petición GET manejando sesión y errores.
        """
        if not self._session_id:
            logger.debug("Not find sessionId")
            self.login()
            
        # Clean endpoint
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        url = self.base_url + endpoint
        headers = self.base_headers 
        logger.debug(f"Processing GET request",)
        logger.debug(f"GET request: url={url}, headers={headers}")

        try:
            # Usar requests.get directamente
            response = requests.get(url, params=params, headers=headers)
            logger.debug(f"Response text: {response.text[0:10]}")
            if response.status_code == 401:
                logger.warning("Token expired (401). Retrying login...")
                self.login() # Re-login para obtener un nuevo _session_id
                # Reconstruir headers con la nueva cookie y reintentar la petición
                headers["Cookie"] = self._session_id if "JSESSIONID=" in self._session_id else f"JSESSIONID={self._session_id}"
                response = requests.get(url, params=params, headers=headers)

            if response.status_code != 200:
                raise apierror(response.status_code, f"request to {endpoint} failed", response.text)

            json_data = response.json()
        #    logger.debug(f"{json_data}")
            if isinstance(json_data, list) and len(json_data) == 0:
                logger.debug(f"Empty list returned. Raw response: {response.text}")
            
            return json_data
        except requests.RequestException as e:
            raise ApiError(500, f"Connection error: {str(e)}")

    def _parse_list(self, data: Any, model_class: Any) -> List[Any]:
        """
        Intenta parsear una lista de diccionarios a modelos Pydantic.
        Si un elemento falla, lo loguea y continúa con el resto.
        """
        if not isinstance(data, list):
            logger.warning(f"Se esperaba una lista, se recibió: {type(data)}")
            return []
            
        parsed_items = []
        for index, item in enumerate(data):
            try:
                parsed_items.append(model_class(**item))
            except Exception as e:
                # Loguear el error específico y el ítem que falló
                logger.error(f"Error parseando ítem #{index} en {model_class.__name__}: {e}. Ítem fallido: {item}") # Añadido el ítem fallido para mejor debug
                # Opcional: Podrías agregar el item crudo si quieres no perderlo
                # parsed_items.append(item) 
                
        return parsed_items

    # --- Ventas ---
    def get_sales_raw(self,
                      fecha_desde: str,
                      fecha_hasta: str,
                      empresas: str = "",
                      detallado: bool = False,
                      nro_lote: int = 1) -> Dict[str, Any]:
        """
        Obtiene comprobantes de ventas SIN validación (raw JSON).
        Retorna un lote específico.
        Útil para pipelines ETL y arquitectura medallion.

        Returns:
            Dict con estructura:
            {
                "dsReporteComprobantesApi": {"VentasResumen": [...]},
                "cantComprobantesVentas": "Numero de lote obtenido: 1/70. ..."
            }
        """
        params = {
            "fechaDesde": fecha_desde,
            "fechaHasta": fecha_hasta,
            "empresas": empresas,
            "detallado": str(detallado).lower(),
            "nroLote": nro_lote
        }

        return self._get("ventas/", params)

    def get_sales(self,
                  fecha_desde: str,
                  fecha_hasta: str,
                  empresas: str = "",
                  detallado: bool = False,
                  ) -> List[Sale]
        """
        Obtiene comprobantes de ventas validados con Pydantic (todos los lotes).
        """
        # Primera request para obtener el primer lote y el total de lotes
        response_data = self.get_sales_raw(fecha_desde, fecha_hasta, empresas, detallado, nro_lote=1)

        # Inicializar lista acumuladora
        sales_data = []

        # Extraer el primer lote de datos
        if isinstance(response_data, dict):
            sales_list = response_data.get("dsReporteComprobantesApi", {}).get("VentasResumen")

            if sales_list is not None:
                sales_data.extend(self._parse_list(sales_list, Sale))
                logger.info(f"Lote 1 procesado: {len(sales_list)} registros")

            # Obtener el total de lotes usando regex
            # Formato: "Numero de lote obtenido: 1/70. Cantidad de comprobantes totales: 69041"
            cant_comprobantes_str = response_data.get("cantComprobantesVentas", "")
            logger.debug(f"cantComprobantesVentas raw: {cant_comprobantes_str}")

            match = re.search(r'(\d+)/(\d+)', cant_comprobantes_str)
            if match:
                lote_actual = int(match.group(1))
                total_lotes = int(str(match.group(2)).replace('.', ''))
                logger.info(f"Total de lotes a procesar: {total_lotes}")

                # Iterar sobre los lotes restantes (si hay más de 1)
                for i in range(lote_actual + 1, total_lotes + 1):
                    response_data = self.get_sales_raw(fecha_desde, fecha_hasta, empresas, detallado, nro_lote=i)

                    if isinstance(response_data, dict):
                        list_ = response_data.get("dsReporteComprobantesApi", {}).get("VentasResumen")

                        if list_ is not None:
                            sales_data.extend(self._parse_list(list_, Sale))
                            logger.info(f"Lote {i}/{total_lotes} procesado: {len(list_)} registros")
            else:
                logger.warning(f"No se pudo parsear total de lotes de: {cant_comprobantes_str}. Asumiendo 1 lote.")

        logger.info(f"Total de ventas obtenidas: {len(sales_data)}")
        return sales_data 
        
    # --- Inventario ---
    def get_articles_raw(self,
                         articulo: int = 0,
                         nro_lote: int = 1,
                         anulado: bool = False) -> Dict[str, Any]:
        """
        Obtiene catálogo de artículos SIN validación (raw JSON).
        Retorna un lote específico.

        Returns:
            Dict con estructura:
            {
                "Articulos": {"eArticulos": [...]},
                "cantArticulos": "Numero de lote obtenido: 2/22. Cantidad de articulos totales: 2103"
            }
        """
        params = {
            "articulo": articulo if articulo > 0 else "",
            "nroLote": nro_lote,
            "anulado": str(anulado).lower()
        }
        return self._get("articulos/", params)

    def get_articles(self,
                     articulo: int = 0,
                     anulado: bool = False) -> List[Articulo]:
        """
        Obtiene catálogo de artículos validados con Pydantic (todos los lotes).

        Args:
            articulo: ID específico (0 para todos)
            anulado: Incluir anulados
        """
        # Primera request para obtener el primer lote y el total de lotes
        response_data = self.get_articles_raw(articulo, nro_lote=1, anulado=anulado)

        # Inicializar lista acumuladora
        articles_data = []

        # Extraer el primer lote de datos
        if isinstance(response_data, dict):
            articles_list = response_data.get("Articulos", {}).get("eArticulos")

            if articles_list is not None:
                articles_data.extend(self._parse_list(articles_list, Articulo))
                logger.info(f"Lote 1 procesado: {len(articles_list)} artículos")

            # Obtener el total de lotes usando regex
            # Formato: "Numero de lote obtenido: 2/22. Cantidad de articulos totales: 2103"
            cant_articulos_str = response_data.get("cantArticulos", "")
            logger.debug(f"cantArticulos raw: {cant_articulos_str}")

            match = re.search(r'(\d+)/(\d+)', cant_articulos_str)
            if match:
                lote_actual = int(match.group(1))
                total_lotes = int(match.group(2))
                logger.info(f"Total de lotes a procesar: {total_lotes}")

                # Iterar sobre los lotes restantes (si hay más de 1)
                for i in range(lote_actual + 1, total_lotes + 1):
                    response_data = self.get_articles_raw(articulo, nro_lote=i, anulado=anulado)

                    if isinstance(response_data, dict):
                        list_ = response_data.get("Articulos", {}).get("eArticulos")

                        if list_ is not None:
                            articles_data.extend(self._parse_list(list_, Articulo))
                            logger.info(f"Lote {i} procesado: {len(list_)} artículos")
            else:
                logger.warning(f"No se pudo parsear total de lotes de: {cant_articulos_str}. Asumiendo 1 lote.")

        logger.info(f"Total de artículos obtenidos: {len(articles_data)}")
        return articles_data

    def get_stock_raw(self,
                      id_deposito: int,
                      frescura: bool = False,
                      fecha: str = "") -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Obtiene stock físico SIN validación (raw JSON).
        """
        params = {
            "idDeposito": id_deposito,
            #"frescura": str(frescura).lower(),
            "DD-MM-AAAA": fecha
        }
        return self._get("stock/", params)

    def get_stock(self,
                  id_deposito: int,
                  frescura: bool = False,
                  fecha: str = "") -> List[StockFisico]:
        """
        Obtiene stock físico validado con Pydantic.
        Args:
            id_deposito: Obligatorio
            frescura: Apertura por frescura
            fecha: DD-MM-AAAA (Opcional, cálculo histórico)
        """
        raw_data = self.get_stock_raw(id_deposito, fecha)
        raw_data = raw_data.get('dsStockFisicoApi').get("dsStock") # retorna la lista de articulos
        return self._parse_list(raw_data, StockFisico)

    # --- Clientes ---
    def get_customers_raw(self,
                          #clientes: int | list | None,
                          #sucursal: int | list | None,
                          anulado: bool = False,
                          nro_lote: int = 1) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Busca clientes SIN validación (raw JSON).
        Retorna todos los clientes.
        Future Refactoring: Agregar logica para retornar en base a una lista de clientes o lista de sucursales. 
        """

        # si no se especifica cliente entonces, entonces trae todos
        params = {
            "cliente": 0,
            "anulado": str(anulado).lower(),
            "nroLote": nro_lote
        }

        return self._get("clientes/", params)
    
    def get_customers(self,
                      anulado: bool = False,
                      nro_lote: int = 0) -> List[Cliente]:
        """
        Busca clientes validados con Pydantic.
        """
        # Inicializar lista acumuladora
        customers_data = []

        if nro_lote == 0:
            # Primera request  para obtener el primer lote y el total de lotes
            response_data = self.get_customers_raw( nro_lote=1)

            # Extraer el primer lote de datos
            if isinstance(response_data, dict):
                customers_list = response_data.get("Clientes", {}).get("eClientes")

                if customers_list is not None:
                    customers_data.extend(self._parse_list(customers_list, Cliente))
                    logger.info(f"Lote 1 procesado: {len(customers_list)} registros")

                # Obtener el total de lotes usando regex
                # Formato: "Numero de lote obtenido: 1/70. Cantidad de comprobantes totales: 69041"
                cant_clientes_str = response_data.get("cantClientes", "")
                logger.debug(f"cantClientes: {cant_clientes_str}")

                match = re.search(r'(\d+)/(\d+)', cant_clientes_str)
                if match:
                    lote_actual = int(match.group(1))
                    total_lotes = int(match.group(2))
                    logger.info(f"Total de lotes a procesar: {total_lotes}")

                    # Iterar sobre los lotes restantes (si hay más de 1)
                    for i in range(lote_actual+1, total_lotes+1):
                        response_data = self.get_customers_raw( nro_lote=1)

                        if isinstance(response_data, dict):
                            list_ = response_data.get("Clientes", {}).get("eClientes")

                            if list_ is not None:
                                customers_data.extend(self._parse_list(list_, Cliente))
                                logger.info(f"Lote {i} procesado: {len(list_)} registros")
                else:
                    logger.warning(f"No se pudo parsear total de lotes de: {cant_clientes_str}. Asumiendo 1 lote.")

            logger.info(f"Total de clientes obtenidas: {len(customers_data)}")
        else:
            response_data = self.get_customers_raw(nro_lote=nro_lote)
            list_ = response_data.get("Clientes", {}).get("eClientes")

            if list_ is not None:
                customers_data.extend(self._parse_list(list_, Cliente))
                logger.info(f"Lote {nro_lote} procesado: {len(list_)} registros")

        return customers_data



    # --- Pedidos ---
    def get_orders_raw(self,
                       fecha_entrega: str = "",
                       fecha_pedido: str = "",
                       facturado: bool = False) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Busca pedidos SIN validación (raw JSON).
        """
        params = {
            "fechaEntrega": fecha_entrega,
            "fechaPedido": fecha_pedido,
            "facturado": str(facturado).lower()
        }
        return self._get("pedidos/", params)

    def get_orders(self,
                   fecha_entrega: str = "",
                   fecha_pedido: str = "",
                   facturado: bool = False) -> List[Pedido]:
        """
        Busca pedidos validados con Pydantic.
        Args:
            fecha_entrega: Fecha de entrega
            fecha_pedido: Fecha de alta
            facturado: Filtrar facturados
        """
        raw_data = self.get_orders_raw(fecha_entrega, fecha_pedido, facturado)
        # Extraer lista de pedidos del JSON
        # Estructura: {"pedidos": [...]}
        pedidos_list = raw_data.get('pedidos', []) if isinstance(raw_data, dict) else raw_data
        return self._parse_list(pedidos_list, Pedido)

    # --- Personal ---

    def get_staff_raw(self,
                      sucursal: int = 0,
                      personal: int = 0) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Busca personal comercial SIN validación (raw JSON).
        """
        params = {
            "sucursal": sucursal if sucursal > 0 else "",
            "personal": personal if personal > 0 else ""
        }
        return self._get("personalComercial/", params)

    def get_staff(self,
                  sucursal: int = 0,
                  personal: int = 0) -> List[PersonalComercial]:
        """
        Busca personal comercial validado con Pydantic.
        """
        raw_data = self.get_staff_raw(sucursal, personal)
        # Extraer lista de personal del JSON
        # Estructura: {"PersonalComercial": {"ePersCom": [...]}}
        staff_list = raw_data.get('PersonalComercial', {}).get('ePersCom', []) if isinstance(raw_data, dict) else raw_data
        return self._parse_list(staff_list, PersonalComercial)

    # --- Rutas ---

    def get_routes_raw(self,
                       sucursal: int = 1,
                       fuerza_venta: int = 1,
                       modo_atencion: int = 0,
                       anulado: bool = False):
        """
        Busca rutas de venta SIN validación (raw JSON).
        """
        params = {
            "sucursal": sucursal,
            "fuerzaventa": fuerza_venta,
            "anulada": str(anulado).lower()  # PDF dice "anulada" en query param pg 36
        }
        return self._get("rutasVenta/", params)

    def get_routes(self,
                   sucursal: int = 1,
                   fuerza_venta: int = 1,
                   modo_atencion: str = "PRE",
                   anulado: bool = False) -> List[RutaVenta]:
        """
        Busca rutas de venta validadas con Pydantic.
        """
        raw_data = self.get_routes_raw(sucursal=sucursal, 
                                       fuerza_venta=fuerza_venta,
                                       anulado=anulado)
        # Extraer lista de rutas del JSON
        # Estructura probable: {"rutasVenta": [...]} o {"RutasVenta": {"eRutas": [...]}}
            # Intentar diferentes estructuras posibles
        routes_list = raw_data.get('RutasVenta')
        routes_list =  routes_list.get('eRutasVenta')
        #logger.debug(f"List to get parsed: {routes_list['eRutasVenta']}")
        return self._parse_list(routes_list, RutaVenta)

    # --- Marketing ---

    def get_marketing_raw(self,
                          cod_scan: int = 0) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Busca jerarquía de marketing SIN validación (raw JSON).

        Args:
            cod_scan: Código de escaneo (opcional, 0 para todos)
        """
        params = {
            "CodScan": cod_scan if cod_scan > 0 else ""
        }
        return self._get("jerarquiaMkt/", params)

    def get_marketing(self,
                      cod_scan: int = 0) -> List[JerarquiaMkt]:
        """
        Busca jerarquía de marketing validada con Pydantic.

        Args:
            cod_scan: Código de escaneo (opcional, 0 para todos)
        """
        raw_data = self.get_marketing_raw(cod_scan)
        # Extraer lista de segmentos del JSON anidado
        # Estructura: {"SubcanalesMkt": {"SegmentosMkt": [...]}}
        segmentos_list = raw_data.get('SubcanalesMkt', {}).get('SegmentosMkt', [])
        return self._parse_list(segmentos_list, JerarquiaMkt)

    # --- Reportes ---
    def export_sales_report(self, 
                            fecha_desde: str, 
                            fecha_hasta: str, 
                            idsucur: str = "1", 
                            empresas: str = "1",
                            tiposdoc: str = "DVVTA,FCVTA",
                            formasagruart: str = "MARCA,GENERICO,,,,,,,,") -> bytes:
        """
        Solicita y descarga el reporte de ventas (Excel/CSV).
        
        El flujo es:
        1. POST a /reporteComprobantesVta/exportarExcel con filtros.
        2. Recibe JSON con path del archivo ('pcArchivo').
        3. GET a ese path para descargar los bytes.
        """
        if not self._session_id:
            self.login()

        endpoint = "reporteComprobantesVta/exportarExcel"
        url = self.base_url + endpoint
        
        payload = {
            "dsFiltrosRepCbtsVta": {
                "eFiltros": [
                    {
                        "letra": None,
                        "serie": None,
                        "numero": None,
                        "numeroHasta": None,
                        "fechadesde": fecha_desde,
                        "fechahasta": fecha_hasta,
                        "idsucur": idsucur,
                        "timbrado": "",
                        "empresas": empresas,
                        "tiposdoc": tiposdoc,
                        "formasagruart": formasagruart
                    }
                ]
            },
            "pcTipo": "D"
        }

        logger.info(f"Requesting sales report export: {fecha_desde} to {fecha_hasta}...")
        
        try:
            # Paso 1: Solicitar exportación
            response = self.session.post(url, json=payload, timeout=self.config.timeout)
            
            if response.status_code == 401:
                self.login()
                response = self.session.post(url, json=payload, timeout=self.config.timeout)
                
            if response.status_code != 200:
                raise ApiError(response.status_code, "Failed to request report export", response.text)
                
            data = response.json()
            pc_archivo = data.get("pcArchivo")
            
            if not pc_archivo:
                raise ApiError(500, "API response missing 'pcArchivo' field")
                
            # Paso 2: Descargar archivo
            # pcArchivo suele venir como ruta relativa tipo "/temp/archivo.xls" o similar.
            # La base_path original en endpoints.py era baseURL sin /web/api...
            # Asumiremos que pcArchivo es relativo a la raíz del servidor web.
            # self.config.api_url es "http://host:port"
            
            # Limpiamos slashes para evitar dobles
            file_url = f"{str(self.config.api_url).rstrip('/')}/{pc_archivo.lstrip('/')}"
            
            logger.info(f"Downloading report from {file_url}...")
            
            file_response = self.session.get(file_url, timeout=self.config.timeout)
            
            if file_response.status_code != 200:
                raise ApiError(file_response.status_code, "Failed to download report file", file_response.text)
                
            return file_response.content
            
        except requests.RequestException as e:
            raise ApiError(500, f"Connection error during report export: {str(e)}")


