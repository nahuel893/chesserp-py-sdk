from typing import List, Optional
from pydantic import BaseModel, Field

# --- Submodelos para Artículos ---

class AgrupacionArticulo(BaseModel):
    """
    Agrupación de artículos.
    Ref: HTML defs["agrupaciones"]
    """
    id_forma_agrupar: Optional[str] = Field(None, alias="idFormaAgrupar") # String en HTML
    des_forma_agrupar: Optional[str] = Field(None, alias="desFormaAgrupar")
    id_articulo: Optional[int] = Field(None, alias="idArticulo")
    id_agrupacion: Optional[int] = Field(None, alias="idAgrupacion")
    des_agrupacion: Optional[str] = Field(None, alias="desAgrupacion")
    # HTML define una recursión posible o relación anidada de relavacio aquí también?
    # defs["agrupaciones"] tiene propiedad "relavacio" -> items "$ref": "#/components/schemas/relavacio"
    # Lo agregaré aunque es extraño que una agrupación tenga envases.
    relavacio: Optional[List["RelacionEnvase"]] = Field(None, alias="relavacio")

class RelacionEnvase(BaseModel):
    """
    Relación con envases/retornables.
    Ref: HTML defs["relavacio"]
    """
    id_articulo: Optional[int] = Field(None, alias="idArticulo")
    id_art_retornable: Optional[int] = Field(None, alias="idArtRetornable")
    des_art_retornable: Optional[str] = Field(None, alias="desArtRetornable")
    cantidad_relacion: Optional[int] = Field(None, alias="cantidadRelacion")
    solo_bulto_cerrado: Optional[int] = Field(None, alias="soloBultoCerrado") # Integer en HTML

# --- Modelo Principal de Artículo ---

class Articulo(BaseModel):
    """
    Maestro de Artículos.
    Ref: HTML defs["articulos"]
    """
    id_articulo: int = Field(alias="idArticulo")
    des_articulo: str = Field(alias="desArticulo")
    unidades_bulto: Optional[int] = Field(None, alias="unidadesBulto")
    anulado: Optional[bool] = Field(None, alias="anulado")
    fecha_alta: Optional[str] = Field(None, alias="fechaAlta")
    factor_venta: Optional[str] = Field(None, alias="factorVenta")
    minimo_venta: Optional[int] = Field(None, alias="minimoVenta")
    
    # Flags y Propiedades Físicas
    pesable: Optional[bool] = Field(None, alias="pesable")
    peso_cota_superior: Optional[int] = Field(None, alias="pesoCotaSuperior")
    peso_cota_inferior: Optional[int] = Field(None, alias="pesoCotaInferior")
    
    es_combo: Optional[bool] = Field(None, alias="esCombo")
    detalle_combo_imp: Optional[int] = Field(None, alias="detalleComboImp")
    detalle_combo_inf: Optional[str] = Field(None, alias="detalleComboInf")
    
    # Impuestos
    exento_iva: Optional[bool] = Field(None, alias="exentoIva")
    inafecto: Optional[bool] = Field(None, alias="inafecto")
    exonerado: Optional[bool] = Field(None, alias="exonerado")
    iva_diferencial: Optional[bool] = Field(None, alias="ivaDiferencial")
    tasa_iva: Optional[int] = Field(None, alias="tasaIva")
    tasa_internos: Optional[int] = Field(None, alias="tasaInternos")
    internos_bulto: Optional[int] = Field(None, alias="internosBulto")
    tasa_iibb: Optional[int] = Field(None, alias="tasaIibb")
    
    # Flags Comerciales
    es_alcoholico: Optional[bool] = Field(None, alias="esAlcoholico")
    visible_mobile: Optional[bool] = Field(None, alias="visibleMobile")
    es_comodatable: Optional[bool] = Field(None, alias="esComodatable")
    des_corta_articulo: Optional[str] = Field(None, alias="desCortaArticulo")
    
    # Presentaciones (En HTML son Integer, salvo las descripciones que deberían ser String pero HTML dice Integer? Asumiremos int o str si falla)
    # defs["articulos"] -> desPresentacionBulto: "type": "integer". Esto huele a error en la doc HTML.
    # Usaré Union[int, str] o Optional[str] para ser seguro.
    id_presentacion_bulto: Optional[int] = Field(None, alias="idPresentacionBulto")
    des_presentacion_bulto: Optional[str] = Field(None, alias="desPresentacionBulto") 
    id_presentacion_unidad: Optional[int] = Field(None, alias="idPresentacionUnidad")
    des_presentacion_unidad: Optional[str] = Field(None, alias="desPresentacionUnidad")
    
    id_unidad_medida: Optional[int] = Field(None, alias="idUnidadMedida")
    des_unidad_medida: Optional[str] = Field(None, alias="desUnidadMedida") 
    valor_unidad_medida: Optional[int] = Field(None, alias="valorUnidadMedida")
    
    # Logística
    id_articulo_estadistico: Optional[int] = Field(None, alias="idArticuloEstadistico")
    cod_barra_bulto: Optional[int] = Field(None, alias="codBarraBulto") # HTML dice Integer
    cod_barra_unidad: Optional[int] = Field(None, alias="codBarraUnidad") # HTML dice Integer
    tiene_retornables: Optional[bool] = Field(None, alias="tieneRetornables")
    bultos_pallet: Optional[int] = Field(None, alias="bultosPallet")
    pisos_pallet: Optional[int] = Field(None, alias="pisosPallet")
    apilabilidad: Optional[int] = Field(None, alias="apilabilidad")
    peso_bulto: Optional[int] = Field(None, alias="pesoBulto")
    lleva_frescura: Optional[bool] = Field(None, alias="llevaFrescura")
    
    # Políticas
    dias_bloqueo: Optional[int] = Field(None, alias="diasBloqueo")
    politica_stock: Optional[int] = Field(None, alias="politicaStock")
    dias_ventana: Optional[int] = Field(None, alias="diasVentana")
    es_activo_fijo: Optional[int] = Field(None, alias="esActivoFijo")
    cantidad_puertas: Optional[int] = Field(None, alias="cantidadPuertas")
    unidades_frente: Optional[int] = Field(None, alias="unidadesFrente")
    litros_repago: Optional[int] = Field(None, alias="litrosRepago")
    
    id_art_usado: Optional[int] = Field(None, alias="idArtUsado")
    anios_amortizacion: Optional[int] = Field(None, alias="aniosAmortizacion")
    
    # Listas anidadas
    agrupaciones: Optional[List[AgrupacionArticulo]] = Field(None, alias="agrupaciones")
    # Relavacio no está directo en `articulos` en el HTML dump que vi, pero sí dentro de agrupaciones.
    # Sin embargo, PDF lo ponía en artículo. Lo dejaré comentado o fuera si no sale en el dump HTML raiz.
    # Revisando el dump... "agrupaciones": { type: array, items: ref agrupaciones }
    # No veo "relavacio" directo en articulos, solo dentro de agrupaciones.

# --- Modelo de Stock Físico ---

class StockFisico(BaseModel):
    """
    Stock físico.
    Ref: HTML defs["stock"] (No visible en el dump truncado, mantengo estructura PDF/General)
    """
    fecha: str = Field(alias="fecha")
    id_deposito: int = Field(alias="idDeposito")
    id_almacen: Optional[int] = Field(None, alias="idAlmacen")
    id_articulo: int = Field(alias="idArticulo")
    ds_articulo: Optional[str] = Field(None, alias="dsArticulo")
    fec_vto_lote: Optional[str] = Field(None, alias="fecVtoLote")
    cant_bultos: float = Field(alias="cantBultos")
    cant_unidades: float = Field(alias="cantUnidades")
