# ChessERP API Python Library

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Librería Python robusta y reutilizable para interactuar con la API de ChessERP. Abstrae la complejidad de la autenticación, manejo de sesiones y paginación automática, permitiendo a los desarrolladores trabajar con objetos Python tipados y validados.

## Características Principales

- **Cliente Unificado**: Interfaz simple para acceder a todos los endpoints de ChessERP
- **Validación Automática**: Modelos Pydantic para garantizar integridad de datos
- **Manejo de Sesiones**: Autenticación automática con reintentos en caso de expiración
- **Paginación Transparente**: Obtención automática de todos los lotes de datos
- **Tipado Estático**: Soporte completo para autocompletado en IDEs
- **Métodos Raw & Parsed**: Acceso a datos crudos (JSON) o validados (Pydantic)
- **Logging Integrado**: Trazabilidad completa de operaciones

## Endpoints Soportados

| Recurso | Descripción | Métodos |
|---------|-------------|---------|
| **Ventas** | Comprobantes de ventas (facturas, tickets) | `get_sales()`, `get_sales_raw()`, `export_sales_report()` |
| **Inventario** | Catálogo de artículos y stock físico | `get_articles()`, `get_stock()` |
| **Clientes** | Base de datos de clientes | `get_customers()` |
| **Pedidos** | Pedidos de venta | `get_orders()` |
| **Personal** | Personal comercial (vendedores) | `get_staff()` |
| **Rutas** | Rutas de venta | `get_routes()` |
| **Marketing** | Jerarquía de marketing (segmentos, canales) | `get_marketing()` |

## Instalación

### Clonar el Repositorio

```bash
git clone https://github.com/tuusuario/chesserp-api.git
cd chesserp-api
```

### Instalar Dependencias

```bash
pip install -r requirements.txt
```

### Configuración

Crea un archivo `.env` en la raíz del proyecto con tus credenciales:

```env
# Instancia B (Producción)
API_URL_B=http://tu-servidor:puerto
USERNAME_B=tu_usuario
PASSWORD_B=tu_contraseña

# Instancia S (Staging/Testing)
API_URL_S=http://tu-servidor-staging:puerto
USERNAME_S=tu_usuario_staging
PASSWORD_S=tu_contraseña_staging
```

## Uso Rápido

### Inicialización del Cliente

```python
from src.client import ChessClient

# Usar instancia configurada (default: 'b')
client = ChessClient(instance='b')

# O con configuración manual
from src.config.settings import Settings

settings = Settings(
    api_url_b="http://mi-servidor:8080",
    username_b="usuario",
    password_b="contraseña"
)
client = ChessClient(settings=settings, instance='b')
```

### Consultar Ventas

```python
# Obtener ventas validadas (Pydantic)
ventas = client.get_sales(
    fecha_desde="2025-01-01",
    fecha_hasta="2025-01-31",
    detallado=True  # Incluir líneas de detalle
)

for venta in ventas:
    print(f"{venta.letra} {venta.serie}-{venta.nro_doc}")
    print(f"Cliente: {venta.nombre_cliente}")
    print(f"Total: ${venta.imp_total}")

    # Acceder a líneas de detalle
    for linea in venta.lines:
        print(f"  - {linea.ds_articulo} x{linea.cantidad_solicitada}")
```

### Consultar Stock

```python
# Obtener stock físico de un depósito
stock = client.get_stock(
    id_deposito=1,
    fecha="01-01-2025"  # Opcional: cálculo histórico
)

for item in stock:
    print(f"{item.ds_articulo}: {item.cant_bultos} bultos")
```

### Exportar Reporte de Ventas

```python
# Generar y descargar reporte Excel
excel_bytes = client.export_sales_report(
    fecha_desde="2025-01-01",
    fecha_hasta="2025-01-31",
    empresas="1",
    tiposdoc="FCVTA,DVVTA"
)

# Guardar archivo
with open("reporte_ventas.xlsx", "wb") as f:
    f.write(excel_bytes)
```

### Acceso a Datos Raw (JSON)

Para pipelines ETL o arquitecturas medallion:

```python
# Obtener primer lote sin validación
raw_data = client.get_sales_raw(
    fecha_desde="2025-01-01",
    fecha_hasta="2025-01-31",
    nro_lote=1
)

# Estructura:
# {
#   "dsReporteComprobantesApi": {"VentasResumen": [...]},
#   "cantComprobantesVentas": "Numero de lote obtenido: 1/70. ..."
# }
```

## Ejemplos Completos

### Consultar Clientes por Sucursal

```python
clientes = client.get_customers(sucursal=1, anulado=False)

for cliente in clientes:
    print(f"ID: {cliente.id_cliente}")
    print(f"Razón Social: {cliente.razon_social}")
    print(f"Ubicación: {cliente.des_localidad}, {cliente.des_provincia}")
```

### Obtener Rutas de Venta

```python
rutas = client.get_routes(
    sucursal=1,
    fuerza_venta=10,
    anulado=False
)

for ruta in rutas:
    print(f"Ruta: {ruta.des_ruta}")
    print(f"Vendedor: {ruta.des_personal}")
```

### Jerarquía de Marketing

```python
segmentos = client.get_marketing(cod_scan=0)

for segmento in segmentos:
    print(f"Segmento: {segmento.des_segmento_mkt}")
    print(f"Código: {segmento.cod_segmento_mkt}")
```

## Estructura del Proyecto

```
chesserp-api/
├── src/
│   ├── client.py              # Cliente principal (ChessClient)
│   ├── logger.py              # Configuración de logging
│   ├── exceptions.py          # Excepciones personalizadas
│   ├── config/
│   │   └── settings.py        # Gestión de configuración (.env)
│   └── models/                # Modelos Pydantic
│       ├── sales.py           # Modelo de ventas
│       ├── inventory.py       # Modelos de artículos y stock
│       ├── clients.py         # Modelo de clientes
│       ├── orders.py          # Modelo de pedidos
│       ├── routes.py          # Modelo de rutas de venta
│       ├── staff.py           # Modelo de personal comercial
│       └── marketing.py       # Modelo de jerarquía marketing
├── tests/
│   ├── conftest.py           # Fixtures de pytest
│   └── test_client.py        # Tests unitarios
├── usage_example.py          # Script de ejemplo interactivo
├── live_test.py              # Tests contra API real
├── requirements.txt          # Dependencias del proyecto
├── CLAUDE.md                 # Contexto del proyecto
└── README.md                 # Este archivo
```

## Testing

### Ejecutar Tests Unitarios

```bash
# Todos los tests
pytest tests/

# Con cobertura
pytest tests/ --cov=src

# Tests específicos
pytest tests/test_client.py -v
```

### Script de Prueba Interactivo

```bash
python usage_example.py
```

Este script proporciona un menú interactivo para probar todos los endpoints disponibles.

## Modelos de Datos

Todos los modelos utilizan **Pydantic v2** para validación automática:

```python
from src.models.sales import Sale
from src.models.inventory import Articulo, StockFisico
from src.models.clients import Cliente
from src.models.orders import Pedido

# Los modelos incluyen:
# - Validación de tipos
# - Campos opcionales claramente definidos
# - Serialización JSON automática
# - Autocompletado en IDEs
```

## Manejo de Errores

La librería proporciona excepciones específicas:

```python
from src.exceptions import AuthError, ApiError, ChessError

try:
    ventas = client.get_sales("2025-01-01", "2025-01-31")
except AuthError as e:
    print(f"Error de autenticación: {e}")
except ApiError as e:
    print(f"Error en la API: {e.status_code} - {e.message}")
except ChessError as e:
    print(f"Error general: {e}")
```

## Logging

Configurar nivel de logging según necesidad:

```python
import logging
from src.logger import get_logger

# Para debug detallado
logging.basicConfig(level=logging.DEBUG)

# Para uso en producción
logging.basicConfig(level=logging.WARNING)
```

## Arquitectura

### Flujo de Ejecución

```
Usuario → ChessClient → Login (si es necesario) → GET Endpoint
                                                 ↓
                                            Parse JSON
                                                 ↓
                                         Validar con Pydantic
                                                 ↓
                                        Retornar Objetos
```

### Características Técnicas

- **Reintentos Automáticos**: Si una petición falla con 401, se reintenta el login automáticamente
- **Paginación Automática**: Los métodos `get_*()` (sin `_raw`) obtienen TODOS los lotes disponibles
- **Parseo Robusto**: Si un registro individual falla la validación, se loguea el error y se continúa con el resto
- **Configuración por Instancia**: Soporte para múltiples instancias de ChessERP (producción, staging, etc.)

## Roadmap

- [ ] Empaquetado PyPI (`pip install chesserp-api`)
- [ ] Soporte para operaciones POST/PUT (crear pedidos, actualizar stock)
- [ ] Caché de resultados con TTL configurable
- [ ] Async support (httpx)
- [ ] CLI para operaciones comunes
- [ ] Documentación Sphinx completa

## Contribución

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

## Soporte

Para reportar bugs o solicitar features, abre un issue en el repositorio de GitHub.

---

**Desarrollado con Python 3.8+ | Pydantic v2 | Requests**
