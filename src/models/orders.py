from typing import List, Optional
from pydantic import BaseModel, Field

class LineaPedido(BaseModel):
    """
    Línea de pedido.
    Ref: HTML defs["pedidosDetalle"]
    """
    id_linea_detalle: int = Field(alias="idLineaDetalle")
    id_motivo_cambio: Optional[int] = Field(None, alias="idMotivoCambio")
    id_articulo: int = Field(alias="idArticulo")
    
    cant_bultos: Optional[int] = Field(None, alias="cantBultos")
    cant_unidades: Optional[int] = Field(None, alias="cantUnidades")
    peso_kilos: Optional[int] = Field(None, alias="pesoKilos") # HTML dice Integer
    
    precio_unitario: Optional[float] = Field(None, alias="precioUnitario") # HTML dice Number
    bonificacion: Optional[float] = Field(None, alias="bonificacion")

class Pedido(BaseModel):
    """
    Pedido.
    Ref: HTML defs["PedidosRequest"] (Usado como base para respuesta)
    """
    id_pedido: int = Field(alias="idPedido")
    origen: str = Field(alias="origen")
    id_usuario: int = Field(alias="idUsuario")
    id_empresa: int = Field(alias="idEmpresa")
    id_sucursal: int = Field(alias="idSucursal")
    
    id_fuerza_ventas: Optional[int] = Field(None, alias="idFuerzaVentas")
    id_deposito: Optional[int] = Field(None, alias="idDeposito")
    id_forma_pago: Optional[int] = Field(None, alias="idFormaPago")
    id_tipo_documento: Optional[int] = Field(None, alias="idTipoDocumento")
    id_cliente: int = Field(alias="idCliente")
    id_alias_cliente: Optional[int] = Field(None, alias="idAliasCliente")
    
    fecha_entrega: Optional[str] = Field(None, alias="fechaEntrega")
    id_vendedor: Optional[int] = Field(None, alias="idVendedor")
    id_modo_atencion: Optional[int] = Field(None, alias="idModoAtencion")
    
    # Detalle con nombre "líneas del pedido" según HTML
    lineas: Optional[List[LineaPedido]] = Field(None, alias="líneas del pedido")