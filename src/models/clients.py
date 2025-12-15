from typing import List, Optional, Union
from pydantic import BaseModel, Field

class ClienteAlias(BaseModel):
    """
    Alias de cliente.
    Ref: HTML defs["clienteAlias"]
    """
    id_cliente: int = Field(alias="idCliente")
    id_alias: int = Field(alias="idAlias")
    fecha_hora_alta: Optional[str] = Field(None, alias="fechaHoraAlta")
    anulado: Optional[bool] = Field(None, alias="anulado")
    
    # Datos Persona
    id_tipo_persona: Optional[int] = Field(None, alias="idTipoPersona")
    apellido_paterno: Optional[str] = Field(None, alias="apellidoPaterno")
    apellido_materno: Optional[str] = Field(None, alias="apellidoMaterno")
    nombres: Optional[str] = Field(None, alias="nombres")
    razon_social: Optional[str] = Field(None, alias="razonSocial")
    fantasia_social: Optional[str] = Field(None, alias="fantasiaSocial")
    
    # Contribuyente
    id_tipo_contribuyente: Optional[int] = Field(None, alias="idTipoContribuyente")
    des_tipo_contribuyente: Optional[str] = Field(None, alias="desTipoContribuyente")
    id_tipo_identificador: Optional[int] = Field(None, alias="idTipoIdentificador")
    des_tipo_identificador: Optional[str] = Field(None, alias="desTipoIdentificador")
    identificador: Optional[int] = Field(None, alias="identificador") # CUIT/DNI
    vencimiento_identificador: Optional[int] = Field(None, alias="vencimientoIdentificador")
    
    # Impuestos
    es_exento_iibb: Optional[bool] = Field(None, alias="esExentoIibb")
    fecha_vencimiento_exencion_iibb: Optional[str] = Field(None, alias="fechaVencimientoExencionIibb")
    es_inscripto_iibb: Optional[bool] = Field(None, alias="esInscriptoIibb")
    numero_inscripcion_iibb: Optional[int] = Field(None, alias="numeroInscripcionIibb")
    es_agente_percepcion_iibb: Optional[bool] = Field(None, alias="esAgentePercepcionIibb")
    es_convenio_multilateral: Optional[bool] = Field(None, alias="esConvenioMultilateral")
    provincias_cm05: Optional[int] = Field(None, alias="provinciasCm05")
    
    # Otros
    permiso_venta_alcohol: Optional[bool] = Field(None, alias="permisoVentaAlcohol")
    vencimiento_permiso_venta_alcohol: Optional[str] = Field(None, alias="vencimientoPermisoVentaAlcohol")
    es_gran_empresa: Optional[bool] = Field(None, alias="esGranEmpresa")
    es_mipyme: Optional[bool] = Field(None, alias="esMipyme")
    
    # Recursión extraña en HTML: clienteAlias tiene array "Clifuerza"
    clifuerza: Optional[List["ClienteFuerza"]] = Field(None, alias="Clifuerza")

class ClienteFuerza(BaseModel):
    """
    Relación Cliente-Fuerza de Venta.
    Ref: HTML defs["Clifuerza"]
    """
    id_sucursal: Optional[int] = Field(None, alias="idSucursal")
    id_cliente: Optional[int] = Field(None, alias="idCliente")
    id_fuerza_ventas: Optional[int] = Field(None, alias="idFuerzaVentas")
    des_fuerza_venta: Optional[str] = Field(None, alias="desFuerzaVenta")
    id_modo_atencion: Optional[int] = Field(None, alias="idModoAtencion")
    des_modo_atencion: Optional[str] = Field(None, alias="desModoAtencion")
    
    fecha_inicio_fuerza: Optional[str] = Field(None, alias="fechaInicioFuerza")
    fecha_fin_fuerza: Optional[str] = Field(None, alias="fechaFinFuerza")
    
    id_ruta: Optional[int] = Field(None, alias="idRuta")
    fecha_ruta_venta: Optional[str] = Field(None, alias="fechaRutaVenta")
    anulado: Optional[bool] = Field(None, alias="anulado")
    
    periodicidad_visita: Optional[int] = Field(None, alias="periodicidadVisita")
    semana_visita: Optional[int] = Field(None, alias="semanaVisita")
    dias_visita: Optional[int] = Field(None, alias="diasVisita")
    intercalacion_visita: Optional[int] = Field(None, alias="intercalacionVisita")
    
    perioricidad_entrega: Optional[int] = Field(None, alias="perioricidadEntrega")
    semana_entrega: Optional[int] = Field(None, alias="semanaEntrega")
    dias_entrega: Optional[int] = Field(None, alias="diasEntrega")
    intercalacion_entrega: Optional[int] = Field(None, alias="intercalacionEntrega")
    
    horarios: Optional[str] = Field(None, alias="Horarios")

class Cliente(BaseModel):
    """
    Maestro de Clientes.
    Ref: HTML defs["clientes"]
    """
    # Identificación Sucursal/Cliente
    id_sucursal: int = Field(alias="idSucursal")
    des_sucursal: Optional[str] = Field(None, alias="desSucursal")
    id_cliente: int = Field(alias="idCliente")
    fecha_alta: Optional[str] = Field(None, alias="fechaAlta")  # API retorna formato: '2021-08-25'
    anulado: Optional[bool] = Field(None, alias="anulado")
    fecha_baja: Optional[str] = Field(None, alias="fechaBaja")
    
    # Datos Comerciales
    id_alias_vigente: Optional[int] = Field(None, alias="idAliasVigente")
    id_forma_pago: Optional[int] = Field(None, alias="idFormaPago")
    des_forma_pago: Optional[str] = Field(None, alias="desFormaPago")
    plazo_pago: Optional[int] = Field(None, alias="plazoPago")
    id_lista_precio: Optional[int] = Field(None, alias="idListaPrecio")
    des_lista_precio: Optional[str] = Field(None, alias="desListaPrecio")
    
    # Comprobantes y Límites
    id_comprobante: Optional[str] = Field(None, alias="idComprobante") # HTML String
    des_comprobante: Optional[str] = Field(None, alias="desComprobante")
    limite_importe: Optional[int] = Field(None, alias="limiteImporte")
    id_art_limite: Optional[int] = Field(None, alias="idArtLimite")
    des_art_limite: Optional[str] = Field(None, alias="desArtLimite")
    cant_art_limite: Optional[int] = Field(None, alias="cantArtLimite")
    cpbtes_impagos: Optional[int] = Field(None, alias="cpbtesImpagos")
    dias_deuda_vencida: Optional[int] = Field(None, alias="diasDeudaVencida")
    
    # Ubicación Principal
    id_pais: Optional[str] = Field(None, alias="idPais")
    id_provincia: Optional[str] = Field(None, alias="idProvincia")
    des_provincia: Optional[str] = Field(None, alias="desProvincia")
    id_departamento: Optional[int] = Field(None, alias="idDepartamento")
    des_departamento: Optional[str] = Field(None, alias="desDepartamento")
    id_localidad: Optional[int] = Field(None, alias="idLocalidad")
    des_localidad: Optional[str] = Field(None, alias="desLocalidad")
    calle: Optional[str] = Field(None, alias="calle")
    altura: Optional[int] = Field(None, alias="altura")
    entre_calle_1: Optional[Union[str, int]] = Field(None, alias="entreCalle1")  # API retorna strings o ints
    entre_calle_2: Optional[Union[str, int]] = Field(None, alias="entreCalle2")  # API retorna strings o ints
    comentario: Optional[Union[str, int]] = Field(None, alias="comentario")  # API retorna strings o ints
    longitud_geo: Optional[Union[str, int]] = Field(None, alias="longitudGeo")  # API retorna strings o ints
    latitud_geo: Optional[Union[str, int]] = Field(None, alias="latitudGeo")  # API retorna strings o ints
    horario: Optional[Union[str, int]] = Field(None, alias="horario")  # API retorna strings o ints
    
    # Ubicación Entrega
    id_localidad_entrega: Optional[int] = Field(None, alias="idLocalidadEntrega")
    des_localidad_entrega: Optional[str] = Field(None, alias="desLocalidadEntrega")
    calle_entrega: Optional[str] = Field(None, alias="calleEntrega")
    altura_entrega: Optional[int] = Field(None, alias="alturaEntrega")
    piso_depto_entrega: Optional[Union[str, int]] = Field(None, alias="pisoDeptoEntrega")  # API retorna strings o ints
    entre_calle_1_entrega: Optional[Union[str, int]] = Field(None, alias="entreCalle1Entrega")  # API retorna strings o ints (ej: 'SANTA CECILIA' o 0)
    entre_calle_2_entrega: Optional[Union[str, int]] = Field(None, alias="entreCalle2Entrega")  # API retorna strings o ints
    comentario_entrega: Optional[str] = Field(None, alias="comentarioEntrega")
    longitud_geo_entrega: Optional[Union[str, int]] = Field(None, alias="longitudGeoEntrega")  # API retorna strings o ints
    latitud_geo_entrega: Optional[Union[str, int]] = Field(None, alias="latitudGeoEntrega")  # API retorna strings o ints
    horario_entrega: Optional[Union[str, int]] = Field(None, alias="horarioEntrega")  # API retorna strings o ints
    
    # Contacto
    telefono_fijo: Optional[Union[str, int]] = Field(None, alias="telefonoFijo")  # API retorna strings o ints (puede incluir guiones, espacios, etc.)
    telefono_movil: Optional[str] = Field(None, alias="telefonoMovil")
    email: Optional[str] = Field(None, alias="email")
    comentario_adicional: Optional[str] = Field(None, alias="comentarioAdicional")
    
    # Comisiones
    id_comision_venta: Optional[int] = Field(None, alias="idComisionVenta")
    des_comision_venta: Optional[str] = Field(None, alias="desComisionVenta")
    id_comision_flete: Optional[int] = Field(None, alias="idComisionFlete")
    des_comision_flete: Optional[str] = Field(None, alias="desComisionFlete")
    porcentaje_flete: Optional[int] = Field(None, alias="porcentajeFlete")
    
    # Marketing
    id_subcanal_mkt: Optional[int] = Field(None, alias="idSubcanalMkt")
    des_subcanal_mkt: Optional[str] = Field(None, alias="desSubcanalMkt")
    id_canal_mkt: Optional[int] = Field(None, alias="idCanalMkt")
    des_canal_mkt: Optional[str] = Field(None, alias="desCanalMkt")
    id_segmento_mkt: Optional[int] = Field(None, alias="idSegmentoMkt")
    des_segmento_mkt: Optional[str] = Field(None, alias="desSegmentoMkt")
    id_ramo: Optional[int] = Field(None, alias="idRamo")
    des_ramo: Optional[str] = Field(None, alias="desRamo")
    id_area: Optional[int] = Field(None, alias="idArea")
    des_area: Optional[str] = Field(None, alias="desArea")
    id_agrupacion: Optional[int] = Field(None, alias="idAgrupacion")
    des_agrupacion: Optional[str] = Field(None, alias="desAgrupacion")
    
    es_potencial: Optional[bool] = Field(None, alias="esPotencial")
    es_cuenta_y_orden: Optional[bool] = Field(None, alias="esCuentayOrden")
    id_ocasion_consumo: Optional[int] = Field(None, alias="idOcasionConsumo")
    des_ocasion_consumo: Optional[str] = Field(None, alias="desOcasionConsumo")
    id_subcategoria_foco: Optional[int] = Field(None, alias="idSubcategoriaFoco")
    des_subcategoria_foco: Optional[str] = Field(None, alias="desSubcategoriaFoco")
    foco_trade: Optional[bool] = Field(None, alias="focoTrade")
    foco_ventas: Optional[bool] = Field(None, alias="focoVentas")
    cluster_ventas: Optional[Union[str, int]] = Field(None, alias="clusterVentas")  # API retorna strings o ints
    
    # Relaciones
    cliente_alias: Optional[List[ClienteAlias]] = Field(None, alias="cliente alias")
