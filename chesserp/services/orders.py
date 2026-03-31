"""Orders service — non-paginated orders endpoint."""

from typing import Any, Dict, List, Union

from chesserp.models.orders import Pedido
from chesserp.services import BaseService


class OrdersService(BaseService):

    def get_raw(
        self,
        fecha_entrega: str = "",
        fecha_pedido: str = "",
        facturado: bool = False,
    ) -> Any:
        """Fetch orders (raw JSON)."""
        params = {
            "fechaEntrega": fecha_entrega,
            "fechaPedido": fecha_pedido,
            "facturado": str(facturado).lower(),
        }
        return self._client._get("pedidos/", params)

    def get(
        self,
        fecha_entrega: str = "",
        fecha_pedido: str = "",
        facturado: bool = False,
        raw: bool = False,
    ) -> Union[List[Pedido], List[Dict[str, Any]]]:
        """Fetch orders parsed or raw."""
        raw_data = self.get_raw(fecha_entrega, fecha_pedido, facturado)
        pedidos_list = raw_data.get("pedidos", []) if isinstance(raw_data, dict) else raw_data
        if raw:
            return pedidos_list
        return self._client._parse_list(pedidos_list, Pedido)
