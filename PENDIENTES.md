# Pendientes - ChessERP API

> Ultima actualizacion: 2026-02-18

## Criticos (bloquean push limpio)

### P1. Crear archivos `__init__.py`
**Estado**: Pendiente
**Archivos**: `chesserp/__init__.py`, `chesserp/models/__init__.py`
**Detalle**: El paquete funciona por namespace packages implícitos de Python 3.3+, pero para un paquete distribuible es mejor practica tener `__init__.py` con exports explícitos. Sin ellos, `from chesserp import ChessClient` no funciona.
**Impacto**: Cualquier usuario que haga `pip install .` y trate de importar de forma limpia va a tener problemas.

### P2. Arreglar `chesserp/sales.py` - Error de sintaxis
**Estado**: Pendiente
**Archivo**: `chesserp/sales.py:80-83`
**Detalle**: El metodo `process_data_reports()` esta vacio (sin `pass` ni body), lo que causa SyntaxError al importar. Esto **rompe el import del modulo entero** si alguien intenta importar `chesserp.sales`.
**Solucion**: Agregar `pass` o eliminar el metodo hasta que se implemente.

### P3. Crear `.env.example`
**Estado**: Pendiente
**Detalle**: No existe archivo de ejemplo para las variables de entorno. Quien clone el repo no sabe que variables configurar. El `.env` real esta en `.gitignore` (correcto), pero falta la plantilla.

## Bugs

### B1. `live_test.py:158` - Logica invertida en `_flatten_routes`
**Estado**: Pendiente
**Detalle**: La condicion `if ruta.cliente_rutas:` (linea 158) deberia ser `if not ruta.cliente_rutas:`. Actualmente, cuando la ruta TIENE clientes, agrega un registro con Nones, y cuando NO tiene, intenta iterar (nunca se ejecuta el for).

### B2. `usage_example.py` - Metodo inexistente
**Estado**: Pendiente
**Archivo**: `usage_example.py` funcion `test_marketing()`
**Detalle**: Llama a `client.get_marketing_hierarchy()` que no existe. El metodo correcto es `client.get_marketing()`.

### B3. `main.py` - Variables de entorno legacy
**Estado**: Pendiente
**Archivo**: `main.py`
**Detalle**: Usa `os.getenv("API_URL_B")`, `os.getenv("USERNAME_B")`, etc. Pero el `.env` actual usa el patron con prefijo: `EMPRESA1_API_URL`, `EMPRESA1_USERNAME`, etc. El script `main.py` no va a encontrar las variables.
**Solucion**: Migrar a `ChessClient.from_env(prefix="EMPRESA2_")`.

## Mejoras de calidad

### M1. Restaurar tests unitarios (pytest)
**Estado**: Pendiente
**Detalle**: Los tests `tests/test_client.py` y `tests/conftest.py` fueron eliminados en commit `6b93644`. pytest esta configurado en `pyproject.toml` pero no tiene tests que ejecutar. La infra esta lista, faltan los tests.
**Prioridad**: Alta - sin tests no hay forma de validar cambios sin la API real.

### M2. Actualizar README.md
**Estado**: Pendiente
**Detalle**: El README tiene multiples errores:
- Referencia `src/` en vez de `chesserp/` (estructura de archivos, imports)
- Badge dice Python 3.8+ pero `pyproject.toml` requiere 3.10+
- Ejemplo de inicializacion usa `ChessClient(instance='b')` que no existe
- Ejemplo de Settings no coincide con la clase real
- Imports usan `from src.client` en vez de `from chesserp.client`

### M3. Limpiar `chesserp/sales.py`
**Estado**: Pendiente
**Detalle**: El archivo es un stub con columnas hardcodeadas y un `__main__` que referencia paths absolutos de Windows. La logica de aplanado de ventas esta en `live_test.py._flatten_sales()` y deberia migrar aqui como servicio.

### M4. Agregar `chesserp_api.egg-info/` a `.gitignore`
**Estado**: Pendiente
**Detalle**: El directorio `egg-info` aparece como untracked en git. Es un artefacto de `pip install -e .` y no deberia trackearse.

### M5. El `.gitignore` excluye `*.txt`
**Estado**: Pendiente
**Detalle**: La regla `*.txt` en `.gitignore` podria causar problemas si se agregan archivos `.txt` que si deben trackearse (como `requirements.txt`, que ya estaba tracked antes de agregar la regla). Considerar ser mas especifico (ej: `data/*.txt`).

## Roadmap (futuro)

- [ ] Empaquetado PyPI (`pip install chesserp-api`)
- [ ] Soporte para operaciones POST/PUT (crear pedidos, actualizar stock)
- [ ] Cache de resultados con TTL configurable
- [ ] Async support (httpx)
- [ ] CLI para operaciones comunes
- [ ] Documentacion Sphinx

## Temas discutidos en sesion

### Exposicion de endpoints de la API
**Fecha**: 2026-02-18
**Conclusion**: Los paths relativos de la API (`ventas/`, `clientes/`, etc.) estan hardcodeados en `client.py` y visibles en el historial de git. Se discutio que:
- No representan un riesgo real de seguridad: sin la URL base y credenciales son inutiles.
- Son parte de la documentacion publica de ChessERP.
- Limpiar el historial de git (filter-branch/BFG) no vale la pena para paths relativos.
- Opcionalmente se pueden mover a configuracion en el futuro, pero no es prioritario.
