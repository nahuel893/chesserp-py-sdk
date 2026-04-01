"""Tests for marketing service (get / get_raw)."""

import pytest

from chesserp.client import ChessClient
from chesserp.models.marketing import JerarquiaMkt

BASE_URL = "http://test-api.local"
API_PATH = "/web/api/chess/v1/"
MARKETING_URL = BASE_URL + API_PATH + "jerarquiaMkt/"


def _make_segmento(id_segmento: int):
    """Helper: builds a minimal marketing hierarchy dict matching the API schema."""
    return {
        "idSegmentoMkt": id_segmento,
        "desSegmentoMkt": f"Segmento {id_segmento}",
        "compania": True,
    }


def _make_response(segmentos: list):
    """Helper: wraps segmentos list in the API response structure."""
    return {"SubcanalesMkt": {"SegmentosMkt": segmentos}}


# ---------------------------------------------------------------------------
# get — parsed models
# ---------------------------------------------------------------------------

class TestGetMarketing:

    def test_returns_pydantic_models(self, client, mock_api):
        segmentos = [_make_segmento(1), _make_segmento(2)]
        mock_api.get(MARKETING_URL, json=_make_response(segmentos))

        result = client.marketing.get()

        assert len(result) == 2
        assert all(isinstance(s, JerarquiaMkt) for s in result)

    def test_ids_match(self, client, mock_api):
        segmentos = [_make_segmento(10), _make_segmento(20)]
        mock_api.get(MARKETING_URL, json=_make_response(segmentos))

        result = client.marketing.get()

        assert [s.id_segmento_mkt for s in result] == [10, 20]

    def test_empty_response(self, client, mock_api):
        mock_api.get(MARKETING_URL, json=_make_response([]))

        result = client.marketing.get()

        assert result == []

    def test_raw_returns_dicts(self, client, mock_api):
        segmentos = [_make_segmento(1)]
        mock_api.get(MARKETING_URL, json=_make_response(segmentos))

        result = client.marketing.get(raw=True)

        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["idSegmentoMkt"] == 1


# ---------------------------------------------------------------------------
# get_raw — full API response
# ---------------------------------------------------------------------------

class TestGetMarketingRaw:

    def test_get_raw_returns_full_dict(self, client, mock_api):
        segmentos = [_make_segmento(1)]
        mock_api.get(MARKETING_URL, json=_make_response(segmentos))

        result = client.marketing.get_raw()

        assert "SubcanalesMkt" in result
        assert len(result["SubcanalesMkt"]["SegmentosMkt"]) == 1


# ---------------------------------------------------------------------------
# get — params propagation
# ---------------------------------------------------------------------------

class TestGetMarketingParams:

    def test_cod_scan_param_sent(self, client, mock_api):
        mock_api.get(MARKETING_URL, json=_make_response([]))

        client.marketing.get(cod_scan=5)

        req = mock_api.request_history[-1]
        assert req.qs.get("codscan") == ["5"]


# ---------------------------------------------------------------------------
# get — error handling
# ---------------------------------------------------------------------------

class TestGetMarketingErrors:

    def test_500_raises_api_error(self, client, mock_api):
        from chesserp.exceptions import ApiError

        mock_api.get(MARKETING_URL, status_code=500, text="Internal Server Error")

        with pytest.raises(ApiError) as exc_info:
            client.marketing.get()

        assert exc_info.value.status_code == 500
