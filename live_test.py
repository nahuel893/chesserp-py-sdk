# Local Imports
from src.client import ChessClient
from src.exceptions import AuthError, ApiError
from src.logger import setup_logger, get_logger
from datetime import date, datetime, timedelta
import csv
import os

# Configurar logger globalmente al inicio (capturará logs de src.client también)
logger = setup_logger(log_file="live_test.log")

# Directorio de salida para archivos
OUTPUT_DIR = "data/out"

class Testing:
    """
    Clase de pruebas para validar todos los modelos de datos de ChessERP API.
    Ejecuta pruebas contra la API real y exporta resultados a CSV.
    """

    def __init__(self, instance: str = 'b'):
        """
        Inicializa la clase de pruebas.

        Args:
            instance: Instancia de ChessERP a usar ('b' o 's')
        """
        logger.info(f'{"":=^60}')
        logger.info(f'{"INICIANDO TESTING CLASS":^60}')
        logger.info(f'{"":=^60}')

        # Crear directorio de salida si no existe
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        logger.debug(f"Directorio de salida: {OUTPUT_DIR}")

        try:
            logger.info(f"Instanciando ChessClient (instance={instance})...")
            self.client = ChessClient(instance=instance)
            logger.info("Cliente instanciado correctamente")
        except Exception as error:
            logger.error(f"Error instanciando el cliente de ChessERP: {error}")
            raise

    def _to_csv(self, data, filename: str = "output.csv"):
        """
        Exporta datos a CSV.

        Args:
            data: Lista de diccionarios o lista de objetos Pydantic
            filename: Nombre del archivo CSV de salida
        """
        if not data:
            logger.warning("No hay datos para exportar")
            return False

        # Convertir objetos Pydantic a diccionarios si es necesario
        if hasattr(data[0], 'model_dump'):
            # Pydantic v2
            data = [item.model_dump() for item in data]
        elif hasattr(data[0], 'dict'):
            # Pydantic v1
            data = [item.dict() for item in data]

        # Obtener las cabeceras del primer elemento
        headers = data[0].keys()

        filepath = os.path.join(OUTPUT_DIR, filename) if not filename.startswith(OUTPUT_DIR) else filename

        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Datos exportados a: {filepath} ({len(data)} registros)")
        return True

    # ═══════════════════════════════════════════════════════════════
    # FUNCIONES DE APLANADO (Denormalización de estructuras anidadas)
    # ═══════════════════════════════════════════════════════════════

    def _flatten_marketing(self, data) -> list:
        """
        Aplana JerarquiaMkt → Canal → Subcanal.
        Una fila por cada combinación Segmento/Canal/Subcanal.
        """
        flat = []
        for segmento in data:
            seg_base = {
                'id_segmento_mkt': segmento.id_segmento_mkt,
                'des_segmento_mkt': segmento.des_segmento_mkt,
                'segmento_compania': segmento.compania,
            }
            if not segmento.canales_mkt:
                flat.append({**seg_base, 'id_canal_mkt': None, 'des_canal_mkt': None,
                            'canal_compania': None, 'id_subcanal_mkt': None,
                            'des_subcanal_mkt': None, 'subcanal_compania': None})
                continue
            for canal in segmento.canales_mkt:
                canal_base = {
                    **seg_base,
                    'id_canal_mkt': canal.id_canal_mkt,
                    'des_canal_mkt': canal.des_canal_mkt,
                    'canal_compania': canal.compania,
                }
                if not canal.subcanales_mkt:
                    flat.append({**canal_base, 'id_subcanal_mkt': None,
                                'des_subcanal_mkt': None, 'subcanal_compania': None})
                    continue
                for subcanal in canal.subcanales_mkt:
                    flat.append({
                        **canal_base,
                        'id_subcanal_mkt': subcanal.id_subcanal_mkt,
                        'des_subcanal_mkt': subcanal.des_subcanal_mkt,
                        'subcanal_compania': subcanal.compania,
                    })
        return flat

    def _flatten_routes(self, data) -> list:
        """
        Aplana RutaVenta → ClienteRuta.
        Una fila por cada combinación Ruta/Cliente.
        """
        flat = []
        for ruta in data:
            ruta_base = {
                'id_sucursal': ruta.id_sucursal,
                'des_sucursal': ruta.des_sucursal,
                'id_fuerza_ventas': ruta.id_fuerza_ventas,
                'des_fuerza_ventas': ruta.des_fuerza_ventas,
                'id_modo_atencion': ruta.id_modo_atencion,
                'des_modo_atencion': ruta.des_modo_atencion,
                'id_ruta': ruta.id_ruta,
                'des_ruta': ruta.des_ruta,
                'fecha_desde': ruta.fecha_desde,
                'fecha_hasta': ruta.fecha_hasta,
                'anulado': ruta.anulado,
                'id_personal': ruta.id_personal,
                'des_personal': ruta.des_personal,
                'periodicidad_visita': ruta.periodicidad_visita,
                'semana_visita': ruta.semana_visita,
                'dias_visita': ruta.dias_visita,
                'periodicidad_entrega': ruta.periodicidad_entrega,
                'semana_entrega': ruta.semana_entrega,
                'dias_entrega': ruta.dias_entrega,
            }
            if not ruta.cliente_rutas:
                flat.append({**ruta_base, 'cli_id_cliente': None, 'cli_razon_social': None,
                            'cli_intercalacion_visita': None, 'cli_intercalacion_entrega': None})
                continue
            for cli in ruta.cliente_rutas:
                flat.append({
                    **ruta_base,
                    'cli_id_cliente': cli.id_cliente,
                    'cli_razon_social': cli.razon_social,
                    'cli_intercalacion_visita': cli.intercalacion_visita,
                    'cli_intercalacion_entrega': cli.intercalacion_entrega,
                    'cli_fecha_desde': cli.fecha_desde,
                    'cli_fecha_hasta': cli.fecha_hasta,
                })
        return flat

    def _flatten_clients(self, data) -> list:
        """
        Aplana Cliente → ClienteAlias → CliFuerza.
        Una fila por cada combinación Cliente/Alias/Fuerza.
        """
        flat = []
        for cliente in data:
            cli_base = {
                'id_sucursal': cliente.id_sucursal,
                'des_sucursal': cliente.des_sucursal,
                'id_cliente': cliente.id_cliente,
                'fecha_alta': cliente.fecha_alta,
                'anulado': cliente.anulado,
                'id_forma_pago': cliente.id_forma_pago,
                'des_forma_pago': cliente.des_forma_pago,
                'id_lista_precio': cliente.id_lista_precio,
                'des_lista_precio': cliente.des_lista_precio,
                'calle': cliente.calle,
                'des_localidad': cliente.des_localidad,
                'des_provincia': cliente.des_provincia,
                'telefono_movil': cliente.telefono_movil,
                'email': cliente.email,
                'des_canal_mkt': cliente.des_canal_mkt,
                'des_subcanal_mkt': cliente.des_subcanal_mkt,
            }
            if not cliente.cliente_alias:
                flat.append({**cli_base, 'alias_id_alias': None, 'alias_razon_social': None,
                            'alias_identificador': None, 'fuerza_id_fuerza_ventas': None,
                            'fuerza_des_fuerza_venta': None, 'fuerza_id_ruta': None})
                continue
            for alias in cliente.cliente_alias:
                alias_base = {
                    **cli_base,
                    'alias_id_alias': alias.id_alias,
                    'alias_razon_social': alias.razon_social,
                    'alias_identificador': alias.identificador,
                    'alias_tipo_contribuyente': alias.des_tipo_contribuyente,
                }
                if not alias.clifuerza:
                    flat.append({**alias_base, 'fuerza_id_fuerza_ventas': None,
                                'fuerza_des_fuerza_venta': None, 'fuerza_id_ruta': None})
                    continue
                for fuerza in alias.clifuerza:
                    flat.append({
                        **alias_base,
                        'fuerza_id_fuerza_ventas': fuerza.id_fuerza_ventas,
                        'fuerza_des_fuerza_venta': fuerza.des_fuerza_venta,
                        'fuerza_id_modo_atencion': fuerza.id_modo_atencion,
                        'fuerza_id_ruta': fuerza.id_ruta,
                        'fuerza_anulado': fuerza.anulado,
                    })
        return flat

    def _flatten_orders(self, data) -> list:
        """
        Aplana Pedido → LineaPedido.
        Una fila por cada combinación Pedido/Línea.
        """
        flat = []
        for pedido in data:
            ped_base = {
                'id_pedido': pedido.id_pedido,
                'origen': pedido.origen,
                'id_empresa': pedido.id_empresa,
                'id_sucursal': pedido.id_sucursal,
                'id_cliente': pedido.id_cliente,
                'id_vendedor': pedido.id_vendedor,
                'fecha_entrega': pedido.fecha_entrega,
                'id_forma_pago': pedido.id_forma_pago,
                'id_deposito': pedido.id_deposito,
            }
            if not pedido.lineas:
                flat.append({**ped_base, 'linea_id_articulo': None, 'linea_cant_bultos': None,
                            'linea_cant_unidades': None, 'linea_precio_unitario': None})
                continue
            for linea in pedido.lineas:
                flat.append({
                    **ped_base,
                    'linea_id_linea': linea.id_linea_detalle,
                    'linea_id_articulo': linea.id_articulo,
                    'linea_cant_bultos': linea.cant_bultos,
                    'linea_cant_unidades': linea.cant_unidades,
                    'linea_peso_kilos': linea.peso_kilos,
                    'linea_precio_unitario': linea.precio_unitario,
                    'linea_bonificacion': linea.bonificacion,
                })
        return flat

    def _flatten_sales(self, data) -> list:
        """
        Aplana Sale → SaleLine.
        Una fila por cada combinación Venta/Línea.
        """
        flat = []
        for venta in data:
            venta_base = {
                'id_empresa': venta.id_empresa,
                'ds_empresa': venta.ds_empresa,
                'id_documento': venta.id_documento,
                'ds_documento': venta.ds_documento,
                'letra': venta.letra,
                'serie': venta.serie,
                'nro_doc': venta.nro_doc,
                'fecha_comprobante': venta.fecha_comprobante,
                'id_sucursal': venta.id_sucursal,
                'ds_sucursal': venta.ds_sucursal,
                'id_cliente': venta.id_cliente,
                'nombre_cliente': venta.nombre_cliente,
                'id_vendedor': venta.id_vendedor,
                'ds_vendedor': venta.ds_vendedor,
                'subtotal_neto': venta.subtotal_neto,
                'subtotal_final': venta.subtotal_final,
            }
            if not venta.lines:
                flat.append({**venta_base, 'linea_id_articulo': None, 'linea_ds_articulo': None,
                            'linea_cantidad': None, 'linea_precio_neto': None})
                continue
            for linea in venta.lines:
                flat.append({
                    **venta_base,
                    'linea_id_linea': linea.id_linea,
                    'linea_id_articulo': linea.id_articulo,
                    'linea_ds_articulo': linea.ds_articulo,
                    'linea_cantidades_total': linea.cantidades_total,
                    'linea_precio_bruto': linea.precio_unitario_bruto,
                    'linea_precio_neto': linea.precio_unitario_neto,
                    'linea_bonificacion': linea.bonificacion,
                    'linea_subtotal_neto': linea.subtotal_neto,
                    'linea_subtotal_final': linea.subtotal_final,
                })
        return flat

    def _flatten_articles(self, data) -> list:
        """
        Aplana Articulo → Agrupacion → RelacionEnvase.
        Una fila por cada combinación Artículo/Agrupación/Envase.
        """
        flat = []
        for art in data:
            art_base = {
                'id_articulo': art.id_articulo,
                'des_articulo': art.des_articulo,
                'unidades_bulto': art.unidades_bulto,
                'anulado': art.anulado,
                'fecha_alta': art.fecha_alta,
                'pesable': art.pesable,
                'es_combo': art.es_combo,
                'cod_barra_bulto': art.cod_barra_bulto,
                'cod_barra_unidad': art.cod_barra_unidad,
                'lleva_frescura': art.lleva_frescura,
            }
            if not art.agrupaciones:
                flat.append({**art_base, 'agrup_id_forma': None, 'agrup_des_forma': None,
                            'agrup_id_agrupacion': None, 'agrup_des_agrupacion': None,
                            'env_id_retornable': None, 'env_des_retornable': None})
                continue
            for agrup in art.agrupaciones:
                agrup_base = {
                    **art_base,
                    'agrup_id_forma': agrup.id_forma_agrupar,
                    'agrup_des_forma': agrup.des_forma_agrupar,
                    'agrup_id_agrupacion': agrup.id_agrupacion,
                    'agrup_des_agrupacion': agrup.des_agrupacion,
                }
                if not agrup.relavacio:
                    flat.append({**agrup_base, 'env_id_retornable': None,
                                'env_des_retornable': None, 'env_cantidad': None})
                    continue
                for env in agrup.relavacio:
                    flat.append({
                        **agrup_base,
                        'env_id_retornable': env.id_art_retornable,
                        'env_des_retornable': env.des_art_retornable,
                        'env_cantidad': env.cantidad_relacion,
                    })
        return flat

    def _test_wrapper(self, test_name: str, test_func):
        """
        Wrapper para ejecutar tests con manejo de errores y logging.

        Args:
            test_name: Nombre del test para logging
            test_func: Función de test a ejecutar
        """
        logger.info(f'{"":─^60}')
        logger.info(f"TEST: {test_name}")
        logger.info(f'{"":─^60}')

        start_time = datetime.now()
        try:
            result = test_func()
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"✓ {test_name} completado en {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = (datetime.now() - start_time).total_seconds()
            logger.error(f"✗ {test_name} falló después de {elapsed:.2f}s: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════
    # TESTS DE MODELOS
    # ═══════════════════════════════════════════════════════════════

    def stock(self):
        """Test del modelo StockFisico."""
        def _test():
            logger.info("Obteniendo stock físico del depósito 1...")
            data = self.client.get_stock(
                id_deposito=1,
                fecha="07-12-2025"
            )
            logger.info(f"Registros obtenidos: {len(data)}")

            if data:
                logger.debug(f"Primer registro: {data[0]}")
                self._to_csv(data, 'test_stock.csv')
            return data

        return self._test_wrapper("Stock (StockFisico)", _test)

    def sales(self):
        """Test del modelo Sale (Ventas)."""
        def _test():
            # Usar fechas del mes anterior para tener datos
            # fecha_hasta = date.today()
            # fecha_desde = fecha_hasta - timedelta(days=2)

            fecha_hasta = date(2025, 12, 3)
            fecha_desde = date(2025, 12, 1)


            logger.info(f"Obteniendo ventas desde {fecha_desde} hasta {fecha_hasta}...")
            data = self.client.get_sales(
                fecha_desde=fecha_desde.strftime("%Y-%m-%d"),
                fecha_hasta=fecha_hasta.strftime("%Y-%m-%d"),
                detallado=True,
                empresas="1",
            )
            logger.info(f"Ventas obtenidas: {len(data)}")

            if data:
                logger.debug(f"Primera venta: {data[0]}")
                # Aplanar Venta → Líneas
                #flat_data = self._flatten_sales(data)
                flat_data = data
                logger.info(f"Registros aplanados (venta+líneas): {len(flat_data)}")
                self._to_csv(flat_data, 'test_sales.csv')
            return data

        return self._test_wrapper("Sales (Ventas)", _test)

    def articles(self):
        """Test del modelo Articulo."""
        def _test():
            logger.info("Obteniendo catálogo de artículos...")
            data = self.client.get_articles(anulado=False)
            logger.info(f"Artículos obtenidos: {len(data)}")

            if data:
                logger.debug(f"Primer artículo: {data[0]}")
                # Aplanar Artículo → Agrupaciones → Envases
                flat_data = self._flatten_articles(data)
                logger.info(f"Registros aplanados (art+agrup+env): {len(flat_data)}")
                self._to_csv(flat_data, 'test_articles.csv')
            return data

        return self._test_wrapper("Articles (Artículos)", _test)

    def routes(self):
        """Test del modelo RutaVenta."""
        def _test():
            logger.info("Obteniendo rutas de venta...")
            data = self.client.get_routes(anulado=False)
            logger.info(f"Rutas obtenidas: {len(data)}")

            if data:
                logger.debug(f"Primera ruta: {data[0]}")
                # Aplanar Ruta → Clientes
                flat_data = self._flatten_routes(data)
                logger.info(f"Registros aplanados (ruta+clientes): {len(flat_data)}")
                self._to_csv(flat_data, 'test_routes.csv')
            return data

        return self._test_wrapper("Routes (RutaVenta)", _test)

    def orders(self):
        """Test del modelo Pedido."""
        def _test():
            # Usar fechas recientes para encontrar pedidos
            fecha_hoy = date.today().strftime("%Y-%m-%d")
            fecha_ayer = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")

            logger.info(f"Obteniendo pedidos con fecha de entrega {fecha_ayer} a {fecha_hoy}...")
            data = self.client.get_orders(
                fecha_entrega=fecha_hoy,
                facturado=False
            )
            logger.info(f"Pedidos obtenidos: {len(data)}")

            if data:
                logger.debug(f"Primer pedido: {data[0]}")
                # Aplanar Pedido → Líneas
                flat_data = self._flatten_orders(data)
                logger.info(f"Registros aplanados (pedido+líneas): {len(flat_data)}")
                self._to_csv(flat_data, 'test_orders.csv')
            return data

        return self._test_wrapper("Orders (Pedidos)", _test)

    def clients(self):
        """Test del modelo Cliente."""
        def _test():
            logger.info("Obteniendo clientes...")
            data = self.client.get_customers()
            logger.info(f"Clientes obtenidos: {len(data)}")

            if data:
                logger.debug(f"Primer cliente: {data[0]}")
                # Aplanar Cliente → Alias → Fuerza
                flat_data = self._flatten_clients(data)
                logger.info(f"Registros aplanados (cliente+alias+fuerza): {len(flat_data)}")
                self._to_csv(flat_data, 'test_clients.csv')
            return data

        return self._test_wrapper("Clients (Clientes)", _test)

    def staff(self):
        """Test del modelo PersonalComercial."""
        def _test():
            logger.info("Obteniendo personal comercial...")
            data = self.client.get_staff()
            logger.info(f"Personal obtenido: {len(data)}")

            if data:
                logger.debug(f"Primer personal: {data[0]}")
                self._to_csv(data, 'test_staff.csv')
            return data

        return self._test_wrapper("Staff (PersonalComercial)", _test)

    def mkt(self):
        """Test del modelo JerarquiaMkt (Marketing)."""
        def _test():
            logger.info("Obteniendo jerarquía de marketing...")

            # Primero ver el raw para debug
            raw_data = self.client.get_marketing_raw()
            logger.debug(f"Raw data type: {type(raw_data)}")
            logger.debug(f"Raw data preview: {str(raw_data)[:500]}")

            data = self.client.get_marketing()
            logger.info(f"Segmentos de marketing obtenidos: {len(data)}")

            if data:
                logger.debug(f"Primer segmento: {data[0]}")
                # Aplanar Segmento → Canal → Subcanal
                flat_data = self._flatten_marketing(data)
                logger.info(f"Registros aplanados (seg+canal+subcanal): {len(flat_data)}")
                self._to_csv(flat_data, 'test_marketing.csv')
            else:
                logger.warning("No se obtuvieron datos de marketing")
            return data

        return self._test_wrapper("Marketing (JerarquiaMkt)", _test)

    # ═══════════════════════════════════════════════════════════════
    # EJECUCIÓN DE TESTS
    # ═══════════════════════════════════════════════════════════════

    def run_all(self):
        """
        Ejecuta todas las pruebas de modelos disponibles.

        Returns:
            dict: Resultados de cada test (nombre -> datos o None si falló)
        """
        logger.info(f'{"":═^60}')
        logger.info(f'{"EJECUTANDO TODOS LOS TESTS":^60}')
        logger.info(f'{"":═^60}')

        start_time = datetime.now()

        results = {
            'stock': self.stock(),
            'sales': self.sales(),
            'articles': self.articles(),
            'routes': self.routes(),
            'orders': self.orders(),
            'clients': self.clients(),
            'staff': self.staff(),
            'mkt': self.mkt(),
        }

        # Resumen
        elapsed = (datetime.now() - start_time).total_seconds()
        passed = sum(1 for v in results.values() if v is not None)
        failed = sum(1 for v in results.values() if v is None)

        logger.info(f'{"":═^60}')
        logger.info(f'{"RESUMEN DE TESTS":^60}')
        logger.info(f'{"":═^60}')
        logger.info(f"Total ejecutados: {len(results)}")
        logger.info(f"Exitosos: {passed}")
        logger.info(f"Fallidos: {failed}")
        logger.info(f"Tiempo total: {elapsed:.2f}s")
        logger.info(f'{"":═^60}')

        return results

    def run_quick(self):
        """
        Ejecuta un subconjunto rápido de tests (stock, articles, routes, staff).
        Útil para validación rápida de conectividad.
        """
        logger.info(f'{"EJECUTANDO TESTS RÁPIDOS":^60}')

        results = {
            'stock': self.stock(),
            'articles': self.articles(),
            'routes': self.routes(),
            'staff': self.staff(),
        }

        return results

def main():
    """
    Punto de entrada principal para ejecutar las pruebas en vivo.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Pruebas en vivo de ChessERP API')
    parser.add_argument(
        '--instance', '-i',
        type=str,
        default='b',
        choices=['b', 's'],
        help='Instancia de ChessERP a usar (default: b)'
    )
    parser.add_argument(
        '--test', '-t',
        type=str,
        default='all',
        choices=['all', 'quick', 'stock', 'sales', 'articles', 'routes', 'orders', 'clients', 'staff', 'mkt'],
        help='Test específico a ejecutar (default: all)'
    )

    args = parser.parse_args()

    logger.info(f'{"":═^60}')
    logger.info(f'{"LIVE TEST - ChessERP API":^60}')
    logger.info(f'{"":═^60}')
    logger.info(f"Instancia: {args.instance}")
    logger.info(f"Test: {args.test}")

    # Inicializar clase de pruebas
    tester = Testing(instance=args.instance)

    # Ejecutar test(s) seleccionado(s)
    if args.test == 'all':
        results = tester.run_all()
    elif args.test == 'quick':
        results = tester.run_quick()
    else:
        # Ejecutar test individual
        test_method = getattr(tester, args.test, None)
        if test_method:
            results = {args.test: test_method()}
        else:
            logger.error(f"Test '{args.test}' no encontrado")
            return

    logger.info("Pruebas finalizadas.")


if __name__ == '__main__':
    main()


