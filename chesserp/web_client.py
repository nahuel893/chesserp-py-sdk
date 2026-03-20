import os
import logging
from typing import List, Optional, Dict, Any, Union

import requests
from dotenv import load_dotenv

from chesserp.exceptions import AuthError, ApiError
from chesserp.models.pricing import ListaPrecio, PrecioArticulo
from chesserp.logger import get_logger

logger = get_logger(__name__)

load_dotenv()

# Paths de la API web (frontend)
WEB_API_PATH = "/web/api/"
WEB_LOGIN_PATH = "/static/auth/j_spring_security_check"


class ChessWebClient:
    """
    Cliente para la API web interna de ChessERP (endpoints del frontend).

    Esta API NO está documentada oficialmente. Los endpoints fueron
    reverse-engineered del tráfico de red del frontend Angular.

    Usa Spring Security form login (distinto al ChessClient oficial).
    La sesión se maneja via requests.Session() con cookies automáticas.

    Uso:
        # Desde variables de entorno con prefijo
        client = ChessWebClient.from_env(prefix="EMPRESA1_")

        # O directo con credenciales
        client = ChessWebClient(
            api_url="http://servidor:puerto",
            username="usuario",
            password="clave"
        )
    """

    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        timeout: int = 60,
        name: Optional[str] = None,
    ):
        self.api_url = api_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.name = name or api_url

        self.base_url = self.api_url + WEB_API_PATH
        self._login_url = self.api_url + WEB_LOGIN_PATH
        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Cache-Control": "no-cache",
        })
        self._authenticated = False

    @classmethod
    def from_env(cls, prefix: str = "", env_file: Optional[str] = None) -> "ChessWebClient":
        """
        Crea un cliente desde variables de entorno.

        Args:
            prefix: Prefijo para las variables (ej: "EMPRESA1_" busca
                    EMPRESA1_API_URL, EMPRESA1_USERNAME, EMPRESA1_PASSWORD)
            env_file: Ruta opcional a archivo .env
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
            name=prefix.rstrip("_") if prefix else None,
        )

    def login(self) -> None:
        """
        Autenticación via Spring Security form login.
        Almacena la cookie JSESSIONID en la sesión automáticamente.
        """
        logger.info(f"[{self.name}] Authenticating as {self.username} (web)...")
        payload = {
            "j_username": self.username,
            "j_password": self.password,
        }
        try:
            resp = self._session.post(
                self._login_url,
                data=payload,
                allow_redirects=True,
                timeout=self.timeout,
            )
            resp.raise_for_status()

            if "JSESSIONID" not in self._session.cookies:
                raise AuthError(
                    "Login fallido: no se recibió JSESSIONID. "
                    "Verificar usuario/contraseña."
                )

            self._authenticated = True
            logger.info(f"[{self.name}] Web authentication successful.")

        except requests.RequestException as e:
            raise AuthError(f"Connection error during web login: {str(e)}")

    def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """
        Realiza un GET autenticado a la API web.
        Reintenta login automaticamente si la sesion expiro (401/redirect a login).
        """
        if not self._authenticated:
            self.login()

        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        url = self.base_url + endpoint

        try:
            resp = self._session.get(url, params=params, timeout=self.timeout)

            if resp.status_code == 401:
                logger.warning("[web] Session expired (401). Retrying login...")
                self.login()
                resp = self._session.get(url, params=params, timeout=self.timeout)

            if resp.status_code != 200:
                raise ApiError(resp.status_code, f"Web request to {endpoint} failed", resp.text)

            return resp.json()

        except requests.RequestException as e:
            raise ApiError(500, f"Connection error: {str(e)}")

    def _parse_list(self, data: Any, model_class: Any) -> List[Any]:
        """
        Parsea una lista de dicts a modelos Pydantic.
        Si un elemento falla, lo loguea y continua con el resto.
        """
        if not isinstance(data, list):
            logger.warning(f"Se esperaba una lista, se recibió: {type(data)}")
            return []

        parsed = []
        for i, item in enumerate(data):
            try:
                parsed.append(model_class(**item))
            except Exception as e:
                logger.error(f"Error parseando ítem #{i} en {model_class.__name__}: {e}")
        return parsed

    # --- Listas de Precios ---

    def get_price_lists_raw(self) -> Dict[str, Any]:
        """
        Devuelve todas las listas de precios (raw JSON).

        Response:
            {
                "eListaPrecios": [
                    {
                        "listaspre": 1,
                        "titulis": "LISTA SALTA MAYORISTA",
                        "idvigencia": 8260,
                        "vigente": true,
                        "fecvigenciadesde": "2026-03-18T17:42:21.251",
                        "fecvigenciahasta": null
                    }
                ]
            }
        """
        return self._get("precios/obtenerVigenciasListas")

    def get_price_lists(
        self,
        solo_vigentes: bool = True,
        raw: bool = False,
    ) -> Union[List[ListaPrecio], List[Dict[str, Any]]]:
        """
        Devuelve el catalogo de listas de precios.

        Args:
            solo_vigentes: Si True (default), retorna solo las listas actualmente vigentes.
            raw: Si True, retorna lista de dicts sin validar.
        """
        data = self.get_price_lists_raw()
        listas = data.get("eListaPrecios", [])

        if solo_vigentes:
            listas = [l for l in listas if l.get("vigente") is True]

        logger.info(f"Listas de precios obtenidas: {len(listas)}")

        if raw:
            return listas
        return self._parse_list(listas, ListaPrecio)

    def get_price_list_items_raw(
        self,
        id_lista: int,
        id_vigencia: int,
        solo_vigentes: bool = True,
        filtro_familia: str = "",
    ) -> Dict[str, Any]:
        """
        Devuelve los articulos de una lista de precios (raw JSON).

        Args:
            id_lista: ID de la lista (campo listaspre)
            id_vigencia: ID de vigencia activa (campo idvigencia)
            solo_vigentes: Si True, solo precios vigentes al dia de hoy (plPre=false)
            filtro_familia: Filtro por familia/grupo (vacio = todos)

        Response:
            {
                "dsPrecios": {
                    "ePrecios": [{codart, descrip, precio, prefin, ...}]
                }
            }
        """
        params = {
            "piLis": id_lista,
            "piVig": id_vigencia,
            "plPre": "false" if solo_vigentes else "true",
            "pcFag": filtro_familia,
        }
        return self._get("precios/obtenerListaPrecios", params)

    def get_price_list_items(
        self,
        id_lista: int,
        id_vigencia: int,
        solo_vigentes: bool = True,
        filtro_familia: str = "",
        raw: bool = False,
    ) -> Union[List[PrecioArticulo], List[Dict[str, Any]]]:
        """
        Devuelve los articulos con precios de una lista especifica.

        Args:
            id_lista: ID de la lista (campo listaspre de get_price_lists)
            id_vigencia: ID de vigencia activa (campo id_vigencia de ListaPrecio)
            solo_vigentes: Si True (default), solo precios vigentes al dia de hoy
            filtro_familia: Filtro por familia/grupo (vacio = todos los articulos)
            raw: Si True, retorna lista de dicts sin validar.
        """
        data = self.get_price_list_items_raw(
            id_lista, id_vigencia, solo_vigentes, filtro_familia
        )
        items = data.get("dsPrecios", {}).get("ePrecios", [])

        logger.info(f"Articulos obtenidos para lista {id_lista}: {len(items)}")

        if raw:
            return items
        return self._parse_list(items, PrecioArticulo)
