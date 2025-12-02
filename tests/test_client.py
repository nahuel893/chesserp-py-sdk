import pytest
import requests
from src.exceptions import AuthError, ApiError
from src.models.sales import Sale

def test_login_success(client, requests_mock):
    """Prueba que el login guarde el session ID correctamente."""
    # Simulamos la respuesta de la API
    requests_mock.post(
        "http://test-api.com/web/api/chess/v1/auth/login",
        json={"sessionId": "fake-session-123", "usuario": "test_user"},
        status_code=200
    )

    session_id = client.login()

    assert session_id == "fake-session-123"
    assert client._session_id == "fake-session-123"
    assert client.session.headers["Cookie"] == "fake-session-123"

def test_login_failure(client, requests_mock):
    """Prueba que falle correctamente si las credenciales son malas."""
    requests_mock.post(
        "http://test-api.com/web/api/chess/v1/auth/login",
        status_code=401,
        text="Unauthorized"
    )

    with pytest.raises(AuthError) as excinfo:
        client.login()
    
    assert "Login failed" in str(excinfo.value)

def test_get_sales_success(client, requests_mock):
    """Prueba la obtención y parseo de ventas."""
    # 1. Mock del login (necesario porque _get llama a login si no hay sesión)
    requests_mock.post(
        "http://test-api.com/web/api/chess/v1/auth/login",
        json={"sessionId": "fake-session-123"}
    )
    
    # 2. Mock de la respuesta de ventas
    # Ajustamos el mock para cumplir con los campos OBLIGATORIOS del modelo Sale
    mock_sales_data = [
        {
            "idEmpresa": 1,
            "idDocumento": 10,
            "letra": "A",
            "serie": "0001",
            "nrodoc": 12345678,
            "fechaComprobate": "01-01-2023", # Nota el typo 'Comprobate' que está en el modelo
            "idSucursal": 5,
            "idCliente": 99,
            "nombreCliente": "Cliente Test",
            "subtotalFinal": 121.0
        }
    ]
    
    # NOTA: Ajusta la URL si client.py agrega slashes extra o no
    requests_mock.get(
        "http://test-api.com/web/api/chess/v1/ventas/",
        json=mock_sales_data,
        status_code=200
    )

    # Ejecutar
    sales = client.get_sales(fecha_desde="2023-01-01", fecha_hasta="2023-01-31")

    # Validar
    assert len(sales) == 1
    # Verifica que sea una instancia del modelo Sale (y no un dict)
    # Esto validará implícitamente que el modelo Pydantic funciona
    # Si falla aquí, es posible que el mock data no coincida con el modelo Sale
    # Lo dejaremos correr para ver si el modelo Sale tiene validaciones estrictas
