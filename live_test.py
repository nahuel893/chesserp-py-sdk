# Local Imports
from src.client import ChessClient
from src.exceptions import AuthError, ApiError
from src import client
from src.logger import setup_logger, get_logger

from datetime import date
import pandas as pd

# Configurar logger globalmente al inicio (capturará logs de src.client también)
logger = setup_logger(log_file="live_test.log")

def main():
    logger.info("Iniciando prueba en vivo...")
    
    # 1. Inicializar el cliente
    # instance = b, usa las credenciales _B del .env
    try:
        client = ChessClient(instance='b')
    except Exception as error:
        print("Error instanciando el cliente de ChessERP:", error, client)

    # 2. Realizar Loging
    logger.info("Testing Login")
    f_ini = client.login() 
    logger.debug(f"Session ID: {f_ini}")

    # 3. Prueba de ventas
    logger.info("Testing Sales")
    sales = client.get_sales(
        fecha_desde="2025-11-01", 
        fecha_hasta="2025-11-02", 
        detallado=True,
        empresas=1,
    )
    logger.info(f"Sales Data")
    # conversion  
    print(sales[0:1])

    # 4. 
 

if __name__ == '__main__':
    main()


