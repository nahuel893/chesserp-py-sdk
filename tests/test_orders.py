"""Tests for orders service (get / get_raw)."""

import pytest

from chesserp.client import ChessClient
from chesserp.models.orders import Pedido

BASE_URL = "http://test-api.local"
API_PATH = "/web/api/chess/v1/"
ORDERS_URL = BASE_URL + API_PATH + "pedidos/"


def _make_order(id_pedido: str, id_cliente: int = 1):
    """Helper: builds a minimal order dict matching the API schema."""
    return {
        "idPedido": id_pedido,
        "idCliente": id_cliente,
        "idEmpresa": 1,
        "idSucursal": 1,
        "fechaEntrega": "2025-02-01",
    }


def _make_response(orders: list):
    """Helper: wraps orders list in the API response structure."""
    return {"pedidos": orders}


# ---------------------------------------------------------------------------
# get — parsed
# ---------------------------------------------------------------------------

class TestGetOrders:

    def test_returns_pydantic_models(self, client, mock_api):
        orders = [_make_order("NXB-1-001"), _make_order("NXB-1-002")]
        mock_api.get(ORDERS_URL, json=_make_response(orders))

        result = client.orders.get()

        assert len(result) == 2
        assert all(isinstance(p, Pedido) for p in result)

    def test_fields_match(self, client, mock_api):
        orders = [_make_order("NXB-5-100", id_cliente=42)]
        mock_api.get(ORDERS_URL, json=_make_response(orders))

        result = client.orders.get()

        assert result[0].id_pedido == "NXB-5-100"
        assert result[0].id_cliente == 42

    def test_raw_returns_dicts(self, client, mock_api):
        orders = [_make_order("NXB-1-001")]
        mock_api.get(ORDERS_URL, json=_make_response(orders))

        result = client.orders.get(raw=True)

        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["idPedido"] == "NXB-1-001"

    def test_empty_response(self, client, mock_api):
        mock_api.get(ORDERS_URL, json=_make_response([]))

        result = client.orders.get()

        assert result == []


# ---------------------------------------------------------------------------
# get_raw
# ---------------------------------------------------------------------------

class TestGetOrdersRaw:

    def test_returns_full_api_dict(self, client, mock_api):
        orders = [_make_order("NXB-1-001")]
        mock_api.get(ORDERS_URL, json=_make_response(orders))

        result = client.orders.get_raw()

        assert "pedidos" in result
        assert len(result["pedidos"]) == 1

    def test_passes_params(self, client, mock_api):
        mock_api.get(ORDERS_URL, json=_make_response([]))

        client.orders.get_raw(
            fecha_entrega="2025-02-01",
            fecha_pedido="2025-01-15",
            facturado=True,
        )

        req = [r for r in mock_api.request_history if "pedidos" in r.path]
        assert len(req) == 1
        assert req[0].qs.get("fechaentrega") == ["2025-02-01"]
        assert req[0].qs.get("fechapedido") == ["2025-01-15"]
        assert req[0].qs.get("facturado") == ["true"]


# ---------------------------------------------------------------------------
# get — error handling
# ---------------------------------------------------------------------------

class TestGetOrdersErrors:

    def test_401_triggers_relogin(self, client, mock_api):
        """Si la API retorna 401, el client re-loginea y reintenta."""
        orders = [_make_order("NXB-1-001")]

        mock_api.get(ORDERS_URL, [
            {"status_code": 401},
            {"json": _make_response(orders)},
        ])

        result = client.orders.get()

        assert len(result) == 1

    def test_500_raises_api_error(self, client, mock_api):
        from chesserp.exceptions import ApiError

        mock_api.get(ORDERS_URL, status_code=500, text="Internal Server Error")

        with pytest.raises(ApiError) as exc_info:
            client.orders.get()

        assert exc_info.value.status_code == 500
