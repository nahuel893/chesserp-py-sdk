# ChessERP API Python Library

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Libreria Python robusta y reutilizable para interactuar con la API de ChessERP. Abstrae la complejidad de la autenticacion, manejo de sesiones y paginacion automatica, permitiendo a los desarrolladores trabajar con objetos Python tipados y validados.

## Caracteristicas Principales

- **Cliente Unificado**: Interfaz simple para acceder a todos los endpoints de ChessERP
- **Validacion Automatica**: Modelos Pydantic v2 para garantizar integridad de datos
- **Manejo de Sesiones**: Autenticacion automatica con reintentos en caso de expiracion (401)
- **Paginacion Transparente**: Obtencion automatica de todos los lotes de datos
- **Tipado Estatico**: Soporte completo para autocompletado en IDEs
- **Metodos Raw & Parsed**: Acceso a datos crudos (JSON) o validados (Pydantic)
- **Logging Integrado**: Trazabilidad completa de operaciones (file + console)

## Endpoints Soportados

| Recurso | Metodos | Paginado |
|---------|---------|----------|
| **Ventas** | `get_sales()`, `get_sales_raw()`, `export_sales_report()` | Si |
| **Articulos** | `get_articles()`, `get_articles_raw()` | Si |
| **Stock** | `get_stock()`, `get_stock_raw()` | No |
| **Clientes** | `get_customers()`, `get_customers_raw()` | Si |
| **Pedidos** | `get_orders()`, `get_orders_raw()` | No |
| **Personal Comercial** | `get_staff()`, `get_staff_raw()` | No |
| **Rutas de Venta** | `get_routes()`, `get_routes_raw()` | No |
| **Marketing** | `get_marketing()`, `get_marketing_raw()` | No |

## Instalacion

### Clonar el Repositorio

```bash
git clone https://github.com/tuusuario/chesserp-api.git
cd chesserp-api
```

### Instalar

```bash
pip install -e .          # Modo desarrollo (editable)
pip install -e ".[dev]"   # Con dependencias de testing
```

### Configuracion

Copia el archivo de ejemplo y completa con tus credenciales:

```bash
cp .env.example .env
```

El `.env` usa un patron de prefijos por empresa:

```env
# Empresa 1
EMPRESA1_API_URL=http://tu-servidor:puerto/
EMPRESA1_USERNAME=tu_usuario
EMPRESA1_PASSWORD=tu_password

# Empresa 2 (opcional)
EMPRESA2_API_URL=http://otro-servidor:puerto/
EMPRESA2_USERNAME=tu_usuario
EMPRESA2_PASSWORD=tu_password
```

## Uso Rapido

### Inicializacion del Cliente

```python
from chesserp import ChessClient

# Desde variables de entorno con prefijo
client = ChessClient.from_env(prefix="EMPRESA1_")

# O directo con credenciales
client = ChessClient(
    api_url="http://tu-servidor:puerto",
    username="usuario",
    password="clave"
)
```

### Consultar Ventas

```python
ventas = client.get_sales(
    fecha_desde="2025-01-01",
    fecha_hasta="2025-01-31",
    detallado=True
)

for venta in ventas:
    print(f"{venta.letra} {venta.serie}-{venta.nro_doc}")
    print(f"Cliente: {venta.nombre_cliente}")
    print(f"Total: ${venta.imp_total}")

    for linea in venta.lines:
        print(f"  - {linea.ds_articulo} x{linea.cantidad_solicitada}")
```

### Consultar Stock

```python
stock = client.get_stock(id_deposito=1)

for item in stock:
    print(f"{item.ds_articulo}: {item.cant_bultos} bultos")
```

### Exportar Reporte de Ventas a Excel

```python
excel_bytes = client.export_sales_report(
    fecha_desde="2025-01-01",
    fecha_hasta="2025-01-31",
    empresas="1",
    tiposdoc="FCVTA,DVVTA"
)

with open("reporte_ventas.xlsx", "wb") as f:
    f.write(excel_bytes)
```

### Acceso a Datos Raw (JSON)

Para pipelines ETL o cuando se necesita el JSON sin validar:

```python
raw_data = client.get_sales_raw(
    fecha_desde="2025-01-01",
    fecha_hasta="2025-01-31",
    nro_lote=1
)
```

Todos los metodos `get_*()` aceptan `raw=True` para retornar listas de dicts en vez de objetos Pydantic.

### Mas Ejemplos

```python
# Clientes
clientes = client.get_customers(anulado=False)

# Pedidos
pedidos = client.get_orders(fecha_pedido="2025-01-15")

# Personal comercial
personal = client.get_staff(sucursal=1)

# Rutas de venta
rutas = client.get_routes(sucursal=1, fuerza_venta=10)

# Jerarquia de marketing
segmentos = client.get_marketing(cod_scan=0)
```

## Manejo de Errores

```python
from chesserp import ChessClient, AuthError, ApiError, ChessError

try:
    ventas = client.get_sales("2025-01-01", "2025-01-31")
except AuthError as e:
    print(f"Error de autenticacion: {e}")
except ApiError as e:
    print(f"Error en la API: {e.status_code} - {e.message}")
except ChessError as e:
    print(f"Error general: {e}")
```

## Estructura del Proyecto

```
chesserp-api/
├── chesserp/                    # Paquete principal
│   ├── __init__.py              # Exports: ChessClient, excepciones
│   ├── client.py                # Cliente principal (auth, paginacion, endpoints)
│   ├── exceptions.py            # ChessError, AuthError, ApiError
│   ├── logger.py                # Logger centralizado (file + console)
│   ├── sales.py                 # Servicio de ventas
│   ├── stock.py                 # Servicio de stock (pandas)
│   ├── config/
│   │   └── settings.py          # PathConfig, LogLevel, Settings
│   └── models/                  # Modelos Pydantic v2
│       ├── __init__.py          # Re-exports de todos los modelos
│       ├── sales.py             # Sale
│       ├── inventory.py         # Articulo, StockFisico
│       ├── clients.py           # Cliente
│       ├── orders.py            # Pedido, LineaPedido
│       ├── routes.py            # RutaVenta, ClienteRuta
│       ├── staff.py             # PersonalComercial
│       └── marketing.py         # JerarquiaMkt, CanalMkt, SubCanalMkt
├── live_test.py                 # Tests contra API real
├── usage_example.py             # Menu interactivo de pruebas
├── main.py                      # Script batch de exportacion
├── pyproject.toml               # Config de proyecto y dependencias
├── requirements.txt             # Dependencias
└── .env.example                 # Plantilla de variables de entorno
```

## Scripts de Prueba

### Testing contra API real

```bash
python live_test.py --prefix EMPRESA1_ --test all
python live_test.py --prefix EMPRESA1_ --test sales
python live_test.py --test quick
```

### Menu interactivo

```bash
python usage_example.py
```

## Dependencias

| Paquete | Uso |
|---------|-----|
| `requests` | HTTP client |
| `python-dotenv` | Variables de entorno desde .env |
| `pydantic` | Validacion de modelos |
| `pandas` | Manipulacion de datos |
| `openpyxl` | Export Excel |
| `numpy` | Operaciones numericas |

## Roadmap

- [ ] Empaquetado PyPI (`pip install chesserp-api`)
- [ ] Soporte para operaciones POST/PUT (crear pedidos, actualizar stock)
- [ ] Cache de resultados con TTL configurable
- [ ] Async support (httpx)
- [ ] CLI para operaciones comunes

## Licencia

Este proyecto esta bajo la licencia MIT. Ver archivo `LICENSE` para mas detalles.

---

**Python 3.10+ | Pydantic v2 | Requests**
