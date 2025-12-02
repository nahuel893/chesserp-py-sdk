from typing import Optional
from pydantic import BaseModel, Field

class PersonalComercial(BaseModel):
    """
    Personal Comercial.
    Ref: HTML defs["personalComercial"]
    """
    id_sucursal: int = Field(alias="idSucursal")
    des_sucursal: Optional[str] = Field(None, alias="desSucursal")
    
    id_personal: int = Field(alias="idPersonal")
    des_personal: str = Field(alias="desPersonal")
    
    id_fuerza_ventas: Optional[int] = Field(None, alias="idFuerzaVentas")
    des_fuerza_ventas: Optional[str] = Field(None, alias="desFuerzaVentas")
    
    cargo: Optional[str] = Field(None, alias="cargo")
    tipo_venta: Optional[str] = Field(None, alias="tipoVenta")
    
    id_personal_superior: Optional[int] = Field(None, alias="idPersonalSuperior")
    des_personal_superior: Optional[str] = Field(None, alias="desPersonalSuperior")
    
    domicilio: Optional[str] = Field(None, alias="domicilio")
    telefono: Optional[str] = Field(None, alias="telefono")
    fecha_nacimiento: Optional[str] = Field(None, alias="fechaNacimiento")
    
    usuario_sistema: Optional[str] = Field(None, alias="usuarioSistema")
    
    id_tipo_segmento: Optional[int] = Field(None, alias="idTipoSegmento")
    des_tipo_segmento: Optional[str] = Field(None, alias="desTipoSegmento")