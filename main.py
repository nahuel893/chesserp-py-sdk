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

def main(): # Creamos una instancia de la clase Endpoint
    pass

if __name__ == "__main__":
    main()
