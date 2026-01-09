# Local Imports
from chesserp.client import ChessClient
from chesserp.exceptions import AuthError, ApiError
from chesserp.logger import setup_logger, get_logger
from datetime import date, datetime, timedelta
from typing import Optional
from dotenv import load_dotenv
import calendar
import csv
import os

load_dotenv()

# Configurar logger globalmente al inicio
logger = setup_logger(log_file="live_test.log")

# Directorio de salida para archivos
OUTPUT_DIR = "data/out"


class Testing:
    """
    Clase de pruebas para validar todos los modelos de datos de ChessERP API.
    Ejecuta pruebas contra la API real y exporta resultados a CSV.
    """

    def __init__(self, client: Optional[ChessClient] = None, env_prefix: str = ""):
        """
        Inicializa la clase de pruebas.

        Args:
            client: Instancia de ChessClient (opcional, si no se pasa se crea desde env)
            env_prefix: Prefijo para variables de entorno (ej: "EMPRESA1_")
        """
        logger.info(f'{"":=^60}')
        logger.info(f'{"INICIANDO TESTING CLASS":^60}')
        logger.info(f'{"":=^60}')

        # Crear directorio de salida si no existe
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        logger.debug(f"Directorio de salida: {OUTPUT_DIR}")

        try:
            if client:
                self.client = client
                logger.info("Cliente recibido por parámetro")
            else:
                # Crear cliente desde variables de entorno
                logger.info(f"Creando ChessClient desde env (prefix={env_prefix})...")
                self.client = ChessClient.from_env(prefix=env_prefix)
            logger.info("Cliente instanciado correctamente")
        except Exception as error:
            logger.error(f"Error instanciando el cliente de ChessERP: {error}")
            raise

    def to_csv(self, data, filename: str = "output.csv"):
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
            if ruta.cliente_rutas:
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
        Una fila por cliente, con múltiples columnas numeradas para cada fuerza.
        Incluye TODOS los campos del modelo Cliente.

        NOTA: Primero determina el máximo número de fuerzas para asegurar
        que todos los rows tengan las mismas columnas en el CSV.
        """
        if not data:
            return []

        # Primer paso: encontrar el máximo número de fuerzas
        max_fuerzas = max(len(cliente.clifuerza) if cliente.clifuerza else 0 for cliente in data)
        logger.debug(f"Máximo número de fuerzas encontrado: {max_fuerzas}")

        # Campos de fuerza que necesitamos en todas las filas
        fuerza_fields = [
            'id_sucursal', 'id_cliente', 'id_fuerza_ventas', 'des_fuerza_venta',
            'id_modo_atencion', 'des_modo_atencion', 'fecha_inicio_fuerza',
            'fecha_fin_fuerza', 'id_ruta', 'fecha_ruta_venta', 'anulado',
            'periodicidad_visita', 'semana_visita', 'dias_visita',
            'intercalacion_visita', 'perioricidad_entrega', 'semana_entrega',
            'dias_entrega', 'intercalacion_entrega', 'horarios',
        ]

        flat = []
        for cliente in data:
            # Cliente base - TODOS los campos del modelo Cliente
            cli_base = {
                # Identificación Sucursal/Cliente
                'id_sucursal': cliente.id_sucursal,
                'des_sucursal': cliente.des_sucursal,
                'id_cliente': cliente.id_cliente,
                'fecha_alta': cliente.fecha_alta,
                'anulado': cliente.anulado,
                'fecha_baja': cliente.fecha_baja,

                # Datos Comerciales
                'id_alias_vigente': cliente.id_alias_vigente,
                'id_forma_pago': cliente.id_forma_pago,
                'des_forma_pago': cliente.des_forma_pago,
                'plazo_pago': cliente.plazo_pago,
                'id_lista_precio': cliente.id_lista_precio,
                'des_lista_precio': cliente.des_lista_precio,

                # Comprobantes y Límites
                'id_comprobante': cliente.id_comprobante,
                'des_comprobante': cliente.des_comprobante,
                'limite_importe': cliente.limite_importe,
                'id_art_limite': cliente.id_art_limite,
                'des_art_limite': cliente.des_art_limite,
                'cant_art_limite': cliente.cant_art_limite,
                'cpbtes_impagos': cliente.cpbtes_impagos,
                'dias_deuda_vencida': cliente.dias_deuda_vencida,

                # Ubicación Principal
                'id_pais': cliente.id_pais,
                'id_provincia': cliente.id_provincia,
                'des_provincia': cliente.des_provincia,
                'id_departamento': cliente.id_departamento,
                'des_departamento': cliente.des_departamento,
                'id_localidad': cliente.id_localidad,
                'des_localidad': cliente.des_localidad,
                'calle': cliente.calle,
                'altura': cliente.altura,
                'entre_calle_1': cliente.entre_calle_1,
                'entre_calle_2': cliente.entre_calle_2,
                'comentario': cliente.comentario,
                'longitud_geo': cliente.longitud_geo,
                'latitud_geo': cliente.latitud_geo,
                'horario': cliente.horario,

                # Ubicación Entrega
                'id_localidad_entrega': cliente.id_localidad_entrega,
                'des_localidad_entrega': cliente.des_localidad_entrega,
                'calle_entrega': cliente.calle_entrega,
                'altura_entrega': cliente.altura_entrega,
                'piso_depto_entrega': cliente.piso_depto_entrega,
                'entre_calle_1_entrega': cliente.entre_calle_1_entrega,
                'entre_calle_2_entrega': cliente.entre_calle_2_entrega,
                'comentario_entrega': cliente.comentario_entrega,
                'longitud_geo_entrega': cliente.longitud_geo_entrega,
                'latitud_geo_entrega': cliente.latitud_geo_entrega,
                'horario_entrega': cliente.horario_entrega,

                # Contacto
                'telefono_fijo': cliente.telefono_fijo,
                'telefono_movil': cliente.telefono_movil,
                'email': cliente.email,
                'comentario_adicional': cliente.comentario_adicional,

                # Comisiones
                'id_comision_venta': cliente.id_comision_venta,
                'des_comision_venta': cliente.des_comision_venta,
                'id_comision_flete': cliente.id_comision_flete,
                'des_comision_flete': cliente.des_comision_flete,
                'porcentaje_flete': cliente.porcentaje_flete,

                # Marketing (TODOS los campos)
                'id_subcanal_mkt': cliente.id_subcanal_mkt,
                'des_subcanal_mkt': cliente.des_subcanal_mkt,
                'id_canal_mkt': cliente.id_canal_mkt,
                'des_canal_mkt': cliente.des_canal_mkt,
                'id_segmento_mkt': cliente.id_segmento_mkt,
                'des_segmento_mkt': cliente.des_segmento_mkt,
                'id_ramo': cliente.id_ramo,
                'des_ramo': cliente.des_ramo,
                'id_area': cliente.id_area,
                'des_area': cliente.des_area,
                'id_agrupacion': cliente.id_agrupacion,
                'des_agrupacion': cliente.des_agrupacion,

                # Marketing - Atributos adicionales
                'es_potencial': cliente.es_potencial,
                'es_cuenta_y_orden': cliente.es_cuenta_y_orden,
                'id_ocasion_consumo': cliente.id_ocasion_consumo,
                'des_ocasion_consumo': cliente.des_ocasion_consumo,
                'id_subcategoria_foco': cliente.id_subcategoria_foco,
                'des_subcategoria_foco': cliente.des_subcategoria_foco,
                'foco_trade': cliente.foco_trade,
                'foco_ventas': cliente.foco_ventas,
                'cluster_ventas': cliente.cluster_ventas,

                # Aplanando alias
                'alias_id_alias': cliente.cliente_alias[0].id_alias if cliente.cliente_alias else None,
                'alias_razon_social': cliente.cliente_alias[0].razon_social if cliente.cliente_alias else None,
                'alias_fantasia_social': cliente.cliente_alias[0].fantasia_social if cliente.cliente_alias else None,
                'alias_identificador': cliente.cliente_alias[0].identificador if cliente.cliente_alias else None,
                'alias_id_tipo_contribuyente': cliente.cliente_alias[0].id_tipo_contribuyente if cliente.cliente_alias else None,
                'alias_des_tipo_contribuyente': cliente.cliente_alias[0].des_tipo_contribuyente if cliente.cliente_alias else None,
                'alias_fecha_hora_alta': cliente.cliente_alias[0].fecha_hora_alta if cliente.cliente_alias else None,
                'alias_anulado': cliente.cliente_alias[0].anulado if cliente.cliente_alias else None,
            }

            # Agregar campos para todas las fuerzas (1 a max_fuerzas)
            for i in range(1, max_fuerzas + 1):
                # Si el cliente tiene la fuerza número i, agregar sus valores
                if cliente.clifuerza and i <= len(cliente.clifuerza):
                    fuerza = cliente.clifuerza[i - 1]  # i-1 porque las listas son 0-indexed
                    cli_base.update({
                        f'fuerza_id_sucursal{i}': fuerza.id_sucursal,
                        f'fuerza_id_cliente{i}': fuerza.id_cliente,
                        f'fuerza_id_fuerza_ventas{i}': fuerza.id_fuerza_ventas,
                        f'fuerza_des_fuerza_venta{i}': fuerza.des_fuerza_venta,
                        f'fuerza_id_modo_atencion{i}': fuerza.id_modo_atencion,
                        f'fuerza_des_modo_atencion{i}': fuerza.des_modo_atencion,
                        f'fuerza_fecha_inicio_fuerza{i}': fuerza.fecha_inicio_fuerza,
                        f'fuerza_fecha_fin_fuerza{i}': fuerza.fecha_fin_fuerza,
                        f'fuerza_id_ruta{i}': fuerza.id_ruta,
                        f'fuerza_fecha_ruta_venta{i}': fuerza.fecha_ruta_venta,
                        f'fuerza_anulado{i}': fuerza.anulado,
                        f'fuerza_periodicidad_visita{i}': fuerza.periodicidad_visita,
                        f'fuerza_semana_visita{i}': fuerza.semana_visita,
                        f'fuerza_dias_visita{i}': fuerza.dias_visita,
                        f'fuerza_intercalacion_visita{i}': fuerza.intercalacion_visita,
                        f'fuerza_perioricidad_entrega{i}': fuerza.perioricidad_entrega,
                        f'fuerza_semana_entrega{i}': fuerza.semana_entrega,
                        f'fuerza_dias_entrega{i}': fuerza.dias_entrega,
                        f'fuerza_intercalacion_entrega{i}': fuerza.intercalacion_entrega,
                        f'fuerza_horarios{i}': fuerza.horarios,
                    })
                else:
                    # Si no tiene esa fuerza, rellenar con None
                    cli_base.update({
                        f'fuerza_id_sucursal{i}': None,
                        f'fuerza_id_cliente{i}': None,
                        f'fuerza_id_fuerza_ventas{i}': None,
                        f'fuerza_des_fuerza_venta{i}': None,
                        f'fuerza_id_modo_atencion{i}': None,
                        f'fuerza_des_modo_atencion{i}': None,
                        f'fuerza_fecha_inicio_fuerza{i}': None,
                        f'fuerza_fecha_fin_fuerza{i}': None,
                        f'fuerza_id_ruta{i}': None,
                        f'fuerza_fecha_ruta_venta{i}': None,
                        f'fuerza_anulado{i}': None,
                        f'fuerza_periodicidad_visita{i}': None,
                        f'fuerza_semana_visita{i}': None,
                        f'fuerza_dias_visita{i}': None,
                        f'fuerza_intercalacion_visita{i}': None,
                        f'fuerza_perioricidad_entrega{i}': None,
                        f'fuerza_semana_entrega{i}': None,
                        f'fuerza_dias_entrega{i}': None,
                        f'fuerza_intercalacion_entrega{i}': None,
                        f'fuerza_horarios{i}': None,
                    })

            flat.append(cli_base)
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
                self.to_csv(data, 'test_stock.csv')
            return data

        return self._test_wrapper("Stock (StockFisico)", _test)

    def sales(self):
        """Test del modelo Sale (Ventas)."""
        def _test():
            # Get Sales full month
        #     hoy = date.today()
        #     fecha_desde = date(hoy.year, hoy.month, 1)
        #     dias_en_mes = calendar.monthrange(fecha_desde.year, fecha_desde.month)[1]
        #     fecha_hasta = date(hoy.year, hoy.month, dias_en_mes)
            fecha_desde = date(2026, 1, 1)
            fecha_hasta = date(2026, 1, 31)

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
                self.to_csv(flat_data, 'test_sales.csv')
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
                self.to_csv(flat_data, 'test_articles.csv')
            return data

        return self._test_wrapper("Articles (Artículos)", _test)

    def routes(self):
        """Test del modelo RutaVenta."""
        def _test():
            logger.info("Obteniendo rutas de venta...")
            data = self.client.get_routes(sucursal=1, anulado=False)
            logger.info(f"Rutas obtenidas: {len(data)}")

            if data:
                logger.debug(f"Primera ruta: {data[0]}")
                # Aplanar Ruta → Clientes
                flat_data = data
                #flat_data = self._flatten_routes(data)
                logger.info(f"Registros aplanados (ruta+clientes): {len(flat_data)}")
                self.to_csv(flat_data, 'test_routes.csv')
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
                self.to_csv(flat_data, 'test_orders.csv')
            return data

        return self._test_wrapper("Orders (Pedidos)", _test)

    def clients(self):
        """Test del modelo Cliente."""
        def _test():
            logger.info("Obteniendo clientes...")
            data = self.client.get_customers(nro_lote=0)
            logger.info(f"Clientes obtenidos: {len(data)}")

            if data:
                logger.debug(f"Primer cliente: {data[0]}")
                # Aplanar Cliente → Alias → Fuerza
                flat_data = self._flatten_clients(data)
                logger.info(f"Registros aplanados (cliente+alias+fuerza): {len(flat_data)}")
                self.to_csv(flat_data, 'test_clients.csv')
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
                self.to_csv(data, 'test_staff.csv')
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
                self.to_csv(flat_data, 'test_marketing.csv')
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

    Uso:
        python live_test.py --prefix EMPRESA1_ --test sales
        python live_test.py --test all  # usa variables sin prefijo (API_URL, USERNAME, PASSWORD)
    """
    import argparse

    parser = argparse.ArgumentParser(description='Pruebas en vivo de ChessERP API')
    parser.add_argument(
        '--prefix', '-p',
        type=str,
        default='',
        help='Prefijo para variables de entorno (ej: EMPRESA1_). Default: sin prefijo'
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
    logger.info(f"Prefix: {args.prefix or '(ninguno)'}")
    logger.info(f"Test: {args.test}")

    # Inicializar clase de pruebas con prefijo de variables de entorno
    tester = Testing(env_prefix=args.prefix)

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


