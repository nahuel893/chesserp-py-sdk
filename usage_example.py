import os
import sys
import logging
from dotenv import load_dotenv
from chesserp.client import ChessClient
from chesserp.exceptions import ChessError

# Configurar log para ver info útil pero no saturar
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

def print_separator(title):
    print(f"\n{'-'*60}")
    print(f" {title.upper()}")
    print(f"{'-'*60}")

def wait_for_enter():
    input("\nPresione ENTER para continuar...")

# --- Funciones de Prueba ---

def test_sales(client):
    print_separator("Prueba de Ventas")
    print("Obteniendo ventas del 2025-10-01 al 2025-10-05...")
    try:
        ventas = client.get_sales(
            fecha_desde="2025-10-01",
            fecha_hasta="2025-10-05",
            detallado=True
        )
        print(f"✅ Éxito: Se recuperaron {len(ventas)} comprobantes.")
        if ventas:
            v = ventas[0]
            print(f"   Detalle del primero: {v.letra} {v.serie}-{v.nro_doc}")
            print(f"   Cliente: {v.nombre_cliente}")
            if v.lines:
                print(f"   Items ({len(v.lines)}): {v.lines[0].ds_articulo} x {v.lines[0].cantidad_solicitada}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_stock(client):
    print_separator("Prueba de Stock Físico")
    deposito_id = input("Ingrese ID Depósito (default 1): ") or "1"
    try:
        stock = client.get_stock(id_deposito=int(deposito_id), frescura=False)
        print(f"✅ Éxito: Se recuperaron {len(stock)} registros.")
        if stock:
            s = stock[0]
            print(f"   Ejemplo: {s.ds_articulo} (ID: {s.id_articulo}) - Cant: {s.cant_bultos}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_articles(client):
    print_separator("Prueba de Artículos")
    try:
        print("Trayendo lote 0 (primeros registros)...")
        articulos = client.get_articles(nro_lote=0)
        print(f"✅ Éxito: Se recuperaron {len(articulos)} artículos.")
        if articulos:
            a = articulos[0]
            print(f"   Ejemplo: {a.des_articulo} (ID: {a.id_articulo}) - Bulto: {a.unidades_bulto}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_customers(client):
    print_separator("Prueba de Clientes")
    try:
        print("Trayendo lote 0 (primeros registros)...")
        clientes = client.get_customers(nro_lote=0)
        print(f"✅ Éxito: Se recuperaron {len(clientes)} clientes.")
        if clientes:
            c = clientes[0]
            print(f"   Ejemplo: {c.razon_social} (ID: {c.id_cliente})")
            print(f"   Ubicación: {c.des_localidad}, {c.des_provincia}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_orders(client):
    print_separator("Prueba de Pedidos")
    fecha = input("Ingrese fecha de pedido (YYYY-MM-DD) [default 2025-10-01]: ") or "2025-10-01"
    try:
        pedidos = client.get_orders(fecha_pedido=fecha)
        print(f"✅ Éxito: Se recuperaron {len(pedidos)} pedidos para la fecha {fecha}.")
        if pedidos:
            p = pedidos[0]
            print(f"   Ejemplo: Pedido #{p.id_pedido} | Cliente: {p.id_cliente}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_staff(client):
    print_separator("Prueba de Personal Comercial")
    try:
        personal = client.get_staff()
        print(f"✅ Éxito: Se recuperaron {len(personal)} miembros.")
        if personal:
            p = personal[0]
            print(f"   Ejemplo: {p.des_personal} - {p.cargo}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_routes(client):
    print_separator("Prueba de Rutas de Venta")
    try:
        rutas = client.get_routes()
        print(f"✅ Éxito: Se recuperaron {len(rutas)} rutas.")
        if rutas:
            r = rutas[0]
            print(f"   Ejemplo: {r.des_ruta} (ID: {r.id_ruta})")
            print(f"   Vendedor asignado: {r.des_personal}")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_marketing(client):
    print_separator("Prueba de Jerarquía Marketing")
    try:
        mkt = client.get_marketing_hierarchy()
        print(f"✅ Éxito: Se recuperaron {len(mkt)} segmentos.")
        if mkt:
            s = mkt[0]
            print(f"   Segmento: {s.des_segmento_mkt}")
            if s.canales_mkt:
                print(f"   Canales asociados: {len(s.canales_mkt)}")
    except Exception as e:
        print(f"❌ Error: {e}")

# --- Menú Principal ---

def main():
    load_dotenv()

    print("\nInicializando cliente ChessERP...")
    try:
        # Crear cliente desde variables de entorno
        # Requiere: API_URL, USERNAME, PASSWORD en .env
        client = ChessClient.from_env()
        client.login()
        print("✅ Login exitoso.\n")
    except Exception as e:
        print(f"❌ Error crítico al loguear: {e}")
        return

    while True:
        print_separator("MENÚ DE PRUEBAS CHESS ERP")
        print("1. Consultar Ventas")
        print("2. Consultar Stock Físico")
        print("3. Consultar Catálogo de Artículos")
        print("4. Consultar Clientes")
        print("5. Consultar Pedidos")
        print("6. Consultar Personal Comercial")
        print("7. Consultar Rutas de Venta")
        print("8. Consultar Jerarquía Marketing")
        print("9. Ejecutar TODAS las pruebas")
        print("0. Salir")
        
        choice = input("\nSeleccione una opción: ")
        
        if choice == '1':
            test_sales(client)
        elif choice == '2':
            test_stock(client)
        elif choice == '3':
            test_articles(client)
        elif choice == '4':
            test_customers(client)
        elif choice == '5':
            test_orders(client)
        elif choice == '6':
            test_staff(client)
        elif choice == '7':
            test_routes(client)
        elif choice == '8':
            test_marketing(client)
        elif choice == '9':
            test_sales(client)
            test_stock(client)
            test_articles(client)
            test_customers(client)
            test_orders(client)
            test_staff(client)
            test_routes(client)
            test_marketing(client)
        elif choice == '0':
            print("\nAdiós!")
            break
        else:
            print("\nOpción no válida.")
        
        wait_for_enter()

if __name__ == "__main__":
    main()
