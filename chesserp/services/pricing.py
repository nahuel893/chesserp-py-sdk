"""Pricing service — price lists and price list items (web API)."""

from typing import Any, Dict, List, Union

from chesserp.models.pricing import ListaPrecio, PrecioArticulo
from chesserp.services import BaseService
from chesserp.logger import get_logger

logger = get_logger(__name__)


class PricingService(BaseService):

    def get_lists_raw(self) -> Dict[str, Any]:
        """Fetch all price lists (raw JSON)."""
        return self._client._get("precios/obtenerVigenciasListas")

    def get_lists(
        self,
        solo_vigentes: bool = True,
        raw: bool = False,
    ) -> Union[List[ListaPrecio], List[Dict[str, Any]]]:
        """Fetch price list catalog, optionally filtering active-only."""
        data = self.get_lists_raw()
        listas = data.get("eListaPrecios", [])

        if solo_vigentes:
            listas = [l for l in listas if l.get("vigente") is True]

        logger.info(f"Listas de precios obtenidas: {len(listas)}")

        if raw:
            return listas
        return self._client._parse_list(listas, ListaPrecio)

    def get_items_raw(
        self,
        id_lista: int,
        id_vigencia: int,
        solo_vigentes: bool = True,
        filtro_familia: str = "",
    ) -> Dict[str, Any]:
        """Fetch price list items (raw JSON)."""
        params = {
            "piLis": id_lista,
            "piVig": id_vigencia,
            "plPre": "false" if solo_vigentes else "true",
            "pcFag": filtro_familia,
        }
        return self._client._get("precios/obtenerListaPrecios", params)

    def get_items(
        self,
        id_lista: int,
        id_vigencia: int,
        solo_vigentes: bool = True,
        filtro_familia: str = "",
        raw: bool = False,
    ) -> Union[List[PrecioArticulo], List[Dict[str, Any]]]:
        """Fetch price list items parsed or raw."""
        data = self.get_items_raw(id_lista, id_vigencia, solo_vigentes, filtro_familia)
        items = data.get("dsPrecios", {}).get("ePrecios", [])

        logger.info(f"Articulos obtenidos para lista {id_lista}: {len(items)}")

        if raw:
            return items
        return self._client._parse_list(items, PrecioArticulo)
