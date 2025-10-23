# Estandar library imports
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Local imports
from src.endpoints import Endpoints
from src.stock import StockData

ABS_PATH = (os.path.abspath(__file__))
#FATHER_PATH = os.path.dirname(ABS_PATH)
DATA_PATH = os.path.join(os.path.dirname(ABS_PATH), "data")
print(ABS_PATH)
#print(FATHER_PATH)
print(DATA_PATH)

"""
    TO-DO:
    * Import and export to csv
    * Add tests
    * Create Sales class
"""
def main(): # Creamos una instancia de la clase Endpoint
    load_dotenv()
    
    # Login Chess S
    endp = Endpoints(os.getenv("API_URL_S"), os.getenv("USERNAME_S"), os.getenv("PASSWORD_S"))
    endp.login()

    # Login
    stock = StockData(endp)
    stock.load_extra_data(
        df_deposits_path= os.path.join(DATA_PATH, "deposits_s.csv"),
        df_bloat_articles_path= os.path.join(DATA_PATH, "bloat_articles_s.csv"),
        df_categories_path= os.path.join(DATA_PATH, "categories_s.csv"),
        categories_id_col='Codigo'
    )
    stock.get_stocks()
    stock.transform_data()
    stock.to_excel(name="stock_s")
    
    # Login Chess B
    endp = Endpoints(os.getenv("API_URL_B"), os.getenv("USERNAME_B"), os.getenv("PASSWORD_B"))
    endp.login()

    # Login
    stock = StockData(endp)
    stock.load_extra_data(
        df_deposits_path= os.path.join(DATA_PATH, "deposits_b.csv"),
        df_bloat_articles_path= os.path.join(DATA_PATH, "bloat_articles_b.csv"),
        df_categories_path= os.path.join(DATA_PATH, "categories_b.csv"),
    )
    stock.get_stocks()
    stock.transform_data()
    stock.to_csv(name="stock_b")
    branches = [1, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16]
    endp.obtener_reporte(
        branches, "ventas_hasta_hoy", "2025-10-01", "2025-10-31")
    # Get report of sales

    # Realizamos el login
    # response = endpoint.login()
    # Obtenemos el reporte
    # start_date = datetime(2025, 4, 1)
    # end_date = datetime(2025, 4, 30)  # Adjust this date as needed

    # current_date = start_date

    # # Hacer peticiones por mes
    # while current_date < end_date:
    #     next_month = current_date + timedelta(days=31)
    #     next_month = next_month.replace(day=1)

    #     fecha_inicio = current_date.strftime("%Y-%m-%d")
    #     fecha_fin = (next_month - timedelta(days=1)).strftime("%Y-%m-%d")
        
    #     print('fecha inicio:', fecha_inicio)
    #     print('fecha fin:', fecha_fin)

    #     nombre_mes = current_date.strftime("%B")
    #     nombre_anio = current_date.strftime("%Y")

    #     print('nombre del mes:', nombre_mes)
    #     print('nombre del anio:', nombre_anio)

    #     name = f'Reporte {nombre_mes} {nombre_anio}'
    #     endpoint.obtener_reporte(name, fecha_inicio, fecha_fin)
    #     current_date = next_month

      
    #     # Luego cada mes procesarlo, dejar columnas importanes y guardarlo.
    #     ruta_archivo = os.path.join( FATHER_PATH+ "\\" + name + '.xls')
    #     data.delete_bloat_columns(ruta_archivo) 


if __name__ == "__main__":
    main()
