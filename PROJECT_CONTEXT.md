# Contexto Tecnico: ChessERP API Python Library

> Este archivo complementa `CLAUDE.md` con detalles tecnicos profundos sobre modelos, API y decisiones de diseno.

## 1. Modelos Pydantic - Detalle

### Tabla resumen

| Archivo | Clases | Campos aprox. | Anidamiento | Notas |
|---------|--------|---------------|-------------|-------|
| `sales.py` | `Sale` | 150+ | 1 nivel (lines) | Typos de API (`fechaComprobate`), tipos mixtos `Union[int, str]` |
| `inventory.py` | `Articulo`, `StockFisico`, `AgrupacionArticulo`, `RelacionEnvase` | 100+ | 2 niveles | Agrupaciones con envases anidados |
| `clients.py` | `Cliente`, `ClienteAlias`, `ClienteFuerza` | 160+ | 2 niveles | Coordenadas geo, fuerzas de venta multiples |
| `orders.py` | `Pedido`, `LineaPedido` | 30+ | 1 nivel | IDs tipo string (`NXB-15-2516938`) |
| `routes.py` | `RutaVenta`, `ClienteRuta` | 20+ | 2 niveles | Validador custom `empty_str_to_none` |
| `staff.py` | `PersonalComercial` | 15+ | Plano | Jerarquia (superior) |
| `marketing.py` | `JerarquiaMkt`, `CanalMkt`, `SubCanalMkt` | 10+ | 3 niveles | Estructura recursiva Segmento>Canal>Subcanal |

### Patrones comunes en los modelos
- **`Field(alias=...)`**: Todos usan alias para mapear campos del JSON de la API.
- **`Optional[...]`**: La mayoria de campos son Optional porque la API es inconsistente.
- **`Union[int, str]`**: Varios campos de la API devuelven a veces int, a veces string.
- **Validadores custom**: `routes.py` tiene `OptionalInt` con `BeforeValidator` para convertir strings vacios a None.

## 2. Estructura de respuestas de la API ChessERP

### Endpoints con paginacion (lotes)
Los endpoints que manejan lotes retornan un campo con formato:
```
"Numero de lote obtenido: 1/70. Cantidad de comprobantes totales: 69041"
```
El cliente parsea esto con regex `r'(\d+)/(\d+)'` para iterar todos los lotes.

**Ventas:**
```json
{
    "dsReporteComprobantesApi": {"VentasResumen": [...]},
    "cantComprobantesVentas": "Numero de lote obtenido: 1/70. ..."
}
```

**Articulos:**
```json
{
    "Articulos": {"eArticulos": [...]},
    "cantArticulos": "Numero de lote obtenido: 1/22. ..."
}
```

**Clientes:**
```json
{
    "Clientes": {"eClientes": [...]},
    "cantClientes": "Numero de lote obtenido: 1/15. ..."
}
```

### Endpoints sin paginacion

**Stock:** `{"dsStockFisicoApi": {"dsStock": [...]}}`
**Pedidos:** `{"pedidos": [...]}`
**Personal:** `{"PersonalComercial": {"ePersCom": [...]}}`
**Rutas:** `{"RutasVenta": {"eRutasVenta": [...]}}`
**Marketing:** `{"SubcanalesMkt": {"SegmentosMkt": [...]}}`

## 3. Autenticacion

- **Endpoint**: `POST /web/api/chess/v1/auth/login`
- **Payload**: `{"usuario": "...", "password": "..."}`
- **Respuesta**: JSON con campo `sessionId`
- **Uso**: Se envia como header `Cookie: <sessionId>` en cada request
- **Retry**: Si un GET retorna 401, se reintenta login automaticamente

## 4. Capa de Servicios

### StockData (`chesserp/stock.py`) - Funcional
Servicio completo que:
- Obtiene stock via `ChessClient`
- Carga datos auxiliares (depositos, articulos descartables, categorias) desde CSV
- Merge con pandas (depositos, categorias)
- Filtrado de articulos "bloat"
- Pivot table por sucursal
- Export a Excel/CSV

### SalesData (`chesserp/sales.py`) - Incompleto
Solo tiene un listado de columnas hardcodeado y un metodo vacio. `live_test.py` tiene la logica de aplanado que deberia migrar aqui.

## 5. Dependencias del Proyecto

### Runtime
| Paquete | Version | Uso |
|---------|---------|-----|
| `requests` | >=2.28.0 | HTTP client |
| `python-dotenv` | >=1.0.0 | Variables de entorno desde .env |
| `pandas` | >=2.0.0 | Manipulacion de datos (StockData) |
| `pydantic` | >=2.0.0 | Validacion de modelos |
| `openpyxl` | >=3.1.0 | Export Excel |
| `numpy` | >=1.24.0 | Operaciones numericas (StockData) |

### Dev
| Paquete | Version | Uso |
|---------|---------|-----|
| `pytest` | >=7.0.0 | Testing (sin tests actualmente) |
| `requests-mock` | >=1.11.0 | Mock HTTP para tests |
| `pytest-cov` | >=4.0.0 | Cobertura de codigo |

## 6. Historial de Migraciones Relevantes

| Commit | Descripcion |
|--------|-------------|
| `c4d4ec8` | Migracion a arquitectura limpia, elimina `src/endpoints.py` legacy |
| `2d598ef` | Renombra `src/` a `chesserp/` para empaquetado |
| `79ffc9f` | Limpieza de archivos viejos en `src/` |
| `6b93644` | Refactor multi-client. **Elimina tests unitarios** (`tests/conftest.py`, `tests/test_client.py`) |
| `e5a4f24` | Agrega `pyproject.toml` |
| `d2ade39` | Fix en `ApiError` call en client.py |

## 7. Notas sobre la API ChessERP
- La API tiene typos en nombres de campos (ej: `fechaComprobate` en vez de `fechaComprobante`).
- Los campos pueden cambiar de tipo entre requests (int vs string).
- Algunos endpoints devuelven listas vacias como `[]` en vez de objetos con listas vacias.
- El `sessionId` se envia como cookie, no como header Authorization.
- No hay documentacion OpenAPI/Swagger; la referencia es un HTML estatico.
