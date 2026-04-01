"""Staff service — non-paginated personal comercial endpoint."""

from typing import Any, Dict, List, Union

from chesserp.models.staff import PersonalComercial
from chesserp.services import BaseService


class StaffService(BaseService):

    def get_raw(
        self,
        sucursal: int = 0,
        personal: int = 0,
    ) -> Any:
        """Fetch commercial staff (raw JSON)."""
        params = {
            "sucursal": sucursal if sucursal > 0 else "",
            "personal": personal if personal > 0 else "",
        }
        return self._client._get("personalComercial/", params)

    def get(
        self,
        sucursal: int = 0,
        personal: int = 0,
        raw: bool = False,
    ) -> Union[List[PersonalComercial], List[Dict[str, Any]]]:
        """Fetch commercial staff parsed or raw."""
        raw_data = self.get_raw(sucursal, personal)
        staff_list = (
            raw_data.get("PersonalComercial", {}).get("ePersCom", [])
            if isinstance(raw_data, dict)
            else raw_data
        )
        if raw:
            return staff_list
        return self._client._parse_list(staff_list, PersonalComercial)
