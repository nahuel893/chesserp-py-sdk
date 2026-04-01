"""Domain services for ChessERP API."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chesserp._base import BaseClient


class BaseService:
    """Base for all domain services. Holds a reference to the client."""

    def __init__(self, client: BaseClient) -> None:
        self._client = client


from chesserp.services.sales import SalesService
from chesserp.services.inventory import InventoryService
from chesserp.services.customers import CustomersService
from chesserp.services.orders import OrdersService
from chesserp.services.staff import StaffService
from chesserp.services.routes import RoutesService
from chesserp.services.marketing import MarketingService
from chesserp.services.reports import ReportsService
from chesserp.services.pricing import PricingService

__all__ = [
    "BaseService",
    "SalesService",
    "InventoryService",
    "CustomersService",
    "OrdersService",
    "StaffService",
    "RoutesService",
    "MarketingService",
    "ReportsService",
    "PricingService",
]
