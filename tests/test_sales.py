"""Tests for sales service (get / get_raw)."""

import pytest

from chesserp.client import ChessClient
from chesserp.models.sales import Sale

BASE_URL = "http://test-api.local"
API_PATH = "/web/api/chess/v1/"
SALES_URL = BASE_URL + API_PATH + "ventas/"


def _make_sale(id_empresa: int = 1, nro_doc: int = 100):
    """Helper: builds a minimal sale dict matching the API schema."""
    return {
        "idEmpresa": id_empresa,
        "dsEmpresa": f"Empresa {id_empresa}",
        "nrodoc": nro_doc,
        "anulado": False,
    }


def _make_response(sales: list, lote_actual: int, total_lotes: int):
    """Helper: wraps sales list in the API response structure."""
    total = len(sales) * total_lotes
    return {
        "dsReporteComprobantesApi": {"VentasResumen": sales},
        "cantComprobantesVentas": (
            f"Numero de lote obtenido: {lote_actual}/{total_lotes}. "
            f"Cantidad de comprobantes totales: {total}"
        ),
    }


# ---------------------------------------------------------------------------
# get — single lote
# ---------------------------------------------------------------------------

class TestGetSalesSingleLote:

    def test_returns_pydantic_models(self, client, mock_api):
        sales = [_make_sale(1, 100), _make_sale(1, 101)]
        mock_api.get(SALES_URL, json=_make_response(sales, 1, 1))

        result = client.sales.get(fecha_desde="2025-01-01", fecha_hasta="2025-01-31")

        assert len(result) == 2
        assert all(isinstance(s, Sale) for s in result)

    def test_fields_match(self, client, mock_api):
        sales = [_make_sale(5, 200)]
        mock_api.get(SALES_URL, json=_make_response(sales, 1, 1))

        result = client.sales.get(fecha_desde="2025-01-01", fecha_hasta="2025-01-31")

        assert result[0].id_empresa == 5
        assert result[0].nro_doc == 200

    def test_raw_returns_dicts(self, client, mock_api):
        sales = [_make_sale(1, 100)]
        mock_api.get(SALES_URL, json=_make_response(sales, 1, 1))

        result = client.sales.get(
            fecha_desde="2025-01-01", fecha_hasta="2025-01-31", raw=True,
        )

        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["nrodoc"] == 100

    def test_empty_response(self, client, mock_api):
        mock_api.get(SALES_URL, json=_make_response([], 1, 1))

        result = client.sales.get(fecha_desde="2025-01-01", fecha_hasta="2025-01-31")

        assert result == []


# ---------------------------------------------------------------------------
# get — multi lote (pagination)
# ---------------------------------------------------------------------------

class TestGetSalesMultiLote:

    def test_fetches_all_lotes(self, client, mock_api):
        """Verifica que se iteren todos los lotes y se acumulen los resultados."""
        lote1 = [_make_sale(1, 100), _make_sale(1, 101)]
        lote2 = [_make_sale(1, 102), _make_sale(1, 103)]
        lote3 = [_make_sale(1, 104)]

        mock_api.get(SALES_URL, [
            {"json": _make_response(lote1, 1, 3)},
            {"json": _make_response(lote2, 2, 3)},
            {"json": _make_response(lote3, 3, 3)},
        ])

        result = client.sales.get(fecha_desde="2025-01-01", fecha_hasta="2025-03-31")

        assert len(result) == 5
        assert [s.nro_doc for s in result] == [100, 101, 102, 103, 104]

    def test_multi_lote_raw(self, client, mock_api):
        lote1 = [_make_sale(1, 100)]
        lote2 = [_make_sale(1, 200)]

        mock_api.get(SALES_URL, [
            {"json": _make_response(lote1, 1, 2)},
            {"json": _make_response(lote2, 2, 2)},
        ])

        result = client.sales.get(
            fecha_desde="2025-01-01", fecha_hasta="2025-01-31", raw=True,
        )

        assert len(result) == 2
        assert all(isinstance(s, dict) for s in result)


# ---------------------------------------------------------------------------
# get_raw — single lote
# ---------------------------------------------------------------------------

class TestGetSalesRaw:

    def test_returns_full_api_dict(self, client, mock_api):
        sales = [_make_sale(1, 100)]
        response = _make_response(sales, 1, 1)
        mock_api.get(SALES_URL, json=response)

        result = client.sales.get_raw(
            fecha_desde="2025-01-01", fecha_hasta="2025-01-31",
        )

        assert "dsReporteComprobantesApi" in result
        assert "cantComprobantesVentas" in result
        items = result["dsReporteComprobantesApi"]["VentasResumen"]
        assert len(items) == 1

    def test_specific_lote(self, client, mock_api):
        sales = [_make_sale(1, 999)]
        mock_api.get(SALES_URL, json=_make_response(sales, 3, 5))

        result = client.sales.get_raw(
            fecha_desde="2025-01-01", fecha_hasta="2025-01-31", nro_lote=3,
        )

        items = result["dsReporteComprobantesApi"]["VentasResumen"]
        assert len(items) == 1
        assert items[0]["nrodoc"] == 999


# ---------------------------------------------------------------------------
# get — error handling
# ---------------------------------------------------------------------------

class TestGetSalesErrors:

    def test_401_triggers_relogin(self, client, mock_api):
        """Si la API retorna 401, el client re-loginea y reintenta."""
        sales = [_make_sale(1, 100)]

        mock_api.get(SALES_URL, [
            {"status_code": 401},
            {"json": _make_response(sales, 1, 1)},
        ])

        result = client.sales.get(fecha_desde="2025-01-01", fecha_hasta="2025-01-31")

        assert len(result) == 1

    def test_500_raises_api_error(self, client, mock_api):
        from chesserp.exceptions import ApiError

        mock_api.get(SALES_URL, status_code=500, text="Internal Server Error")

        with pytest.raises(ApiError) as exc_info:
            client.sales.get(fecha_desde="2025-01-01", fecha_hasta="2025-01-31")

        assert exc_info.value.status_code == 500
