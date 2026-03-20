import pytest
import requests_mock as rm

from chesserp.client import ChessClient


BASE_URL = "http://test-api.local"
API_PATH = "/web/api/chess/v1/"
LOGIN_PATH = "/web/api/chess/v1/auth/login"

LOGIN_RESPONSE = {"sessionId": "JSESSIONID=abc123"}


@pytest.fixture
def mock_api():
    """Provides a requests_mock adapter with login pre-configured."""
    with rm.Mocker() as m:
        m.post(BASE_URL + LOGIN_PATH, json=LOGIN_RESPONSE)
        yield m


@pytest.fixture
def client(mock_api):
    """Provides a ChessClient pointed at the mock API, already logged in."""
    c = ChessClient(
        api_url=BASE_URL,
        username="testuser",
        password="testpass",
    )
    c.login()
    return c
