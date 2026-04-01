"""ChessClient — thin shell over BaseClient for the official ChessERP REST API."""

import requests

from chesserp._base import BaseClient
from chesserp.exceptions import AuthError
from chesserp.logger import get_logger
from chesserp.services.sales import SalesService
from chesserp.services.inventory import InventoryService
from chesserp.services.customers import CustomersService
from chesserp.services.orders import OrdersService
from chesserp.services.staff import StaffService
from chesserp.services.routes import RoutesService
from chesserp.services.marketing import MarketingService
from chesserp.services.reports import ReportsService

logger = get_logger(__name__)

DEFAULT_API_PATH = "/web/api/chess/v1/"
DEFAULT_LOGIN_PATH = "/web/api/chess/v1/auth/login"


class ChessClient(BaseClient):
    """
    Client for the official ChessERP REST API.

    Uses JSON-based authentication (POST usuario/password).

    Usage::

        client = ChessClient(api_url="https://api.empresa.com",
                              username="user", password="pass")
        ventas = client.sales.get(fecha_desde="2025-01-01", fecha_hasta="2025-12-31")
        clientes = client.customers.get()
    """

    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        api_path: str = DEFAULT_API_PATH,
        login_path: str = DEFAULT_LOGIN_PATH,
        timeout: int = 30,
        name: str | None = None,
    ):
        super().__init__(api_url, username, password, api_path, login_path, timeout, name)

        # Domain services
        self.sales = SalesService(self)
        self.inventory = InventoryService(self)
        self.customers = CustomersService(self)
        self.orders = OrdersService(self)
        self.staff = StaffService(self)
        self.routes = RoutesService(self)
        self.marketing = MarketingService(self)
        self.reports = ReportsService(self)

    def login(self) -> None:
        """Authenticate via JSON POST and store session cookie."""
        credentials = {"usuario": self.username, "password": self.password}
        logger.info(f"[{self.name}] Authenticating as {self.username}...")

        try:
            resp = self._session.post(self._login_url, json=credentials, timeout=self.timeout)

            if resp.status_code != 200:
                raise AuthError(f"Login failed: {resp.status_code} - {resp.text}")

            data = resp.json()
            session_id = data.get("sessionId")

            if not session_id:
                raise AuthError("No sessionId returned from API")

            # Set cookie header for the session
            self._session.headers.update({"Cookie": session_id})
            self._authenticated = True
            logger.info("Authentication successful.")

        except requests.RequestException as e:
            raise AuthError(f"Connection error during login: {str(e)}")
