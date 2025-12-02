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
        self.base_headers = {
        }
         
        self.base_url = str(self.config.api_url) + os.getenv("API_PATH")
        self.auth_url = os.getenv("API_PATH_LOGIN")        
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

            # Construimos el header para todas las request
            self.base_headers = {
                "Cookie": self._session_id}

            # Solo almacenar el ID, el header Cookie se construirá en cada _get
            logger.info("Authentication successful.")
            
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
        logger.debug(f"GET request: url={url}, headers={headers}")

        try:
            # Usar requests.get directamente
            response = requests.get(url, params=params, headers=headers)
            
            if response.status_code == 401:
                logger.warning("Token expired (401). Retrying login...")
                self.login() # Re-login para obtener un nuevo _session_id
                # Reconstruir headers con la nueva cookie y reintentar la petición
                headers["Cookie"] = self._session_id if "JSESSIONID=" in self._session_id else f"JSESSIONID={self._session_id}"
                response = requests.get(url, params=params, headers)

            if response.status_code != 200:
                raise apierror(response.status_code, f"request to {endpoint} failed", response.text)
            json_data = response.json()
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
    def get_sales(self,
                  fecha_desde: str,
                  fecha_hasta: str,
                  empresas: str = "",
                  detallado: bool = False,
                  ) -> List[Sale]:
        """
        Obtiene comprobantes de ventas (todos los lotes).
        """
        # Primera request para obtener el primer lote y el total de lotes
        nro_lote = 1
        params = {
            "fechaDesde": fecha_desde,
            "fechaHasta": fecha_hasta,
            "empresas": empresas,
            "detallado": str(detallado).lower(),
            "nroLote": nro_lote
        }
        response_data = self._get("ventas/", params)

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
                total_lotes = int(match.group(2))
                logger.info(f"Total de lotes a procesar: {total_lotes}")

                # Iterar sobre los lotes restantes (si hay más de 1)
                for i in range(lote_actual + 1, total_lotes + 1):
                    params['nroLote'] = i
                    response_data = self._get("ventas/", params)

                    if isinstance(response_data, dict):
                        list_ = response_data.get("dsReporteComprobantesApi", {}).get("VentasResumen")

                        if list_ is not None:
                            sales_data.extend(self._parse_list(list_, Sale))
                            logger.info(f"Lote {i} procesado: {len(list_)} registros")
            else:
                logger.warning(f"No se pudo parsear total de lotes de: {cant_comprobantes_str}. Asumiendo 1 lote.")

        logger.info(f"Total de ventas obtenidas: {len(sales_data)}")
        return sales_data

    def get_sales_raw(self,
                  fecha_desde: str,
                  fecha_hasta: str,
                  empresas: str = "",
                  detallado: bool = False,
                  nro_lote: int = 0) -> Dict[str, Any]:
        """
        Obtiene comprobantes de ventas SIN validación (raw JSON).
        Útil para pipelines ETL y arquitectura medallion.
        """
        params = {
            "fechaDesde": fecha_desde,
            "fechaHasta": fecha_hasta,
            "empresas": empresas,
            "detallado": str(detallado).lower(),
            "nroLote": nro_lote
        }
        
        response_data = self._get("ventas/", params)
        
        return response_data 
        
    # --- Inventario ---

    def get_articles(self, 
                     articulo: int = 0, 
                     nro_lote: int = 0, 
                     anulado: bool = False) -> List[Articulo]:
        """
        Obtiene catálogo de artículos.
        Args:
            articulo: ID específico (0 para todos)
            nro_lote: Paginación
            anulado: Incluir anulados
        """
        params = {
            "articulo": articulo if articulo > 0 else "",
            "nroLote": nro_lote,
            "anulado": str(anulado).lower()
        }
        return self._parse_list(self._get("articulos/", params), Articulo)

    def get_stock(self, 
                  id_deposito: int, 
                  frescura: bool = False, 
                  fecha: str = "") -> List[StockFisico]:
        """
        Obtiene stock físico.
        Args:
            id_deposito: Obligatorio
            frescura: Apertura por frescura
            fecha: DD-MM-AAAA (Opcional, cálculo histórico)
        """
        params = {
            "idDeposito": id_deposito,
            "frescura": str(frescura).lower(),
            "DD-MM-AAAA": fecha
        }
        return self._parse_list(self._get("stock/", params), StockFisico)

    # --- Clientes ---

    def get_customers(self, 
                      cliente: int = 0, 
                      sucursal: int = 0, 
                      anulado: bool = False, 
                      nro_lote: int = 0) -> List[Cliente]:
        """
        Busca clientes.
        """
        params = {
            "cliente": cliente if cliente > 0 else "",
            "sucursal": sucursal if sucursal > 0 else "",
            "anulado": str(anulado).lower(),
            "nroLote": nro_lote
        }
        return self._parse_list(self._get("clientes/", params), Cliente)

    # --- Pedidos ---

    def get_orders(self, 
                   fecha_entrega: str = "", 
                   fecha_pedido: str = "", 
                   facturado: bool = False) -> List[Pedido]:
        """
        Busca pedidos.
        Args:
            fecha_entrega: Fecha de entrega
            fecha_pedido: Fecha de alta
            facturado: Filtrar facturados
        """
        params = {
            "fechaEntrega": fecha_entrega,
            "fechaPedido": fecha_pedido,
            "facturado": str(facturado).lower()
        }
        return self._parse_list(self._get("pedidos/", params), Pedido)

    # --- Personal ---

    def get_staff(self, 
                  sucursal: int = 0, 
                  personal: int = 0) -> List[PersonalComercial]:
        """
        Busca personal comercial.
        """
        params = {
            "sucursal": sucursal if sucursal > 0 else "",
            "personal": personal if personal > 0 else ""
        }
        return self._parse_list(self._get("personalComercial/", params), PersonalComercial)

    # --- Rutas ---

    def get_routes(self, 
                   sucursal: int = 0, 
                   fuerza_venta: int = 0, 
                   modo_atencion: int = 0,
                   ruta: int = 0,
                   anulado: bool = False) -> List[RutaVenta]:
        """
        Busca rutas de venta.
        """
        params = {
            "sucursal": sucursal if sucursal > 0 else "",
            "fuerzaventa": fuerza_venta if fuerza_venta > 0 else "",
            "modoatencion": modo_atencion if modo_atencion > 0 else "",
            "ruta": ruta if ruta > 0 else "",
            "anulada": str(anulado).lower() # PDF dice "anulada" en query param pg 36
        }
        return self._parse_list(self._get("rutasVenta/", params), RutaVenta)

    # --- Marketing ---

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


