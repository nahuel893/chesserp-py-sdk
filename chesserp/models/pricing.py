from typing import Optional, Union
from pydantic import BaseModel, Field


class ListaPrecio(BaseModel):
    """
    Lista de precios con su vigencia activa.
    Ref: Web API - precios/obtenerVigenciasListas -> eListaPrecios
    """
    id_lista: Optional[int] = Field(None, alias="listaspre")
    titulo: Optional[str] = Field(None, alias="titulis")
    id_vigencia: Optional[int] = Field(None, alias="idvigencia")
    vigente: Optional[bool] = Field(None, alias="vigente")
    fecha_vigencia_desde: Optional[str] = Field(None, alias="fecvigenciadesde")
    fecha_vigencia_hasta: Optional[str] = Field(None, alias="fecvigenciahasta")


class PrecioArticulo(BaseModel):
    """
    Artículo con precios dentro de una lista de precios.
    Ref: Web API - precios/obtenerListaPrecios -> dsPrecios.ePrecios
    """
    # Identificacion
    cod_articulo: Optional[Union[str, int]] = Field(None, alias="codart")
    descripcion: Optional[str] = Field(None, alias="descrip")
    presentacion: Optional[str] = Field(None, alias="despre")
    cod_barra_unidad: Optional[Union[str, int]] = Field(None, alias="codbarrauni")

    # Precios
    precio: Optional[float] = Field(None, alias="precio")
    iva: Optional[float] = Field(None, alias="iva1")
    precio_final: Optional[float] = Field(None, alias="prefin")
    precio_sugerido: Optional[float] = Field(None, alias="preciosugerido")
    precio_consumidor: Optional[float] = Field(None, alias="preconsumidor")
    internos_fijos: Optional[float] = Field(None, alias="interfij")
    precio_compra: Optional[float] = Field(None, alias="precom")
    precio_unit_venta: Optional[float] = Field(None, alias="preunivta")
    precio_unit_compra: Optional[float] = Field(None, alias="preunicom")

    # Margenes
    contribucion_neta: Optional[float] = Field(None, alias="contneta")
    contribucion_margen: Optional[float] = Field(None, alias="contmarg")
    margen_defecto: Optional[float] = Field(None, alias="margdef")
    porc_ib: Optional[float] = Field(None, alias="perib")
    internos: Optional[float] = Field(None, alias="internos")

    # Clasificacion
    cod_marca: Optional[Union[str, int]] = Field(None, alias="codmarca")
    marca: Optional[str] = Field(None, alias="marca")
    cod_rubro: Optional[Union[str, int]] = Field(None, alias="codgene")
    cod_linea: Optional[Union[str, int]] = Field(None, alias="codlin")
    division: Optional[Union[str, int]] = Field(None, alias="division")
    resto: Optional[Union[str, int]] = Field(None, alias="resto")
    btl_x_plt: Optional[Union[str, int, float]] = Field(None, alias="bltxplt")
    orden: Optional[int] = Field(None, alias="idorden")

    # Vigencia
    vigente_desde: Optional[str] = Field(None, alias="vigentedesde")
    vigente_hasta: Optional[str] = Field(None, alias="vigentehasta")
    anulado: Optional[bool] = Field(None, alias="anulado")
