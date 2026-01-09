import requests
import logging
import re
import os
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urljoin
from dotenv import load_dotenv

# Local imports
from chesserp.exceptions import AuthError, ApiError, ChessError
from chesserp.models.sales import Sale
from chesserp.models.inventory import Articulo, StockFisico
from chesserp.models.clients import Cliente
from chesserp.models.orders import Pedido
from chesserp.models.routes import RutaVenta
from chesserp.models.staff import PersonalComercial
from chesserp.models.marketing import JerarquiaMkt
from chesserp.logger import get_logger

# Configure logger
logger = get_logger(__name__)

load_dotenv()

# Paths por defecto de la API ChessERP
DEFAULT_API_PATH = "/web/api/chess/v1/"
DEFAULT_LOGIN_PATH = "/web/api/chess/v1/auth/login"


class ChessClient:
    """
    Cliente principal para la API de ChessERP.
    Maneja autenticación y llamadas a endpoints.

    Uso:
        # Directo con credenciales
        client = ChessClient(
            api_url="https://api.empresa.com",
            username="usuario",
            password="clave"
        )

        # Desde variables de entorno con prefijo
        client = ChessClient.from_env(prefix="CHESS_EMPRESA1_")
        # Lee: CHESS_EMPRESA1_API_URL, CHESS_EMPRESA1_USERNAME, CHESS_EMPRESA1_PASSWORD
    """

    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        api_path: str = DEFAULT_API_PATH,
        login_path: str = DEFAULT_LOGIN_PATH,
        timeout: int = 30,
        name: Optional[str] = None
    ):
        """
        Inicializa el cliente con credenciales directas.

        Args:
            api_url: URL base de la API (ej: "https://api.chesserp.com")
            username: Usuario para autenticación
            password: Contraseña para autenticación
            api_path: Path base de la API (default: /web/api/chess/v1/)
            login_path: Path de login (default: /web/api/chess/v1/auth/login)
            timeout: Timeout en segundos para requests
            name: Nombre opcional para identificar esta instancia en logs
        """
        self.api_url = api_url.rstrip('/')
        self.username = username
        self.password = password
        self.api_path = api_path
        self.login_path = login_path.rstrip('/')
        self.timeout = timeout
        self.name = name or api_url

        # Headers y estado de sesión
        self.base_headers = {}
        self.base_url = self.api_url + self.api_path
        self.auth_url = self.api_url + self.login_path
        self._session_id: Optional[str] = None
        self.cookies = None

    @classmethod
    def from_env(cls, prefix: str = "", env_file: Optional[str] = None) -> "ChessClient":
        """
        Crea un cliente desde variables de entorno.

        Args:
            prefix: Prefijo para las variables (ej: "CHESS_PROD_" busca
                    CHESS_PROD_API_URL, CHESS_PROD_USERNAME, CHESS_PROD_PASSWORD)
            env_file: Ruta opcional a archivo .env

        Returns:
            ChessClient configurado

        Example:
            # .env contiene:
            # EMPRESA1_API_URL=https://api1.com
            # EMPRESA1_USERNAME=user1
            # EMPRESA1_PASSWORD=pass1

            client = ChessClient.from_env(prefix="EMPRESA1_")
        """
        if env_file:
            load_dotenv(env_file)

        api_url = os.getenv(f"{prefix}API_URL")
        username = os.getenv(f"{prefix}USERNAME")
        password = os.getenv(f"{prefix}PASSWORD")

        if not all([api_url, username, password]):
            missing = []
            if not api_url:
                missing.append(f"{prefix}API_URL")
            if not username:
                missing.append(f"{prefix}USERNAME")
            if not password:
                missing.append(f"{prefix}PASSWORD")
            raise ValueError(f"Variables de entorno faltantes: {', '.join(missing)}")

        return cls(
            api_url=api_url,
            username=username,
            password=password,
            name=prefix.rstrip('_') if prefix else None
        )

    def login(self) -> str:
        """
        Realiza el login y almacena el sessionId.
        """
        credentials = {
            "usuario": self.username,
            "password": self.password
        }
        logger.info(f"[{self.name}] Authenticating as {self.username}...")
        
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
                  raw: bool = False
                  ) -> Union[List[Sale], List[Dict[str, Any]]]:
        """
        Obtiene comprobantes de ventas (todos los lotes).

        Args:
            fecha_desde: Fecha inicio (formato API)
            fecha_hasta: Fecha fin (formato API)
            empresas: Filtro de empresas
            detallado: Nivel de detalle
            raw: Si True, retorna lista de dicts sin validar. Si False, retorna List[Sale]
        """
        # Primera request para obtener el primer lote y el total de lotes
        response_data = self.get_sales_raw(fecha_desde, fecha_hasta, empresas, detallado, nro_lote=1)

        # Inicializar lista acumuladora
        sales_data = []

        # Extraer el primer lote de datos
        if isinstance(response_data, dict):
            sales_list = response_data.get("dsReporteComprobantesApi", {}).get("VentasResumen")

            if sales_list is not None:
                if raw:
                    sales_data.extend(sales_list)
                else:
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
                            if raw:
                                sales_data.extend(list_)
                            else:
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
                     anulado: bool = False,
                     raw: bool = False) -> Union[List[Articulo], List[Dict[str, Any]]]:
        """
        Obtiene catálogo de artículos (todos los lotes).

        Args:
            articulo: ID específico (0 para todos)
            anulado: Incluir anulados
            raw: Si True, retorna lista de dicts sin validar. Si False, retorna List[Articulo]
        """
        # Primera request para obtener el primer lote y el total de lotes
        response_data = self.get_articles_raw(articulo, nro_lote=1, anulado=anulado)

        # Inicializar lista acumuladora
        articles_data = []

        # Extraer el primer lote de datos
        if isinstance(response_data, dict):
            articles_list = response_data.get("Articulos", {}).get("eArticulos")

            if articles_list is not None:
                if raw:
                    articles_data.extend(articles_list)
                else:
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
                            if raw:
                                articles_data.extend(list_)
                            else:
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
                  fecha: str = "",
                  raw: bool = False) -> Union[List[StockFisico], List[Dict[str, Any]]]:
        """
        Obtiene stock físico.

        Args:
            id_deposito: Obligatorio
            frescura: Apertura por frescura
            fecha: DD-MM-AAAA (Opcional, cálculo histórico)
            raw: Si True, retorna lista de dicts sin validar. Si False, retorna List[StockFisico]
        """
        raw_data = self.get_stock_raw(id_deposito, fecha)
        raw_data = raw_data.get('dsStockFisicoApi').get("dsStock")  # retorna la lista de articulos
        if raw:
            return raw_data
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
                      nro_lote: int = 0,
                      raw: bool = False) -> Union[List[Cliente], List[Dict[str, Any]]]:
        """
        Busca clientes (todos los lotes o uno específico).

        Args:
            anulado: Incluir anulados
            nro_lote: Lote específico (0 para todos)
            raw: Si True, retorna lista de dicts sin validar. Si False, retorna List[Cliente]
        """
        # Inicializar lista acumuladora
        customers_data = []

        if nro_lote == 0:
            # Primera request  para obtener el primer lote y el total de lotes
            response_data = self.get_customers_raw(anulado=anulado, nro_lote=1)

            # Extraer el primer lote de datos
            if isinstance(response_data, dict):
                customers_list = response_data.get("Clientes", {}).get("eClientes")

                if customers_list is not None:
                    if raw:
                        customers_data.extend(customers_list)
                    else:
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
                        response_data = self.get_customers_raw(nro_lote=i)

                        if isinstance(response_data, dict):
                            list_ = response_data.get("Clientes", {}).get("eClientes")

                            if list_ is not None:
                                if raw:
                                    customers_data.extend(list_)
                                else:
                                    customers_data.extend(self._parse_list(list_, Cliente))
                                logger.info(f"Lote {i} procesado: {len(list_)} registros")
                else:
                    logger.warning(f"No se pudo parsear total de lotes de: {cant_clientes_str}. Asumiendo 1 lote.")

            logger.info(f"Total de clientes obtenidas: {len(customers_data)}")
        else:
            response_data = self.get_customers_raw(nro_lote=nro_lote)
            list_ = response_data.get("Clientes", {}).get("eClientes")

            if list_ is not None:
                if raw:
                    customers_data.extend(list_)
                else:
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
                   facturado: bool = False,
                   raw: bool = False) -> Union[List[Pedido], List[Dict[str, Any]]]:
        """
        Busca pedidos.

        Args:
            fecha_entrega: Fecha de entrega
            fecha_pedido: Fecha de alta
            facturado: Filtrar facturados
            raw: Si True, retorna lista de dicts sin validar. Si False, retorna List[Pedido]
        """
        raw_data = self.get_orders_raw(fecha_entrega, fecha_pedido, facturado)
        # Extraer lista de pedidos del JSON
        # Estructura: {"pedidos": [...]}
        pedidos_list = raw_data.get('pedidos', []) if isinstance(raw_data, dict) else raw_data
        if raw:
            return pedidos_list
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
                  personal: int = 0,
                  raw: bool = False) -> Union[List[PersonalComercial], List[Dict[str, Any]]]:
        """
        Busca personal comercial.
        Args:
            sucursal: ID de sucursal (0 para todas)
            personal: ID de personal (0 para todos)
            raw: Si True, retorna lista de dicts sin validar. Si False, retorna List[PersonalComercial]
        """
        raw_data = self.get_staff_raw(sucursal, personal)
        # Extraer lista de personal del JSON
        # Estructura: {"PersonalComercial": {"ePersCom": [...]}}
        staff_list = raw_data.get('PersonalComercial', {}).get('ePersCom', []) if isinstance(raw_data, dict) else raw_data
        if raw:
            return staff_list
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
                   anulado: bool = False,
                   raw: bool = False) -> Union[List[RutaVenta], List[Dict[str, Any]]]:
        """
        Busca rutas de venta.

        Args:
            sucursal: ID de sucursal
            fuerza_venta: ID de fuerza de venta
            modo_atencion: Modo de atención
            anulado: Incluir anuladas
            raw: Si True, retorna lista de dicts sin validar. Si False, retorna List[RutaVenta]
        """
        raw_data = self.get_routes_raw(sucursal=sucursal,
                                       fuerza_venta=fuerza_venta,
                                       anulado=anulado)
        # Extraer lista de rutas del JSON
        # Estructura probable: {"rutasVenta": [...]} o {"RutasVenta": {"eRutas": [...]}}
        # Intentar diferentes estructuras posibles
        routes_list = raw_data.get('RutasVenta')
        routes_list = routes_list.get('eRutasVenta')
        if raw:
            return routes_list
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
                      cod_scan: int = 0,
                      raw: bool = False) -> Union[List[JerarquiaMkt], List[Dict[str, Any]]]:
        """
        Busca jerarquía de marketing.

        Args:
            cod_scan: Código de escaneo (opcional, 0 para todos)
            raw: Si True, retorna lista de dicts sin validar. Si False, retorna List[JerarquiaMkt]
        """
        raw_data = self.get_marketing_raw(cod_scan)
        # Extraer lista de segmentos del JSON anidado
        # Estructura: {"SubcanalesMkt": {"SegmentosMkt": [...]}}
        segmentos_list = raw_data.get('SubcanalesMkt', {}).get('SegmentosMkt', [])
        if raw:
            return segmentos_list
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

        logger.info(f"[{self.name}] Requesting sales report export: {fecha_desde} to {fecha_hasta}...")

        try:
            # Paso 1: Solicitar exportación
            response = requests.post(url, json=payload, headers=self.base_headers, timeout=self.timeout)

            if response.status_code == 401:
                self.login()
                response = requests.post(url, json=payload, headers=self.base_headers, timeout=self.timeout)

            if response.status_code != 200:
                raise ApiError(response.status_code, "Failed to request report export", response.text)

            data = response.json()
            pc_archivo = data.get("pcArchivo")

            if not pc_archivo:
                raise ApiError(500, "API response missing 'pcArchivo' field")

            # Paso 2: Descargar archivo
            # pcArchivo viene como ruta relativa tipo "/temp/archivo.xls"
            file_url = f"{self.api_url}/{pc_archivo.lstrip('/')}"

            logger.info(f"[{self.name}] Downloading report from {file_url}...")

            file_response = requests.get(file_url, headers=self.base_headers, timeout=self.timeout)

            if file_response.status_code != 200:
                raise ApiError(file_response.status_code, "Failed to download report file", file_response.text)

            return file_response.content

        except requests.RequestException as e:
            raise ApiError(500, f"Connection error during report export: {str(e)}")


