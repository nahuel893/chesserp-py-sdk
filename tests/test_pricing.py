"""Tests for ChessWebClient — price lists endpoints via PricingService."""

import pytest
import requests_mock as rm

from chesserp.web_client import ChessWebClient
from chesserp.models.pricing import ListaPrecio, PrecioArticulo
from chesserp.exceptions import AuthError, ApiError

BASE_URL = "http://test-api.local"
LOGIN_URL = BASE_URL + "/static/auth/j_spring_security_check"
VIGENCIAS_URL = BASE_URL + "/web/api/precios/obtenerVigenciasListas"
LISTA_URL = BASE_URL + "/web/api/precios/obtenerListaPrecios"


def _make_lista(id_lista=1, titulo="LISTA TEST", id_vigencia=100, vigente=True):
    return {
        "listaspre": id_lista,
        "titulis": titulo,
        "idvigencia": id_vigencia,
        "vigente": vigente,
        "fecvigenciadesde": "2026-01-01T00:00:00.000",
        "fecvigenciahasta": None,
    }


def _make_precio(cod="ART001", descrip="Articulo Test", precio=100.0, prefin=121.0):
    return {
        "codart": cod,
        "descrip": descrip,
        "despre": "Caja x 12",
        "precio": precio,
        "iva1": 21.0,
        "prefin": prefin,
        "marca": "MARCA TEST",
        "codmarca": 1,
        "anulado": False,
    }


@pytest.fixture
def mock_api():
    with rm.Mocker() as m:
        yield m


@pytest.fixture
def client(mock_api):
    """Cliente pre-autenticado: inyecta cookie directamente sin pasar por login real."""
    c = ChessWebClient(api_url=BASE_URL, username="user", password="pass")
    c._session.cookies.set("JSESSIONID", "test-session-123", domain="test-api.local")
    c._authenticated = True
    return c


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class TestChessWebClientAuth:

    def test_login_sets_authenticated(self, mock_api):
        """Verifica que login() setea _authenticated cuando recibe JSESSIONID."""
        from unittest.mock import patch
        c = ChessWebClient(api_url=BASE_URL, username="user", password="pass")
        # Simulamos que la sesion ya tiene la cookie (como lo haria Spring Security)
        with patch.object(c._session, "post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.raise_for_status = lambda: None
            c._session.cookies.set("JSESSIONID", "fake-id", domain="test-api.local")
            c.login()
        assert c._authenticated is True

    def test_login_failed_no_jsessionid_raises(self, mock_api):
        mock_api.post(LOGIN_URL, text="")  # sin cookie
        c = ChessWebClient(api_url=BASE_URL, username="bad", password="bad")
        with pytest.raises(AuthError, match="JSESSIONID"):
            c.login()

    def test_auto_login_on_first_request(self, mock_api):
        """Sin login previo, el primer request dispara login automatico."""
        mock_api.post(LOGIN_URL, text="")  # sin JSESSIONID — fallara con AuthError
        mock_api.get(VIGENCIAS_URL, json={"eListaPrecios": []})
        c = ChessWebClient(api_url=BASE_URL, username="user", password="pass")
        # El auto-login falla porque el mock no da JSESSIONID — AuthError esperado
        with pytest.raises(AuthError):
            c.pricing.get_lists()

    def test_401_triggers_relogin(self, client, mock_api):
        mock_api.get(VIGENCIAS_URL, status_code=401)
        mock_api.post(LOGIN_URL, text="")  # sin JSESSIONID — fallara con AuthError
        # Simular sesion expirada: borrar la cookie inyectada por el fixture
        client._session.cookies.clear()
        with pytest.raises(AuthError):
            client.pricing.get_lists()  # 401 dispara relogin, pero mock POST no da cookie


# ---------------------------------------------------------------------------
# pricing.get_lists
# ---------------------------------------------------------------------------

class TestGetPriceLists:

    def test_returns_pydantic_models(self, client, mock_api):
        listas = [_make_lista(1), _make_lista(2)]
        mock_api.get(VIGENCIAS_URL, json={"eListaPrecios": listas})

        result = client.pricing.get_lists()

        assert len(result) == 2
        assert all(isinstance(l, ListaPrecio) for l in result)

    def test_filters_solo_vigentes_by_default(self, client, mock_api):
        listas = [
            _make_lista(1, vigente=True),
            _make_lista(2, vigente=False),
            _make_lista(3, vigente=True),
        ]
        mock_api.get(VIGENCIAS_URL, json={"eListaPrecios": listas})

        result = client.pricing.get_lists()

        assert len(result) == 2
        assert all(l.vigente for l in result)

    def test_solo_vigentes_false_returns_all(self, client, mock_api):
        listas = [_make_lista(1, vigente=True), _make_lista(2, vigente=False)]
        mock_api.get(VIGENCIAS_URL, json={"eListaPrecios": listas})

        result = client.pricing.get_lists(solo_vigentes=False)

        assert len(result) == 2

    def test_raw_returns_dicts(self, client, mock_api):
        listas = [_make_lista(1)]
        mock_api.get(VIGENCIAS_URL, json={"eListaPrecios": listas})

        result = client.pricing.get_lists(raw=True)

        assert isinstance(result[0], dict)
        assert result[0]["listaspre"] == 1

    def test_empty_response(self, client, mock_api):
        mock_api.get(VIGENCIAS_URL, json={"eListaPrecios": []})

        result = client.pricing.get_lists()

        assert result == []

    def test_ids_and_titles(self, client, mock_api):
        listas = [_make_lista(5, titulo="LISTA MAYORISTA", id_vigencia=999)]
        mock_api.get(VIGENCIAS_URL, json={"eListaPrecios": listas})

        result = client.pricing.get_lists()

        assert result[0].id_lista == 5
        assert result[0].titulo == "LISTA MAYORISTA"
        assert result[0].id_vigencia == 999


# ---------------------------------------------------------------------------
# pricing.get_items
# ---------------------------------------------------------------------------

class TestGetPriceListItems:

    def test_returns_pydantic_models(self, client, mock_api):
        precios = [_make_precio("A001"), _make_precio("A002")]
        mock_api.get(LISTA_URL, json={"dsPrecios": {"ePrecios": precios}})

        result = client.pricing.get_items(id_lista=1, id_vigencia=100)

        assert len(result) == 2
        assert all(isinstance(p, PrecioArticulo) for p in result)

    def test_fields_mapped_correctly(self, client, mock_api):
        precios = [_make_precio("A001", precio=50.0, prefin=60.5)]
        mock_api.get(LISTA_URL, json={"dsPrecios": {"ePrecios": precios}})

        result = client.pricing.get_items(id_lista=1, id_vigencia=100)

        assert result[0].cod_articulo == "A001"
        assert result[0].precio == 50.0
        assert result[0].precio_final == 60.5

    def test_raw_returns_dicts(self, client, mock_api):
        precios = [_make_precio("A001")]
        mock_api.get(LISTA_URL, json={"dsPrecios": {"ePrecios": precios}})

        result = client.pricing.get_items(id_lista=1, id_vigencia=100, raw=True)

        assert isinstance(result[0], dict)
        assert result[0]["codart"] == "A001"

    def test_sends_correct_params(self, client, mock_api):
        mock_api.get(LISTA_URL, json={"dsPrecios": {"ePrecios": []}})

        client.pricing.get_items(id_lista=3, id_vigencia=777)

        req = mock_api.last_request
        assert req.qs["pilis"] == ["3"]
        assert req.qs["pivig"] == ["777"]
        assert req.qs["plpre"] == ["false"]

    def test_empty_response(self, client, mock_api):
        mock_api.get(LISTA_URL, json={"dsPrecios": {"ePrecios": []}})

        result = client.pricing.get_items(id_lista=1, id_vigencia=100)

        assert result == []

    def test_500_raises_api_error(self, client, mock_api):
        mock_api.get(LISTA_URL, status_code=500, text="error")

        with pytest.raises(ApiError) as exc_info:
            client.pricing.get_items(id_lista=1, id_vigencia=100)

        assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# from_env
# ---------------------------------------------------------------------------

class TestFromEnv:

    def test_from_env_reads_prefix(self, monkeypatch):
        monkeypatch.setenv("TEST_API_URL", "http://test.local")
        monkeypatch.setenv("TEST_USERNAME", "user")
        monkeypatch.setenv("TEST_PASSWORD", "pass")

        c = ChessWebClient.from_env(prefix="TEST_")

        assert c.api_url == "http://test.local"
        assert c.username == "user"

    def test_from_env_missing_vars_raises(self, monkeypatch):
        monkeypatch.delenv("TEST_API_URL", raising=False)
        monkeypatch.delenv("TEST_USERNAME", raising=False)
        monkeypatch.delenv("TEST_PASSWORD", raising=False)

        with pytest.raises(ValueError, match="TEST_API_URL"):
            ChessWebClient.from_env(prefix="TEST_")
