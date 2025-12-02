from typing import List, Optional
from pydantic import BaseModel, Field

# Estructura recursiva: Segmento -> Canal -> Subcanal

class SubCanalMkt(BaseModel):
    """
    Subcanal de Marketing.
    Ref: HTML defs["SubCanalesMkt"] (inferido de anidación en CanalesMkt)
    """
    id_subcanal_mkt: int = Field(alias="idSubcanalMkt")
    # Nota: HTML tiene un typo en `defs["clientes"]` donde llama al subcanal "ds SegmentoMkt", 
    # pero aquí en Jerarquía suele ser coherente. Usaremos nombres lógicos y alias probables.
    des_subcanal_mkt: str = Field(alias="desSubcanalMkt") 
    id_canal_mkt: Optional[int] = Field(None, alias="idCanalMkt")
    compania: Optional[bool] = Field(None, alias="compania")

class CanalMkt(BaseModel):
    """
    Canal de Marketing.
    Ref: HTML defs["CanalesMkt"]
    """
    id_canal_mkt: int = Field(alias="idCanalMkt")
    des_canal_mkt: str = Field(alias="desCanalMkt")
    id_segmento_mkt: Optional[int] = Field(None, alias="idSegmentoMkt")
    compania: Optional[bool] = Field(None, alias="compania")
    
    subcanales_mkt: Optional[List[SubCanalMkt]] = Field(None, alias="SubCanalesMkt")

class JerarquiaMkt(BaseModel):
    """
    Jerarquía de Marketing (Segmento raíz).
    Ref: HTML defs["jerarquiaMkt"]
    """
    id_segmento_mkt: int = Field(alias="idSegmentoMkt")
    des_segmento_mkt: str = Field(alias="desSegmentoMkt")
    compania: Optional[bool] = Field(None, alias="compania")
    
    canales_mkt: Optional[List[CanalMkt]] = Field(None, alias="CanalesMkt")