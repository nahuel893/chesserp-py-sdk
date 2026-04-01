"""Tests for reports service (export_sales_report)."""

import pytest

from chesserp.client import ChessClient
from chesserp.exceptions import ApiError

BASE_URL = "http://test-api.local"
API_PATH = "/web/api/chess/v1/"
EXPORT_URL = BASE_URL + API_PATH + "reporteComprobantesVta/exportarExcel"


# ---------------------------------------------------------------------------
# export_sales_report — success
# ---------------------------------------------------------------------------

class TestExportSalesReport:

    def test_returns_bytes(self, client, mock_api):
        """Full flow: POST export -> GET file -> returns bytes."""
        file_content = b"fake-excel-binary-content"
        file_path = "/web/api/chess/v1/reports/export_12345.xlsx"

        mock_api.post(EXPORT_URL, json={"pcArchivo": file_path})
        mock_api.get(BASE_URL + "/" + file_path.lstrip("/"), content=file_content)

        result = client.reports.export_sales_report(
            fecha_desde="2025-01-01",
            fecha_hasta="2025-01-31",
        )

        assert isinstance(result, bytes)
        assert result == file_content

    def test_sends_correct_params(self, client, mock_api):
        file_path = "/reports/export.xlsx"
        mock_api.post(EXPORT_URL, json={"pcArchivo": file_path})
        mock_api.get(BASE_URL + "/" + file_path.lstrip("/"), content=b"data")

        client.reports.export_sales_report(
            fecha_desde="2025-03-01",
            fecha_hasta="2025-03-31",
            idsucur="2",
            empresas="3",
        )

        # Verify the POST payload
        req = [r for r in mock_api.request_history if r.method == "POST" and "exportarExcel" in r.url][0]
        body = req.json()
        filtro = body["dsFiltrosRepCbtsVta"]["eFiltros"][0]
        assert filtro["fechadesde"] == "2025-03-01"
        assert filtro["fechahasta"] == "2025-03-31"
        assert filtro["idsucur"] == "2"
        assert filtro["empresas"] == "3"


# ---------------------------------------------------------------------------
# export_sales_report — error handling
# ---------------------------------------------------------------------------

class TestExportSalesReportErrors:

    def test_post_http_error_raises(self, client, mock_api):
        mock_api.post(EXPORT_URL, status_code=500, text="Server Error")

        with pytest.raises(ApiError) as exc_info:
            client.reports.export_sales_report(
                fecha_desde="2025-01-01",
                fecha_hasta="2025-01-31",
            )

        assert exc_info.value.status_code == 500

    def test_missing_pc_archivo_raises(self, client, mock_api):
        """When API response is missing pcArchivo field, should raise ApiError."""
        mock_api.post(EXPORT_URL, json={"otherField": "value"})

        with pytest.raises(ApiError):
            client.reports.export_sales_report(
                fecha_desde="2025-01-01",
                fecha_hasta="2025-01-31",
            )

    def test_file_download_http_error_raises(self, client, mock_api):
        file_path = "/reports/export.xlsx"
        mock_api.post(EXPORT_URL, json={"pcArchivo": file_path})
        mock_api.get(BASE_URL + "/" + file_path.lstrip("/"), status_code=404, text="Not Found")

        with pytest.raises(ApiError) as exc_info:
            client.reports.export_sales_report(
                fecha_desde="2025-01-01",
                fecha_hasta="2025-01-31",
            )

        assert exc_info.value.status_code == 404
