"""Customers service — paginated customer endpoint."""

from typing import Any, Dict, List, Union

from chesserp.models.clients import Cliente
from chesserp.services import BaseService
from chesserp.logger import get_logger

logger = get_logger(__name__)


class CustomersService(BaseService):

    def get_raw(
        self,
        anulado: bool = False,
        nro_lote: int = 1,
    ) -> Dict[str, Any]:
        """Fetch a single customers lote (raw JSON)."""
        params = {
            "cliente": 0,
            "anulado": str(anulado).lower(),
            "nroLote": nro_lote,
        }
        return self._client._get("clientes/", params)

    def get(
        self,
        anulado: bool = False,
        nro_lote: int = 0,
        raw: bool = False,
    ) -> Union[List[Cliente], List[Dict[str, Any]]]:
        """Fetch customers — all lotes (nro_lote=0) or a specific one."""
        if nro_lote > 0:
            response = self.get_raw(anulado=anulado, nro_lote=nro_lote)
            items = response.get("Clientes", {}).get("eClientes", [])
            if raw:
                return items
            return self._client._parse_list(items, Cliente)

        # All lotes — propagate anulado
        def fetcher(lote: int) -> dict:
            return self.get_raw(anulado=anulado, nro_lote=lote)

        return self._client._fetch_paginated(
            raw_fetcher=fetcher,
            data_path=["Clientes", "eClientes"],
            count_key="cantClientes",
            model_class=Cliente,
            raw=raw,
        )
