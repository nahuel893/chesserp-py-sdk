"""ChessWebClient — thin shell over BaseClient for the ChessERP web/frontend API."""

import requests

from chesserp._base import BaseClient
from chesserp.exceptions import AuthError
from chesserp.logger import get_logger
from chesserp.services.pricing import PricingService

logger = get_logger(__name__)

WEB_API_PATH = "/web/api/"
WEB_LOGIN_PATH = "/static/auth/j_spring_security_check"


class ChessWebClient(BaseClient):
    """
    Client for the internal web API of ChessERP (frontend endpoints).

    Uses Spring Security form login. Session managed via requests.Session cookies.

    Usage::

        client = ChessWebClient.from_env(prefix="EMPRESA1_")
        listas = client.pricing.get_lists()
    """

    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        timeout: int = 60,
        name: str | None = None,
    ):
        super().__init__(
            api_url, username, password,
            api_path=WEB_API_PATH,
            login_path=WEB_LOGIN_PATH,
            timeout=timeout,
            name=name,
        )
        self._session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Cache-Control": "no-cache",
        })

        # Domain services
        self.pricing = PricingService(self)

    def login(self) -> None:
        """Authenticate via Spring Security form POST."""
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
                    "Login fallido: no se recibio JSESSIONID. "
                    "Verificar usuario/contrasena."
                )

            self._authenticated = True
            logger.info(f"[{self.name}] Web authentication successful.")

        except requests.RequestException as e:
            raise AuthError(f"Connection error during web login: {str(e)}")
