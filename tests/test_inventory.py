"""Tests for inventory service (articles + stock)."""

import pytest

from chesserp.client import ChessClient
from chesserp.models.inventory import Articulo, StockFisico

BASE_URL = "http://test-api.local"
API_PATH = "/web/api/chess/v1/"
ARTICLES_URL = BASE_URL + API_PATH + "articulos/"
STOCK_URL = BASE_URL + API_PATH + "stock/"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_article(id_articulo: int, anulado: bool = False):
    """Helper: builds a minimal article dict matching the API schema."""
    return {
        "idArticulo": id_articulo,
        "desArticulo": f"Articulo {id_articulo}",
        "anulado": anulado,
        "fechaAlta": "2025-01-01",
    }


def _make_articles_response(articles: list, lote_actual: int, total_lotes: int):
    """Helper: wraps articles list in the API response structure."""
    total = len(articles) * total_lotes
    return {
        "Articulos": {"eArticulos": articles},
        "cantArticulos": (
            f"Numero de lote obtenido: {lote_actual}/{total_lotes}. "
            f"Cantidad de articulos totales: {total}"
        ),
    }


def _make_stock_item(id_articulo: int, cant_bultos: float = 10.0):
    """Helper: builds a minimal stock dict."""
    return {
        "idArticulo": id_articulo,
        "dsArticulo": f"Articulo {id_articulo}",
        "idDeposito": 1,
        "cantBultos": cant_bultos,
        "cantUnidades": cant_bultos * 12,
    }


def _make_stock_response(stock_items: list):
    """Helper: wraps stock list in the API response structure."""
    return {"dsStockFisicoApi": {"dsStock": stock_items}}


# ---------------------------------------------------------------------------
# get_articles — single lote
# ---------------------------------------------------------------------------

class TestGetArticlesSingleLote:

    def test_returns_pydantic_models(self, client, mock_api):
        articles = [_make_article(1), _make_article(2)]
        mock_api.get(ARTICLES_URL, json=_make_articles_response(articles, 1, 1))

        result = client.inventory.get_articles()

        assert len(result) == 2
        assert all(isinstance(a, Articulo) for a in result)

    def test_ids_match(self, client, mock_api):
        articles = [_make_article(10), _make_article(20)]
        mock_api.get(ARTICLES_URL, json=_make_articles_response(articles, 1, 1))

        result = client.inventory.get_articles()

        assert [a.id_articulo for a in result] == [10, 20]

    def test_raw_returns_dicts(self, client, mock_api):
        articles = [_make_article(1)]
        mock_api.get(ARTICLES_URL, json=_make_articles_response(articles, 1, 1))

        result = client.inventory.get_articles(raw=True)

        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["idArticulo"] == 1

    def test_empty_response(self, client, mock_api):
        mock_api.get(ARTICLES_URL, json=_make_articles_response([], 1, 1))

        result = client.inventory.get_articles()

        assert result == []


# ---------------------------------------------------------------------------
# get_articles — multi lote (pagination)
# ---------------------------------------------------------------------------

class TestGetArticlesMultiLote:

    def test_fetches_all_lotes(self, client, mock_api):
        """Verifica que se iteren todos los lotes y se acumulen los resultados."""
        lote1 = [_make_article(1), _make_article(2)]
        lote2 = [_make_article(3)]

        mock_api.get(ARTICLES_URL, [
            {"json": _make_articles_response(lote1, 1, 2)},
            {"json": _make_articles_response(lote2, 2, 2)},
        ])

        result = client.inventory.get_articles()

        assert len(result) == 3
        assert [a.id_articulo for a in result] == [1, 2, 3]

    def test_multi_lote_raw(self, client, mock_api):
        lote1 = [_make_article(1)]
        lote2 = [_make_article(2)]

        mock_api.get(ARTICLES_URL, [
            {"json": _make_articles_response(lote1, 1, 2)},
            {"json": _make_articles_response(lote2, 2, 2)},
        ])

        result = client.inventory.get_articles(raw=True)

        assert len(result) == 2
        assert all(isinstance(a, dict) for a in result)


# ---------------------------------------------------------------------------
# get_articles_raw
# ---------------------------------------------------------------------------

class TestGetArticlesRaw:

    def test_returns_full_api_dict(self, client, mock_api):
        articles = [_make_article(1)]
        response = _make_articles_response(articles, 1, 1)
        mock_api.get(ARTICLES_URL, json=response)

        result = client.inventory.get_articles_raw()

        assert "Articulos" in result
        assert "cantArticulos" in result


# ---------------------------------------------------------------------------
# get_stock — not paginated
# ---------------------------------------------------------------------------

class TestGetStock:

    def test_returns_pydantic_models(self, client, mock_api):
        items = [_make_stock_item(1), _make_stock_item(2)]
        mock_api.get(STOCK_URL, json=_make_stock_response(items))

        result = client.inventory.get_stock(id_deposito=1)

        assert len(result) == 2
        assert all(isinstance(s, StockFisico) for s in result)

    def test_ids_match(self, client, mock_api):
        items = [_make_stock_item(10, 5.0), _make_stock_item(20, 15.0)]
        mock_api.get(STOCK_URL, json=_make_stock_response(items))

        result = client.inventory.get_stock(id_deposito=1)

        assert [s.id_articulo for s in result] == [10, 20]
        assert result[0].cant_bultos == 5.0

    def test_raw_returns_dicts(self, client, mock_api):
        items = [_make_stock_item(1)]
        mock_api.get(STOCK_URL, json=_make_stock_response(items))

        result = client.inventory.get_stock(id_deposito=1, raw=True)

        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["idArticulo"] == 1

    def test_empty_response(self, client, mock_api):
        mock_api.get(STOCK_URL, json=_make_stock_response([]))

        result = client.inventory.get_stock(id_deposito=1)

        assert result == []


# ---------------------------------------------------------------------------
# get_stock_raw
# ---------------------------------------------------------------------------

class TestGetStockRaw:

    def test_returns_full_api_dict(self, client, mock_api):
        items = [_make_stock_item(1)]
        mock_api.get(STOCK_URL, json=_make_stock_response(items))

        result = client.inventory.get_stock_raw(id_deposito=1)

        assert "dsStockFisicoApi" in result
        assert len(result["dsStockFisicoApi"]["dsStock"]) == 1
