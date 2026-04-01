"""Tests for customers service (get / get_raw)."""

import pytest

from chesserp.client import ChessClient
from chesserp.models.clients import Cliente

BASE_URL = "http://test-api.local"
API_PATH = "/web/api/chess/v1/"
CUSTOMERS_URL = BASE_URL + API_PATH + "clientes/"


def _make_customer(id_cliente: int, id_sucursal: int = 1, anulado: bool = False):
    """Helper: builds a minimal customer dict matching the API schema."""
    return {
        "idSucursal": id_sucursal,
        "idCliente": id_cliente,
        "anulado": anulado,
        "razonSocial": f"Cliente Test {id_cliente}",
        "desSucursal": "Sucursal 1",
        "fechaAlta": "2025-01-01",
    }


def _make_response(customers: list, lote_actual: int, total_lotes: int):
    """Helper: wraps customer list in the API response structure."""
    return {
        "Clientes": {"eClientes": customers},
        "cantClientes": f"Numero de lote obtenido: {lote_actual}/{total_lotes}. Cantidad de clientes totales: {len(customers) * total_lotes}",
    }


# ---------------------------------------------------------------------------
# get — single lote
# ---------------------------------------------------------------------------

class TestGetCustomersSingleLote:

    def test_returns_pydantic_models(self, client, mock_api):
        customers = [_make_customer(1), _make_customer(2), _make_customer(3)]
        mock_api.get(CUSTOMERS_URL, json=_make_response(customers, 1, 1))

        result = client.customers.get()

        assert len(result) == 3
        assert all(isinstance(c, Cliente) for c in result)

    def test_ids_match(self, client, mock_api):
        customers = [_make_customer(10), _make_customer(20)]
        mock_api.get(CUSTOMERS_URL, json=_make_response(customers, 1, 1))

        result = client.customers.get()

        assert [c.id_cliente for c in result] == [10, 20]

    def test_raw_returns_dicts(self, client, mock_api):
        customers = [_make_customer(1)]
        mock_api.get(CUSTOMERS_URL, json=_make_response(customers, 1, 1))

        result = client.customers.get(raw=True)

        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["idCliente"] == 1

    def test_empty_response(self, client, mock_api):
        mock_api.get(CUSTOMERS_URL, json=_make_response([], 1, 1))

        result = client.customers.get()

        assert result == []


# ---------------------------------------------------------------------------
# get — multi lote (pagination)
# ---------------------------------------------------------------------------

class TestGetCustomersMultiLote:

    def test_fetches_all_lotes(self, client, mock_api):
        """Verifica que se iteren todos los lotes y se acumulen los resultados."""
        lote1 = [_make_customer(1), _make_customer(2)]
        lote2 = [_make_customer(3), _make_customer(4)]
        lote3 = [_make_customer(5)]

        # Responses queued in order
        mock_api.get(CUSTOMERS_URL, [
            {"json": _make_response(lote1, 1, 3)},
            {"json": _make_response(lote2, 2, 3)},
            {"json": _make_response(lote3, 3, 3)},
        ])

        result = client.customers.get()

        assert len(result) == 5
        assert [c.id_cliente for c in result] == [1, 2, 3, 4, 5]

    def test_multi_lote_raw(self, client, mock_api):
        lote1 = [_make_customer(1)]
        lote2 = [_make_customer(2)]

        mock_api.get(CUSTOMERS_URL, [
            {"json": _make_response(lote1, 1, 2)},
            {"json": _make_response(lote2, 2, 2)},
        ])

        result = client.customers.get(raw=True)

        assert len(result) == 2
        assert all(isinstance(c, dict) for c in result)

    def test_specific_lote(self, client, mock_api):
        """Cuando se pide un lote especifico, solo retorna ese."""
        customers = [_make_customer(99)]
        mock_api.get(CUSTOMERS_URL, json=_make_response(customers, 3, 5))

        result = client.customers.get(nro_lote=3)

        assert len(result) == 1
        assert result[0].id_cliente == 99


# ---------------------------------------------------------------------------
# get — anulado param propagation (hotfix 0.1.1)
# ---------------------------------------------------------------------------

class TestGetCustomersAnulado:

    def test_anulado_true_sent_on_all_lotes(self, client, mock_api):
        """Verifica que anulado=True se pase en TODOS los lotes, no solo el primero."""
        lote1 = [_make_customer(1, anulado=True)]
        lote2 = [_make_customer(2, anulado=True)]

        mock_api.get(CUSTOMERS_URL, [
            {"json": _make_response(lote1, 1, 2)},
            {"json": _make_response(lote2, 2, 2)},
        ])

        client.customers.get(anulado=True)

        # Verify both requests sent anulado=true
        history = mock_api.request_history
        # Filter only GET requests to clientes/
        customer_requests = [r for r in history if "clientes" in r.path]

        for req in customer_requests:
            assert req.qs.get("anulado") == ["true"], (
                f"Request to lote {req.qs.get('nrolote')} missing anulado=true"
            )

    def test_anulado_true_on_specific_lote(self, client, mock_api):
        """Verifica que anulado se pase cuando se pide un lote especifico."""
        customers = [_make_customer(1, anulado=True)]
        mock_api.get(CUSTOMERS_URL, json=_make_response(customers, 2, 3))

        client.customers.get(anulado=True, nro_lote=2)

        customer_requests = [r for r in mock_api.request_history if "clientes" in r.path]
        assert len(customer_requests) == 1
        assert customer_requests[0].qs.get("anulado") == ["true"]

    def test_anulado_false_by_default(self, client, mock_api):
        customers = [_make_customer(1)]
        mock_api.get(CUSTOMERS_URL, json=_make_response(customers, 1, 1))

        client.customers.get()

        customer_requests = [r for r in mock_api.request_history if "clientes" in r.path]
        assert customer_requests[0].qs.get("anulado") == ["false"]


# ---------------------------------------------------------------------------
# get — error handling
# ---------------------------------------------------------------------------

class TestGetCustomersErrors:

    def test_401_triggers_relogin(self, client, mock_api):
        """Si la API retorna 401, el client re-loginea y reintenta."""
        customers = [_make_customer(1)]

        mock_api.get(CUSTOMERS_URL, [
            {"status_code": 401},
            {"json": _make_response(customers, 1, 1)},
        ])

        result = client.customers.get()

        assert len(result) == 1

    def test_500_raises_api_error(self, client, mock_api):
        from chesserp.exceptions import ApiError

        mock_api.get(CUSTOMERS_URL, status_code=500, text="Internal Server Error")

        with pytest.raises(ApiError) as exc_info:
            client.customers.get()

        assert exc_info.value.status_code == 500
