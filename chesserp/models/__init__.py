from chesserp.models.sales import Sale
from chesserp.models.inventory import Articulo, StockFisico
from chesserp.models.clients import Cliente
from chesserp.models.orders import Pedido
from chesserp.models.routes import RutaVenta
from chesserp.models.staff import PersonalComercial
from chesserp.models.marketing import JerarquiaMkt

__all__ = [
    "Sale",
    "Articulo",
    "StockFisico",
    "Cliente",
    "Pedido",
    "RutaVenta",
    "PersonalComercial",
    "JerarquiaMkt",
]
