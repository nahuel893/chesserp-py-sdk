"""Tests for routes service (get / get_raw)."""

import pytest

from chesserp.client import ChessClient
from chesserp.models.routes import RutaVenta

BASE_URL = "http://test-api.local"
API_PATH = "/web/api/chess/v1/"
ROUTES_URL = BASE_URL + API_PATH + "rutasVenta/"


def _make_route(id_ruta: int, id_sucursal: int = 1):
    """Helper: builds a minimal route dict matching the API schema."""
    return {
        "idSucursal": id_sucursal,
        "desSucursal": "Sucursal 1",
        "idRuta": id_ruta,
        "desRuta": f"Ruta {id_ruta}",
        "idFuerzaVentas": 1,
    }


def _make_response(routes: list):
    """Helper: wraps routes list in the API response structure."""
    return {"RutasVenta": {"eRutasVenta": routes}}


# ---------------------------------------------------------------------------
# get — parsed models
# ---------------------------------------------------------------------------

class TestGetRoutes:

    def test_returns_pydantic_models(self, client, mock_api):
        routes = [_make_route(1), _make_route(2)]
        mock_api.get(ROUTES_URL, json=_make_response(routes))

        result = client.routes.get()

        assert len(result) == 2
        assert all(isinstance(r, RutaVenta) for r in result)

    def test_ids_match(self, client, mock_api):
        routes = [_make_route(10), _make_route(20)]
        mock_api.get(ROUTES_URL, json=_make_response(routes))

        result = client.routes.get()

        assert [r.id_ruta for r in result] == [10, 20]

    def test_empty_response(self, client, mock_api):
        mock_api.get(ROUTES_URL, json=_make_response([]))

        result = client.routes.get()

        assert result == []

    def test_raw_returns_dicts(self, client, mock_api):
        routes = [_make_route(1)]
        mock_api.get(ROUTES_URL, json=_make_response(routes))

        result = client.routes.get(raw=True)

        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["idRuta"] == 1


# ---------------------------------------------------------------------------
# get — error response returns empty list (production bug fix)
# ---------------------------------------------------------------------------

class TestGetRoutesErrorResponse:

    def test_api_error_response_returns_empty_list(self, client, mock_api):
        """When API returns {"error": [...]} instead of {"RutasVenta": ...},
        the service should return [] instead of crashing."""
        mock_api.get(ROUTES_URL, json={"error": ["No se encontraron rutas"]})

        result = client.routes.get()

        assert result == []

    def test_api_error_response_raw_returns_empty_list(self, client, mock_api):
        mock_api.get(ROUTES_URL, json={"error": ["No se encontraron rutas"]})

        result = client.routes.get(raw=True)

        assert result == []


# ---------------------------------------------------------------------------
# get_raw — full API response
# ---------------------------------------------------------------------------

class TestGetRoutesRaw:

    def test_get_raw_returns_full_dict(self, client, mock_api):
        routes = [_make_route(1)]
        mock_api.get(ROUTES_URL, json=_make_response(routes))

        result = client.routes.get_raw()

        assert "RutasVenta" in result
        assert len(result["RutasVenta"]["eRutasVenta"]) == 1


# ---------------------------------------------------------------------------
# get — params propagation
# ---------------------------------------------------------------------------

class TestGetRoutesParams:

    def test_sucursal_param_sent(self, client, mock_api):
        mock_api.get(ROUTES_URL, json=_make_response([]))

        client.routes.get(sucursal=3)

        req = mock_api.request_history[-1]
        assert req.qs.get("sucursal") == ["3"]

    def test_fuerza_venta_param_sent(self, client, mock_api):
        mock_api.get(ROUTES_URL, json=_make_response([]))

        client.routes.get(fuerza_venta=2)

        req = mock_api.request_history[-1]
        assert req.qs.get("fuerzaventa") == ["2"]

    def test_anulado_param_sent(self, client, mock_api):
        mock_api.get(ROUTES_URL, json=_make_response([]))

        client.routes.get(anulado=True)

        req = mock_api.request_history[-1]
        assert req.qs.get("anulada") == ["true"]


# ---------------------------------------------------------------------------
# get — error handling
# ---------------------------------------------------------------------------

class TestGetRoutesErrors:

    def test_500_raises_api_error(self, client, mock_api):
        from chesserp.exceptions import ApiError

        mock_api.get(ROUTES_URL, status_code=500, text="Internal Server Error")

        with pytest.raises(ApiError) as exc_info:
            client.routes.get()

        assert exc_info.value.status_code == 500
