import pandas as pd
import os
columnas_importantes = '''Descripcion Empresa
Descripcion Comprobante
Letra
Serie \\ Punto de venta
Numero
Regimen
Motivo Rechazo / Devolucion
Descripcion Motivo Rechazo / Devolucion
Fecha Comprobante
Emisor
Sucursal
Descripcion Sucursal
Esquema
Descripcion Esquema
Deposito
Descripcion Deposito
Vendedor
Descripcion Vendedor
Sector de venta
Descripcion de Sector de Venta
Supervisor
Descripcion Supervisor
Descripcion Tipo IVA
Fecha pedido
Descripcion Transporte
Cajero
Cliente
Razon Social
Domicilio
Codigo de Articulo
Descripcion de Articulo
MARCA
Descripción MARCA
GENERICO
Descripción GENERICO
Proveedor
Precio de compra Bruto
Precio de compra Neto
Bultos Cerrados
Unidades
Bultos con Cargo
Bultos sin Cargo
Bultos Total
Bultos Rechazados
Precio Unitario Bruto
Bonificacion %
Precio Neto Unitario
Subtotal Bruto
Subtotal Bonificado
Subtotal Neto
I.V.A 21%
I.V.A. 27%
I.V.A. 10.5%
Percepción 3337
Percepción 5329
Percepción 212
I.I.B.B(SALTA)
Impuestos Internos
Subtotal Final'''

base_path = os.path.dirname(os.path.abspath(__file__))
columnas_importantes = columnas_importantes.split('\n')

# file_path = os.path.join(base_path, '../data/columnas_importantes.txt')
# with open(file_path, 'r', encoding='utf-8') as file:
#     columnas_importantes = file.read()
class SalesData:
    def __init__(self, endpoint):
        self.data_dir = os.path.abspath(os.path.join((os.getcwd()), "data"))
        self.endpoint = endpoint
        self.sales = pd.DataFrame()

    def delete_bloat_columns(self, path):
        df = pd.read_csv(path, sep="\t", encoding='latin1', low_memory=False)
        df = df[columnas_importantes]
        df.to_excel(os.path.join(base_path, '../data/procesado/'), index=False)
    
    def process_data_reports(self):
        


# def insert_in_db():
#     pass
if __name__ == "__main__":
    name = "/run/media/nahuel/7E9814069813BC19/Users/pc10/Desktop/Comprobantes Web/src/Reporte December 2021.xls"
    delete_bloat_columns(name)
