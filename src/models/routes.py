from typing import List, Optional
from pydantic import BaseModel, Field

class ClienteRuta(BaseModel):
    """
    Cliente asignado a una ruta.
    Ref: HTML defs["clienteRutas"]
    """
    id_sucursal: int = Field(alias="idSucursal")
    id_fuerza_ventas: int = Field(alias="idFuerzaVentas")
    id_modo_atencion: int = Field(alias="idModoAtencion")
    id_ruta: int = Field(alias="idRuta")
    id_cliente: int = Field(alias="idCliente")
    razon_social: Optional[str] = Field(None, alias="razonSocial")
    
    intercalacion_visita: Optional[int] = Field(None, alias="intercalacionVisita")
    intercalacion_entrega: Optional[int] = Field(None, alias="intercalacionEntrega")
    
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
    id_modo_atencion: int = Field(alias="idModoAtencion")
    des_modo_atencion: Optional[str] = Field(None, alias="desModoAtencion")
    
    id_ruta: int = Field(alias="idRuta")
    des_ruta: Optional[str] = Field(None, alias="desRuta")
    
    fecha_desde: Optional[str] = Field(None, alias="fechaDesde")
    fecha_hasta: Optional[str] = Field(None, alias="fechaHasta")
    anulado: Optional[bool] = Field(None, alias="anulado")
    
    id_personal: Optional[int] = Field(None, alias="idPersonal")
    des_personal: Optional[str] = Field(None, alias="desPersonal")
    
    periodicidad_visita: Optional[int] = Field(None, alias="periodicidadVisita")
    semana_visita: Optional[int] = Field(None, alias="semanaVisita")
    dias_visita: Optional[int] = Field(None, alias="dias_visita") # HTML confirma underscore
    
    periodicidad_entrega: Optional[int] = Field(None, alias="periodicidadEntrega")
    semana_entrega: Optional[int] = Field(None, alias="semanaEntrega")
    dias_entrega: Optional[int] = Field(None, alias="diasEntrega")
    
    cliente_rutas: Optional[List[ClienteRuta]] = Field(None, alias="clienteRutas")
