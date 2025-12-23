from typing import Annotated, Any, List, Optional
from pydantic import BaseModel, Field, BeforeValidator


def empty_str_to_none(v: Any) -> Any:
    """Convierte strings vacíos a None."""
    if v == '' or v is None:
        return None
    return int(v) if isinstance(v, str) else v


OptionalInt = Annotated[Optional[int], BeforeValidator(empty_str_to_none)]

class ClienteRuta(BaseModel):
    """
    Cliente asignado a una ruta.
    Ref: HTML defs["clienteRutas"]
    """
    id_sucursal: int = Field(alias="idSucursal")
    id_fuerza_ventas: int = Field(alias="idFuerzaVentas")
    id_modo_atencion: str = Field(alias="idModoAtencion")  # API devuelve string (ej: 'PRE')
    id_ruta: int = Field(alias="idRuta")
    id_cliente: int = Field(alias="idCliente")
    razon_social: Optional[str] = Field(None, alias="razonSocial")
    
    intercalacion_visita: OptionalInt = Field(None, alias="intercalacionVisita")
    intercalacion_entrega: OptionalInt = Field(None, alias="intercalacionEntrega")
    
    fecha_desde: Optional[str] = Field(None, alias="fechaDesde")
    fecha_hasta: Optional[str] = Field(None, alias="fechaHasta")
    fecha_ruta_desde: Optional[str] = Field(None, alias="fechaRutaDesde")

class RutaVenta(BaseModel):
    """
    Ruta de Venta.
    Ref: HTML defs["rutasVenta"]
    """
    id_sucursal: int = Field(alias="idSucursal")
    des_sucursal: Optional[str] = Field(None, alias="desSucursal")
    id_fuerza_ventas: int = Field(alias="idFuerzaVentas")
    des_fuerza_ventas: Optional[str] = Field(None, alias="desFuerzaVentas")
    id_modo_atencion: str = Field(alias="idModoAtencion")  # API devuelve string (ej: 'PRE')
    des_modo_atencion: Optional[str] = Field(None, alias="desModoAtencion")
    
    id_ruta: int = Field(alias="idRuta")
    des_ruta: Optional[str] = Field(None, alias="desRuta")
    
    fecha_desde: Optional[str] = Field(None, alias="fechaDesde")
    fecha_hasta: Optional[str] = Field(None, alias="fechaHasta")
    anulado: Optional[bool] = Field(None, alias="anulado")
    
    id_personal: OptionalInt = Field(None, alias="idPersonal")
    des_personal: Optional[str] = Field(None, alias="desPersonal")

    periodicidad_visita: OptionalInt = Field(None, alias="periodicidadVisita")
    semana_visita: OptionalInt = Field(None, alias="semanaVisita")
    dias_visita: Optional[str] = Field(None, alias="dias_visita")  # Días de semana

    periodicidad_entrega: OptionalInt = Field(None, alias="periodicidadEntrega")
    semana_entrega: OptionalInt = Field(None, alias="semanaEntrega")
    dias_entrega: Optional[str] = Field(None, alias="diasEntrega")  # Días de semana: '2,3,4,5,6,7'

    cliente_rutas: Optional[List[ClienteRuta]] = Field(None, alias="clienteRutas")
