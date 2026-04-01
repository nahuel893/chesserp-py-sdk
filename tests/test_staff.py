"""Tests for staff service (get / get_raw)."""

import pytest

from chesserp.client import ChessClient
from chesserp.models.staff import PersonalComercial

BASE_URL = "http://test-api.local"
API_PATH = "/web/api/chess/v1/"
STAFF_URL = BASE_URL + API_PATH + "personalComercial/"


def _make_staff(id_personal: int, id_sucursal: int = 1):
    """Helper: builds a minimal staff dict matching the API schema."""
    return {
        "idSucursal": id_sucursal,
        "desSucursal": "Sucursal 1",
        "idPersonal": id_personal,
        "desPersonal": f"Vendedor {id_personal}",
    }


def _make_response(staff: list):
    """Helper: wraps staff list in the API response structure."""
    return {"PersonalComercial": {"ePersCom": staff}}


# ---------------------------------------------------------------------------
# get — parsed models
# ---------------------------------------------------------------------------

class TestGetStaff:

    def test_returns_pydantic_models(self, client, mock_api):
        staff = [_make_staff(1), _make_staff(2)]
        mock_api.get(STAFF_URL, json=_make_response(staff))

        result = client.staff.get()

        assert len(result) == 2
        assert all(isinstance(s, PersonalComercial) for s in result)

    def test_ids_match(self, client, mock_api):
        staff = [_make_staff(10), _make_staff(20)]
        mock_api.get(STAFF_URL, json=_make_response(staff))

        result = client.staff.get()

        assert [s.id_personal for s in result] == [10, 20]

    def test_empty_response(self, client, mock_api):
        mock_api.get(STAFF_URL, json=_make_response([]))

        result = client.staff.get()

        assert result == []

    def test_raw_returns_dicts(self, client, mock_api):
        staff = [_make_staff(1)]
        mock_api.get(STAFF_URL, json=_make_response(staff))

        result = client.staff.get(raw=True)

        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["idPersonal"] == 1


# ---------------------------------------------------------------------------
# get_raw — full API response
# ---------------------------------------------------------------------------

class TestGetStaffRaw:

    def test_get_raw_returns_full_dict(self, client, mock_api):
        staff = [_make_staff(1)]
        mock_api.get(STAFF_URL, json=_make_response(staff))

        result = client.staff.get_raw()

        assert "PersonalComercial" in result
        assert len(result["PersonalComercial"]["ePersCom"]) == 1


# ---------------------------------------------------------------------------
# get — params propagation
# ---------------------------------------------------------------------------

class TestGetStaffParams:

    def test_sucursal_param_sent(self, client, mock_api):
        mock_api.get(STAFF_URL, json=_make_response([]))

        client.staff.get(sucursal=5)

        req = mock_api.request_history[-1]
        assert req.qs.get("sucursal") == ["5"]

    def test_personal_param_sent(self, client, mock_api):
        mock_api.get(STAFF_URL, json=_make_response([]))

        client.staff.get(personal=42)

        req = mock_api.request_history[-1]
        assert req.qs.get("personal") == ["42"]


# ---------------------------------------------------------------------------
# get — error handling
# ---------------------------------------------------------------------------

class TestGetStaffErrors:

    def test_500_raises_api_error(self, client, mock_api):
        from chesserp.exceptions import ApiError

        mock_api.get(STAFF_URL, status_code=500, text="Internal Server Error")

        with pytest.raises(ApiError) as exc_info:
            client.staff.get()

        assert exc_info.value.status_code == 500
