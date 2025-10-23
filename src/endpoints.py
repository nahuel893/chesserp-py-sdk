import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd
import io


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
Impuestos Internos
Subtotal Final'''
columnas_importantes = columnas_importantes.split("\n")

from src.logger import get_logger
import json

logger = get_logger(__name__)

class Endpoints:
    global columnas_importantes
    ABS_PATH = os.path.dirname(os.path.abspath(__file__))
    FATHER_PATH = os.path.dirname(ABS_PATH)

    def __init__(self, baseURL: str, user: str, passw: str):
        self.basePath = baseURL
        self.baseURL = f"{self.basePath}web/api"
        self.loginURL = f"{self.basePath}web/api/chess/v1/auth/login"
        self.credentials = {
            "usuario": user, "password": passw}
        self.sessionId = None
        self.depositos = {"1": ""}

        logger.info("Endpoint initialized", extra={"baseURL": self.baseURL})

    def login(self):
        try:
            # Realizamos la solicitud POST para loguearnos
            logger.info("Login in progress")
            logger.debug(f"basePath: {self.basePath}")
            logger.debug(f"loginUrl: {self.loginURL}")
            logger.debug(f"Credentials: {self.credentials}")
            response = requests.post(self.loginURL, json=self.credentials)

            # Verificamos si la respuesta es JSON y obtenemos el sessionId
            if response.status_code == 200:
                try:
                    # Intentamos extraer el sessionId del JSON
                    response_json = response.json()
                    sessionId = response_json.get("sessionId")
                    self.sessionId = sessionId
                    self.response = response

                    if sessionId:
                        logger.info(f"SessionId obtenido: {sessionId}")
                        return response.json()
                    else:
                        logger.error("No se encontró 'sessionId' en la respuesta del servidor.")
                except ValueError:
                    logger.error("La respuesta no es un JSON válido.")
            else:
                logger.error(f"Error en el login: {response.status_code}, Respuesta: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión o solicitud: {e}")

    def obtener_reporte(self, branches: list, name: str, fecha_desde: str, fecha_hasta: str):
        # Formato fecha desde y hasta: "AAAA-MM-DD"
        reports_list = []
        bytes_list = []
        reporte_url = self.baseURL + "/reporteComprobantesVta/exportarExcel"
        header = {"Cookie": self.sessionId}
        data_post = {
            "dsFiltrosRepCbtsVta": {
                "eFiltros": [
                    {
                        "letra": None,
                        "serie": None,
                        "numero": None,
                        "numeroHasta": None,
                        "fechadesde": fecha_desde,
                        "fechahasta": fecha_hasta,
                        "idsucur": "1",
                        "timbrado": "",
                        "empresas": "1",
                        "idsucur": "1",
                        "tiposdoc": "DVVTA,FCVTA",
                        "formasagruart": "MARCA,GENERICO,,,,,,,,"
                    }
                ]
            },
            "pcTipo": "D"
        }

        try:
            for branch in branches:
                data_post["dsFiltrosRepCbtsVta"]["eFiltros"][0]["idsucur"] = str(
                    branch)
                # Realizamos la solicitud POST para exportar el reporte
                response_reporte = requests.post(
                    reporte_url, json=data_post, headers=header)

                # Comprobamos si la respuesta contiene el archivo para descargar
                if response_reporte.status_code == 200:
                    # Extraemos el path del archivo del reporte
                    response_json = response_reporte.json()
                    pcArchivo = response_json.get("pcArchivo")

                    if pcArchivo:
                        logger.info(
                            f"Archivo para descargar: {self.basePath + pcArchivo}")
                    else:
                        logger.info("Error: No se encontró 'pcArchivo' en la respuesta.")
                        exit()

                    # Paso 3: Descargar el archivo
                    archivo_url = self.basePath + pcArchivo
                    response_excel = requests.get(archivo_url, headers=header)

                    if response_excel.status_code == 200:
                        # Guardamos el archivo temporalmente
                        ruta = os.path.join(self.FATHER_PATH, "data", "original", f"{name}-{branch}-{fecha_hasta}.xls")
                        reports_list.append(ruta)
                        with open(ruta, "wb") as f:
                            f.write(response_excel.content)
                        print("Archivo descargado correctamente.")

            dfs = [pd.read_csv(path, sep="\t", encoding='latin1', low_memory=False)[columnas_importantes] for path in reports_list]
            df  = pd.concat(dfs, ignore_index=True)
            pivot= df.pivot_table(
                values='Bultos Total',
                index=['Sucursal','Codigo de Articulo'],
                aggfunc='sum',
            )
            fecha = df['Fecha Comprobante'].max()
            with open(os.path.join(self.FATHER_PATH, "data", "processed","fecha.txt"), "w") as f:
                f.write(str(fecha))

            pivot.reset_index(inplace=True)
            pivot.to_csv(os.path.join(self.FATHER_PATH, "data", "processed", f"pivot-{fecha_hasta}.csv"), index=False)
            df.to_excel(os.path.join(self.FATHER_PATH, "data", "processed", f"{name}-{fecha_hasta}.xlsx"), index=False)

        except requests.exceptions.RequestException as e:
            print(f"Error de conexión o solicitud: {e}")
            exit()

        return reports_list

    def get_sessionId(self):
        return self.sessionId

    def get_stock(self, date=datetime.now().strftime("%d-%m-%Y"), idDeposito="1"):
        stock_url = self.baseURL + "/chess/v1/stock/"
        headers = {"Cookie": self.sessionId}

        params = {
            "idDeposito": idDeposito,
            "frescura": "false",
            "DD-MM-AAAA": date
        }

        try:
            params['idDeposito'] = idDeposito
            params['DD-MM-AAAA'] = date

            response = requests.get(url=stock_url, params=params, headers=headers)
            logger.debug(f"Getting Stock -- Request: Url:{stock_url}, Params:{params}, Headers:{headers}")

            if response.status_code == 200:
                with open(os.path.join(self.FATHER_PATH, "data", "processed", "stock_response.txt"), "w", encoding="utf-8") as f:
                    f.write(json.dumps(response.json(), ensure_ascii=False, indent=2))

                return response.json()
            else:
                logger.error(f"Response is not 200 code: {response.status_code}, Respuesta: {response.text[:10]}")
                return None
        except Exception as error:
            logger.error("Error getting stock", error)


if __name__ == "__main__":
    load_dotenv()

    url = os.getenv("API_URL_B")
    username = os.getenv("USERNAME_B")
    password = os.getenv("PASSWORD_B")
    print(url, username, password)

    endpoint = Endpoints(url, username, password)
    endpoint.login()

    stock = endpoint.get_stock()
    # branches = [1, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16]

    # # branches = [1]
    # endpoint.obtener_reporte(
    #     branches, "ventas_hasta_hoy", "2025-06-01", "2025-06-30")
