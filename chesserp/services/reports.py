"""Reports service — binary Excel export for sales reports."""

from typing import Optional

import requests

from chesserp.exceptions import ApiError
from chesserp.services import BaseService
from chesserp.logger import get_logger

logger = get_logger(__name__)


class ReportsService(BaseService):

    def export_sales_report(
        self,
        fecha_desde: str,
        fecha_hasta: str,
        idsucur: str = "1",
        empresas: str = "1",
        tiposdoc: str = "DVVTA,FCVTA",
        formasagruart: str = "MARCA,GENERICO,,,,,,,,",
        timeout: Optional[int] = None,
    ) -> bytes:
        """
        Request and download a sales report (Excel).

        Flow:
        1. POST to reporteComprobantesVta/exportarExcel with filters.
        2. Response contains 'pcArchivo' path.
        3. GET that path to download bytes.
        """
        payload = {
            "dsFiltrosRepCbtsVta": {
                "eFiltros": [
                    {
                        "letra": None,
                        "serie": None,
                        "numero": None,
                        "numeroHasta": None,
                        "fechadesde": fecha_desde,
                        "fechahasta": fecha_hasta,
                        "idsucur": idsucur,
                        "timbrado": "",
                        "empresas": empresas,
                        "tiposdoc": tiposdoc,
                        "formasagruart": formasagruart,
                    }
                ]
            },
            "pcTipo": "D",
        }

        name = self._client.name
        logger.info(f"[{name}] Requesting sales report export: {fecha_desde} to {fecha_hasta}...")

        # Step 1: request export
        resp = self._client._post(
            "reporteComprobantesVta/exportarExcel",
            json=payload,
            timeout=timeout,
        )

        if resp.status_code != 200:
            raise ApiError(resp.status_code, "Failed to request report export", resp.text)

        data = resp.json()
        pc_archivo = data.get("pcArchivo")

        if not pc_archivo:
            raise ApiError(500, "API response missing 'pcArchivo' field")

        # Step 2: download file
        file_url = f"{self._client.api_url}/{pc_archivo.lstrip('/')}"
        logger.info(f"[{name}] Downloading report from {file_url}...")

        try:
            _timeout = timeout or self._client.timeout
            file_resp = self._client._session.get(file_url, timeout=_timeout)

            if file_resp.status_code != 200:
                raise ApiError(file_resp.status_code, "Failed to download report file", file_resp.text)

            return file_resp.content

        except requests.RequestException as e:
            raise ApiError(500, f"Connection error during report download: {str(e)}")
