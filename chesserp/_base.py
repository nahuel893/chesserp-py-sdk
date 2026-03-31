"""Base client with shared HTTP infrastructure for all ChessERP API clients."""

import os
import re
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

import requests
from dotenv import load_dotenv

from chesserp.exceptions import AuthError, ApiError
from chesserp.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class BaseClient(ABC):
    """
    Abstract base for ChessERP API clients.

    Provides session management, auto-retry on 401, pagination,
    and Pydantic parsing. Subclasses implement ``login()`` only.
    """

    def __init__(
        self,
        api_url: str,
        username: str,
        password: str,
        api_path: str,
        login_path: str,
        timeout: int = 30,
        name: Optional[str] = None,
    ):
        self.api_url = api_url.rstrip("/")
        self.username = username
        self.password = password
        self.api_path = api_path
        self.login_path = login_path.rstrip("/")
        self.timeout = timeout
        self.name = name or api_url

        self.base_url = self.api_url + self.api_path
        self._login_url = self.api_url + self.login_path
        self._session = requests.Session()
        self._authenticated = False

    @classmethod
    def from_env(cls, prefix: str = "", env_file: Optional[str] = None, **kwargs):
        """Create a client from environment variables with an optional prefix."""
        if env_file:
            load_dotenv(env_file)

        api_url = os.getenv(f"{prefix}API_URL")
        username = os.getenv(f"{prefix}USERNAME")
        password = os.getenv(f"{prefix}PASSWORD")

        if not all([api_url, username, password]):
            missing = []
            if not api_url:
                missing.append(f"{prefix}API_URL")
            if not username:
                missing.append(f"{prefix}USERNAME")
            if not password:
                missing.append(f"{prefix}PASSWORD")
            raise ValueError(f"Variables de entorno faltantes: {', '.join(missing)}")

        return cls(
            api_url=api_url,
            username=username,
            password=password,
            name=prefix.rstrip("_") if prefix else None,
            **kwargs,
        )

    @abstractmethod
    def login(self) -> None:
        """Authenticate and store credentials in the session."""
        ...

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """GET with automatic login and 401 retry."""
        if not self._authenticated:
            self.login()

        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        url = self.base_url + endpoint

        try:
            resp = self._session.get(url, params=params, timeout=self.timeout)

            if resp.status_code == 401:
                logger.warning("Session expired (401). Retrying login...")
                self.login()
                resp = self._session.get(url, params=params, timeout=self.timeout)

            if resp.status_code != 200:
                raise ApiError(resp.status_code, f"Request to {endpoint} failed", resp.text)

            json_data = resp.json()
            if isinstance(json_data, list) and len(json_data) == 0:
                logger.debug(f"Empty list returned from {endpoint}")
            return json_data

        except requests.RequestException as e:
            raise ApiError(500, f"Connection error: {str(e)}")

    def _post(
        self,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
    ) -> requests.Response:
        """POST with automatic login and 401 retry. Returns the raw Response."""
        if not self._authenticated:
            self.login()

        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        url = self.base_url + endpoint
        _timeout = timeout or self.timeout

        try:
            resp = self._session.post(url, json=json, data=data, timeout=_timeout)

            if resp.status_code == 401:
                logger.warning("Session expired (401). Retrying login...")
                self.login()
                resp = self._session.post(url, json=json, data=data, timeout=_timeout)

            return resp

        except requests.RequestException as e:
            raise ApiError(500, f"Connection error: {str(e)}")

    def _parse_list(self, data: Any, model_class: type) -> list:
        """Parse a list of dicts into Pydantic models, skipping failures."""
        if not isinstance(data, list):
            logger.warning(f"Se esperaba una lista, se recibio: {type(data)}")
            return []

        parsed = []
        for i, item in enumerate(data):
            try:
                parsed.append(model_class(**item))
            except Exception as e:
                logger.error(
                    f"Error parseando item #{i} en {model_class.__name__}: {e}. "
                    f"Item fallido: {item}"
                )
        return parsed

    def _fetch_paginated(
        self,
        raw_fetcher: Callable[[int], Dict[str, Any]],
        data_path: list[str],
        count_key: str,
        model_class: type | None = None,
        raw: bool = False,
    ) -> list:
        """
        Generic lote-based pagination.

        Args:
            raw_fetcher: callable(nro_lote) -> dict (the raw API response)
            data_path: keys to navigate to the items list, e.g. ["Clientes", "eClientes"]
            count_key: top-level key with pagination string, e.g. "cantClientes"
            model_class: Pydantic model for parsing (ignored when raw=True)
            raw: if True return raw dicts, else parsed models
        """
        response = raw_fetcher(1)
        accumulated: list = []

        if not isinstance(response, dict):
            return accumulated

        # Navigate data_path
        items = response
        for key in data_path:
            items = items.get(key, {}) if isinstance(items, dict) else {}
        if not isinstance(items, list):
            items = []

        if items:
            if raw:
                accumulated.extend(items)
            else:
                accumulated.extend(self._parse_list(items, model_class))
            logger.info(f"Lote 1 procesado: {len(items)} registros")

        # Parse pagination string
        count_str = response.get(count_key, "")
        match = re.search(r"(\d+)/(\d[\d.]*)", count_str)
        if match:
            lote_actual = int(match.group(1))
            total_lotes = int(match.group(2).replace(".", ""))
            logger.info(f"Total de lotes a procesar: {total_lotes}")

            for i in range(lote_actual + 1, total_lotes + 1):
                resp = raw_fetcher(i)
                if isinstance(resp, dict):
                    batch = resp
                    for key in data_path:
                        batch = batch.get(key, {}) if isinstance(batch, dict) else {}
                    if isinstance(batch, list) and batch:
                        if raw:
                            accumulated.extend(batch)
                        else:
                            accumulated.extend(self._parse_list(batch, model_class))
                        logger.info(f"Lote {i}/{total_lotes} procesado: {len(batch)} registros")
        else:
            if count_str:
                logger.warning(f"No se pudo parsear total de lotes de: {count_str}. Asumiendo 1 lote.")

        logger.info(f"Total obtenidos: {len(accumulated)}")
        return accumulated
