# Test Suite Design - ChessERP Python SDK

> Fecha: 2026-02-23

## Objetivo

Restaurar tests automatizados para el proyecto (eliminados en commit `6b93644`). Cubrir todos los metodos publicos de `ChessClient` con unit tests (mocks HTTP) e integration tests (API real).

## Estructura

```
tests/
├── conftest.py              # Fixtures compartidas (mock client, fake responses)
├── test_client_init.py      # __init__, from_env, login
├── test_client_get.py       # _get, _parse_list (metodos internos)
├── test_sales.py            # get_sales, get_sales_raw, export_sales_report
├── test_inventory.py        # get_articles, get_stock
├── test_customers.py        # get_customers
├── test_orders.py           # get_orders
├── test_staff.py            # get_staff
├── test_routes.py           # get_routes
├── test_marketing.py        # get_marketing
└── integration/
    └── test_api_real.py     # Tests contra API real (skip si no hay .env)
```

## Unit Tests (requests_mock)

Mock de `requests.get`/`requests.post` con JSONs que replican la estructura real de la API.

### Cobertura por area

**Inicializacion y auth (`test_client_init.py`)**:
- `__init__`: construccion correcta de URLs, defaults
- `from_env`: lectura de env vars con prefijo, error si faltan variables
- `login`: exitoso (guarda sessionId), fallido (401 -> AuthError), error de conexion

**Metodos internos (`test_client_get.py`)**:
- `_get`: request con session, auto-login si no hay session, re-login en 401, ApiError en otros status
- `_parse_list`: lista valida, item con error (loguea y continua), input no-lista retorna []

**Endpoints con paginacion (`test_sales.py`, `test_inventory.py`, `test_customers.py`)**:
- Respuesta de 1 lote (sin paginacion extra)
- Respuesta multi-lote (verifica que itera todos)
- Modo `raw=True` retorna dicts
- Modo `raw=False` retorna objetos Pydantic
- Respuesta vacia

**Endpoints sin paginacion (`test_orders.py`, `test_staff.py`, `test_routes.py`, `test_marketing.py`)**:
- Respuesta exitosa parsed
- Modo `raw=True`
- Respuesta vacia

**Reporte (`test_sales.py`)**:
- `export_sales_report`: flujo completo (POST -> pcArchivo -> GET bytes)
- Error en POST, campo pcArchivo faltante

## Integration Tests

**Ubicacion**: `tests/integration/test_api_real.py`

**Marcador**: `@pytest.mark.integration`

**Skip automatico**: si no existen las variables de entorno requeridas.

**Ejecucion**:
```bash
# Solo unit tests (default)
pytest tests/ -m "not integration"

# Solo integration
pytest tests/ -m integration

# Todos
pytest tests/
```

**Cobertura**: un test por endpoint que valida retorno de lista no vacia del tipo correcto.

## Dependencias

- `pytest>=7.0.0` (ya en pyproject.toml [dev])
- `requests-mock>=1.11.0` (ya en pyproject.toml [dev])
- `pytest-cov>=4.0.0` (ya en pyproject.toml [dev])

## Enfoque de mocking

Se mockea al nivel de `requests.get`/`requests.post` (no al nivel de `_get`) para testear el flujo completo: autenticacion, parsing de JSON, paginacion y manejo de errores.
