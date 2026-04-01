"""Marketing service — non-paginated marketing hierarchy endpoint."""

from typing import Any, Dict, List, Union

from chesserp.models.marketing import JerarquiaMkt
from chesserp.services import BaseService


class MarketingService(BaseService):

    def get_raw(self, cod_scan: int = 0) -> Any:
        """Fetch marketing hierarchy (raw JSON)."""
        params = {
            "CodScan": cod_scan if cod_scan > 0 else "",
        }
        return self._client._get("jerarquiaMkt/", params)

    def get(
        self,
        cod_scan: int = 0,
        raw: bool = False,
    ) -> Union[List[JerarquiaMkt], List[Dict[str, Any]]]:
        """Fetch marketing hierarchy parsed or raw."""
        raw_data = self.get_raw(cod_scan)
        segmentos_list = raw_data.get("SubcanalesMkt", {}).get("SegmentosMkt", [])
        if raw:
            return segmentos_list
        return self._client._parse_list(segmentos_list, JerarquiaMkt)
