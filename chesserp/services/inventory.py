"""Inventory service — articles (paginated) and stock (single request)."""

from typing import Any, Dict, List, Union

from chesserp.models.inventory import Articulo, StockFisico
from chesserp.services import BaseService
from chesserp.logger import get_logger

logger = get_logger(__name__)


class InventoryService(BaseService):

    # --- Articles (paginated) ---

    def get_articles_raw(
        self,
        articulo: int = 0,
        nro_lote: int = 1,
        anulado: bool = False,
    ) -> Dict[str, Any]:
        """Fetch a single articles lote (raw JSON)."""
        params = {
            "articulo": articulo if articulo > 0 else "",
            "nroLote": nro_lote,
            "anulado": str(anulado).lower(),
        }
        return self._client._get("articulos/", params)

    def get_articles(
        self,
        articulo: int = 0,
        anulado: bool = False,
        raw: bool = False,
    ) -> Union[List[Articulo], List[Dict[str, Any]]]:
        """Fetch all article lotes, concatenated."""

        def fetcher(nro_lote: int) -> dict:
            return self.get_articles_raw(articulo, nro_lote, anulado)

        return self._client._fetch_paginated(
            raw_fetcher=fetcher,
            data_path=["Articulos", "eArticulos"],
            count_key="cantArticulos",
            model_class=Articulo,
            raw=raw,
        )

    # --- Stock (not paginated) ---

    def get_stock_raw(
        self,
        id_deposito: int,
        frescura: bool = False,
        fecha: str = "",
    ) -> Any:
        """Fetch physical stock (raw JSON)."""
        params = {
            "idDeposito": id_deposito,
            "fechastock": fecha,
        }
        return self._client._get("stock/", params)

    def get_stock(
        self,
        id_deposito: int,
        frescura: bool = False,
        fecha: str = "",
        raw: bool = False,
    ) -> Union[List[StockFisico], List[Dict[str, Any]]]:
        """Fetch physical stock."""
        raw_data = self.get_stock_raw(id_deposito, frescura, fecha)
        stock_list = raw_data.get("dsStockFisicoApi", {}).get("dsStock", [])
        if raw:
            return stock_list
        return self._client._parse_list(stock_list, StockFisico)
