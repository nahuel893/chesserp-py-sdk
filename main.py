from src.client import ChessClient
from live_test import Testing
from datetime import date
from calendar import monthrange
import pandas as pd

# Instanciar cliente y helper de testing (para usar _flatten_sales)
chess_client = ChessClient(instance='b')
test = Testing(instance='b')

# Lista para acumular todos los registros aplanados
all_sales = []

# Recorrer mes a mes desde enero 2024 hasta diciembre 2025
for year in [2024, 2025]:
    for month in range(1, 13):
        # Calcular primer y último día del mes
        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])

        fecha_desde = first_day.strftime("%Y-%m-%d")
        fecha_hasta = last_day.strftime("%Y-%m-%d")

        print(f"Obteniendo ventas de {fecha_desde} a {fecha_hasta}...")

        try:
            data = chess_client.get_sales(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                detallado=True,
                empresas="1",
            )

            if data:
                # Aplanar ventas -> una fila por cada línea de venta
                flat_data = test._flatten_sales(data)
                all_sales.extend(flat_data)
                print(f"  -> {len(data)} ventas, {len(flat_data)} líneas")
            else:
                print(f"  -> Sin datos")

        except Exception as e:
            print(f"  -> Error: {e}")

# Crear DataFrame y exportar a CSV
if all_sales:
    df_total = pd.DataFrame(all_sales)
    df_total.to_csv('ventas_2024_2025.csv', index=False)
    print(f"\nExportado ventas_2024_2025.csv con {len(df_total)} líneas totales")
else:
    print("\nNo se obtuvieron datos para exportar")
