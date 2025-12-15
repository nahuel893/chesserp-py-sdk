from typing import List, Optional, Union
from pydantic import BaseModel, Field

class SaleLine(BaseModel):
    """
    Línea de detalle de una venta.
    Ref: HTML defs["ventasDetalle"] (Inferido por contexto de lista "líneas del venta")
    """
    id_linea: int = Field(alias="idLinea")
    id_articulo: int = Field(alias="idArticulo")
    ds_articulo: Optional[str] = Field(None, alias="dsArticulo")
    id_concepto: Optional[int] = Field(None, alias="idConcepto")
    ds_concepto: Optional[str] = Field(None, alias="dsConcepto")
    es_combo: Optional[str] = Field(None, alias="esCombo")
    id_combo: Optional[int] = Field(None, alias="idCombo")
    
    # Datos Estadísticos
    id_articulo_estadistico: Optional[int] = Field(None, alias="idArticuloEstadistico")
    ds_articulo_estadistico: Optional[str] = Field(None, alias="dsArticuloEstadistico")
    presentacion_articulo: Optional[str] = Field(None, alias="presentacionArticulo")
    
    # Cantidades
    cantidad_por_pallets: Optional[int] = Field(None, alias="cantidadPorPallets")
    peso: Optional[float] = Field(None, alias="peso")
    cantidad_solicitada: Optional[float] = Field(None, alias="cantidadSolicitada")
    unidades_solicitadas: Optional[float] = Field(None, alias="unidadesSolicitadas")
    
    # Cantidades con/sin cargo (HTML pg 46 approx)
    cantidades_con_cargo: Optional[float] = Field(None, alias="cantidadesCorCargo") # Nota: HTML/PDF suele tener typo 'CorCargo'
    cantidades_sin_cargo: Optional[float] = Field(None, alias="cantidadesSinCargo")
    cantidades_total: Optional[float] = Field(None, alias="cantidadesTotal")
    peso_total: Optional[float] = Field(None, alias="pesoTotal")
    cantidades_rechazo: Optional[float] = Field(None, alias="cantidadesRechazo")
    
    # Unidades Medida
    unimed_cargo: Optional[float] = Field(None, alias="unimedcargo")
    unimed_scargo: Optional[float] = Field(None, alias="unimedscargo")
    unimed_total: Optional[float] = Field(None, alias="unimedtotal")
    
    # Precios y Montos
    precio_unitario_bruto: Optional[float] = Field(None, alias="precioUnitarioBruto")
    bonificacion: Optional[float] = Field(None, alias="bonificacion")
    precio_unitario_neto: Optional[float] = Field(None, alias="precioUnitarioNeto")
    tipo_cambio: Optional[float] = Field(None, alias="tipocambio")
    
    # Motivos
    motivo_cambio: Optional[str] = Field(None, alias="motivocambio")
    desc_motivo_cambio: Optional[str] = Field(None, alias="descmotcambio")
    
    # Totales Línea
    subtotal_bruto: Optional[float] = Field(None, alias="subtotalBruto")
    subtotal_bonificado: Optional[float] = Field(None, alias="subtotalBonificado")
    subtotal_neto: Optional[float] = Field(None, alias="subtotalNeto")
    subtotal_final: Optional[float] = Field(None, alias="subtotalFinal")
    
    # Impuestos
    iva21: Optional[float] = Field(None, alias="iva21")
    iva27: Optional[float] = Field(None, alias="iva27")
    iva105: Optional[float] = Field(None, alias="iva105")
    internos: Optional[float] = Field(None, alias="internos")
    per3337: Optional[float] = Field(None, alias="per3337")
    percepcion212: Optional[float] = Field(None, alias="percepcion212")
    percepcion_iibb: Optional[float] = Field(None, alias="percepcioniibb")


class Sale(BaseModel):
    """
    Encabezado de comprobante de venta.
    Ref: HTML defs["PedidosVentas"]
    """
    
    # Identificación Empresa/Doc
    id_empresa: int = Field(alias="idEmpresa")
    ds_empresa: Optional[str] = Field(None, alias="dsEmpresa")
    id_documento: Union[int, str] = Field(alias="idDocumento")
    ds_documento: Optional[str] = Field(None, alias="dsDocumento")
    letra: str = Field(alias="letra")
    serie: Union[str, int] = Field(alias="serie")
    nro_doc: int = Field(alias="nrodoc")
    anulado: Optional[bool] = Field(None, alias="anulado")
    
    # Movimientos
    id_mov_comercial: Optional[int] = Field(None, alias="idMovComercial")
    ds_mov_comercial: Optional[str] = Field(None, alias="dsMovComercial")
    id_rechazo: Optional[int] = Field(None, alias="idRechazo")
    ds_rechazo: Optional[str] = Field(None, alias="dsRechazo")
    
    # Fechas
    fecha_comprobante: str = Field(alias="fechaComprobate") # Typo 'Comprobate' presente en HTML defs
    fecha_alta: Optional[str] = Field(None, alias="fechaAlta")
    usuario_alta: Optional[str] = Field(None, alias="usuarioAlta")
    fecha_vencimiento: Optional[str] = Field(None, alias="fechaVencimiento")
    fecha_entrega: Optional[str] = Field(None, alias="fechaEntrega")
    
    # Organización
    id_sucursal: int = Field(alias="idSucursal")
    ds_sucursal: Optional[str] = Field(None, alias="dsSucursal")
    id_fuerza_ventas: Optional[int] = Field(None, alias="idFuerzaVentas")
    ds_fuerza_ventas: Optional[str] = Field(None, alias="dsFuerzaVentas")
    id_deposito: Optional[int] = Field(None, alias="idDeposito")
    ds_deposito: Optional[str] = Field(None, alias="dsDeposito")
    
    # Personal
    id_vendedor: Optional[int] = Field(None, alias="idVendedor")
    ds_vendedor: Optional[str] = Field(None, alias="dsVendedor")
    id_supervisor: Optional[int] = Field(None, alias="idSupervisor")
    ds_supervisor: Optional[str] = Field(None, alias="dsSupervisor")
    id_gerente: Optional[int] = Field(None, alias="idGerente")
    ds_gerente: Optional[str] = Field(None, alias="dsGerente")
    
    # Cliente
    id_cliente: int = Field(alias="idCliente")
    nombre_cliente: Optional[str] = Field(None, alias="nombreCliente")
    domicilio_cliente: Optional[str] = Field(None, alias="domicilioCliente")
    codigo_postal: Optional[Union[int, str]] = Field(None, alias="codigoPostal")
    
    id_localidad: Optional[int] = Field(None, alias="idLocalidad") # No explícito en defs["PedidosVentas"] pero común
    ds_localidad: Optional[str] = Field(None, alias="dsLocalidad")
    id_provincia: Optional[Union[int, str]] = Field(None, alias="idProvincia")
    ds_provincia: Optional[str] = Field(None, alias="dsProvincia")
    
    tipo_contribuyente: Optional[Union[int, str]] = Field(None, alias="tipoConstribuyente")
    ds_tipo_contribuyente: Optional[str] = Field(None, alias="dsTipoConstribuyente")
    
    # Pagos y Caja
    id_tipo_pago: Optional[int] = Field(None, alias="idTipoPago")
    ds_tipo_pago: Optional[str] = Field(None, alias="dsTipoPago")
    fecha_pago: Optional[str] = Field(None, alias="fechaPago")
    id_caja: Optional[int] = Field(None, alias="idCaja")
    fecha_caja: Optional[str] = Field(None, alias="fechaCaja")
    cajero: Optional[Union[int, str]] = Field(None, alias="cajero")
    
    # Logística Extra
    planilla_carga: Optional[str] = Field(None, alias="planillaCarga")
    id_fletero_carga: Optional[int] = Field(None, alias="idFleteroCarga")
    ds_fletero_carga: Optional[str] = Field(None, alias="dsFleteroCarga")
    
    # Pedido Origen
    id_pedido: Optional[int] = Field(None, alias="idPedido")
    fecha_pedido: Optional[str] = Field(None, alias="fechaPedido")
    origen: Optional[str] = Field(None, alias="origen")
    
    # Contabilidad / Segmentación
    id_negocio: Optional[int] = Field(None, alias="idNegocio")
    ds_negocio: Optional[str] = Field(None, alias="dsNegocio")
    id_agrupacion: Optional[int] = Field(None, alias="idAgrupacion")
    ds_agrupacion: Optional[str] = Field(None, alias="dsAgrupacion")
    id_area: Optional[int] = Field(None, alias="idArea")
    ds_area: Optional[str] = Field(None, alias="dsArea")
    id_segmento_mkt: Optional[int] = Field(None, alias="idSegmentoMkt")
    ds_segmento_mkt: Optional[str] = Field(None, alias="dsSegmentoMkt")
    id_canal_mkt: Optional[int] = Field(None, alias="idCanalMkt")
    ds_canal_mkt: Optional[str] = Field(None, alias="dsCanalMkt")
    id_subcanal_mkt: Optional[int] = Field(None, alias="idSubcanalMkt")
    # Nota: El HTML tiene un espacio en el alias "ds SegmentoMkt" para subcanal, verificar en respuesta real.
    ds_subsegmento_mkt: Optional[str] = Field(None, alias="ds SegmentoMkt")
    
    # Contable
    fecha_asiento_contable: Optional[str] = Field(None, alias="fechaAsientoContable")
    nro_asiento_contable: Optional[int] = Field(None, alias="nroAsientoContable")
    nro_plan_contable: Optional[int] = Field(None, alias="nroPlanContable")
    cod_cuenta_contable: Optional[int] = Field(None, alias="codCuentaContable")
    id_centro_costo: Optional[int] = Field(None, alias="idCentroCosto")
    ds_cuenta_contable: Optional[str] = Field(None, alias="dsCuentaContable")
    
    # Totales Monetarios
    subtotal_bruto: Optional[float] = Field(None, alias="subtotalBruto")
    subtotal_bonificado: Optional[float] = Field(None, alias="subtotalBonificado")
    subtotal_neto: Optional[float] = Field(None, alias="subtotalNeto")
    subtotal_final: Optional[float] = Field(None, alias="subtotalFinal")
    
    # Impuestos Globales
    iva21: Optional[float] = Field(None, alias="iva21")
    iva27: Optional[float] = Field(None, alias="iva27")
    iva105: Optional[float] = Field(None, alias="iva105")
    internos: Optional[float] = Field(None, alias="internos")
    per3337: Optional[float] = Field(None, alias="per3337")
    iva2: Optional[float] = Field(None, alias="iva2")
    percepcion212: Optional[float] = Field(None, alias="percepcion212")
    percepcion_iibb: Optional[float] = Field(None, alias="percepcioniibb")
    
    # Trade Spend
    tradespendg: Optional[Union[str, float]] = Field(None, alias="tradespendg")
    tradespends: Optional[Union[str, float]] = Field(None, alias="tradespends")
    tradespendb: Optional[Union[str, float]] = Field(None, alias="tradespendb")
    tradespendi: Optional[Union[str, float]] = Field(None, alias="tradespendi")
    tradespendp: Optional[Union[str, float]] = Field(None, alias="tradespendp")
    tradespendt: Optional[Union[str, float]] = Field(None, alias="tradespendt")
    totradspend: Optional[float] = Field(None, alias="totradspend")
    acciones: Optional[str] = Field(None, alias="acciones")
    
    # Percepciones IIBB Extra
    persiibbd: Optional[Union[float, str]] = Field(None, alias="persiibbd")
    persiibbr: Optional[Union[float, str]] = Field(None, alias="persiibbr")
    
    # Activos Fijos
    numeros_serie: Optional[Union[int, str]] = Field(None, alias="numerosserie")
    numeros_activo: Optional[Union[int, str]] = Field(None, alias="numerosactivo")
    
    # Cuentas y Orden
    cuenta_y_orden: Optional[Union[int, str]] = Field(None, alias="cuentayorden")
    cod_prov_cyo: Optional[int] = Field(None, alias="codprovcyo")
    descrip_cyo: Optional[str] = Field(None, alias="descrip")
    nro_rend_cyo: Optional[int] = Field(None, alias="nrorendcyo")
    
    # Fiscal / Factura Electrónica
    id_tipo_cambio: Optional[int] = Field(None, alias="idTipoCambio")
    ds_tipo_cambio: Optional[str] = Field(None, alias="dsTipoCambio")
    timbrado: Optional[int] = Field(None, alias="timbrado")
    cfdi_emitido: Optional[str] = Field(None, alias="cfdiEmitido")
    regimen_fiscal: Optional[Union[int, str]] = Field(None, alias="regimenFiscal")
    informado: Optional[Union[int, str]] = Field(None, alias="informado")
    firma_digital: Optional[str] = Field(None, alias="firmadigital")
    proveedor: Optional[str] = Field(None, alias="proveedor")
    fvigpcompra: Optional[str] = Field(None, alias="fvigpcompra")
    precio_compra_br: Optional[float] = Field(None, alias="preciocomprabr")
    precio_compra_nt: Optional[float] = Field(None, alias="preciocomprant")
    
    linea_credito: Optional[Union[int, str]] = Field(None, alias="lineaCredito")
    estado_fiscal: Optional[int] = Field(None, alias="estadoFiscal")
    numeracion_fiscal: Optional[Union[int, str]] = Field(None, alias="numeracionFiscal")

    # Lista de Items
    # Ref: HTML property "líneas del venta"
    lines: Optional[List[SaleLine]] = Field(None, alias="líneas del venta")
