"""Routes service — non-paginated sales routes endpoint."""

from typing import Any, Dict, List, Union

from chesserp.models.routes import RutaVenta
from chesserp.services import BaseService


class RoutesService(BaseService):

    def get_raw(
        self,
        sucursal: int = 1,
        fuerza_venta: int = 1,
        modo_atencion: int = 0,
        anulado: bool = False,
    ) -> Any:
        """Fetch sales routes (raw JSON)."""
        params = {
            "sucursal": sucursal,
            "fuerzaventa": fuerza_venta,
            "anulada": str(anulado).lower(),
        }
        return self._client._get("rutasVenta/", params)

    def get(
        self,
        sucursal: int = 1,
        fuerza_venta: int = 1,
        modo_atencion: str = "PRE",
        anulado: bool = False,
        raw: bool = False,
    ) -> Union[List[RutaVenta], List[Dict[str, Any]]]:
        """Fetch sales routes parsed or raw. Handles empty responses gracefully."""
        raw_data = self.get_raw(
            sucursal=sucursal,
            fuerza_venta=fuerza_venta,
            anulado=anulado,
        )
        routes_list = raw_data.get("RutasVenta", {}).get("eRutasVenta", [])
        if raw:
            return routes_list
        return self._client._parse_list(routes_list, RutaVenta)
