import pytest
from src.client import ChessClient
from src.config.settings import Settings

@pytest.fixture
def mock_settings():
    """Crea una configuración falsa para pruebas."""
    return Settings(
        API_URL_S="http://test-api.com",
        USERNAME_S="test_user",
        PASSWORD_S="test_pass",
        API_URL_B="http://test-api-b.com",
        USERNAME_B="test_user_b",
        PASSWORD_B="test_pass_b"
    )

@pytest.fixture
def client(mock_settings):
    """Retorna una instancia de ChessClient configurada para 'S'."""
    return ChessClient(settings=mock_settings, instance='s')
