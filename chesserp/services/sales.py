"""Sales service — paginated sales/comprobantes endpoint."""

from typing import Any, Dict, List, Union

from chesserp.models.sales import Sale
from chesserp.services import BaseService


class SalesService(BaseService):

    def get_raw(
        self,
        fecha_desde: str,
        fecha_hasta: str,
        empresas: str = "",
        detallado: bool = False,
        nro_lote: int = 1,
    ) -> Dict[str, Any]:
        """Fetch a single sales lote (raw JSON)."""
        params = {
            "fechaDesde": fecha_desde,
            "fechaHasta": fecha_hasta,
            "empresas": empresas,
            "detallado": str(detallado).lower(),
            "nroLote": nro_lote,
        }
        return self._client._get("ventas/", params)

    def get(
        self,
        fecha_desde: str,
        fecha_hasta: str,
        empresas: str = "",
        detallado: bool = False,
        raw: bool = False,
    ) -> Union[List[Sale], List[Dict[str, Any]]]:
        """Fetch all sales lotes, concatenated."""

        def fetcher(nro_lote: int) -> dict:
            return self.get_raw(fecha_desde, fecha_hasta, empresas, detallado, nro_lote)

        return self._client._fetch_paginated(
            raw_fetcher=fetcher,
            data_path=["dsReporteComprobantesApi", "VentasResumen"],
            count_key="cantComprobantesVentas",
            model_class=Sale,
            raw=raw,
        )
