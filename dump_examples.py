"""
Genera ejemplos JSON de cada endpoint del ChessClient y ChessWebClient.
Usa la API de services (0.2.0).

Uso:
    python dump_examples.py --prefix EMPRESA1_
    python dump_examples.py --prefix EMPRESA1_ --outdir data/examples
    python dump_examples.py --prefix EMPRESA1_ --only sales,stock
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from chesserp.client import ChessClient
from chesserp.web_client import ChessWebClient


def truncate(data, max_items=3):
    """Trunca listas largas a max_items elementos para que el ejemplo sea legible."""
    if isinstance(data, list):
        truncated = [truncate(item, max_items) for item in data[:max_items]]
        if len(data) > max_items:
            truncated.append(f"... ({len(data) - max_items} items más)")
        return truncated
    if isinstance(data, dict):
        return {k: truncate(v, max_items) for k, v in data.items()}
    return data


def save(outdir: Path, name: str, data):
    """Guarda JSON raw y versión truncada."""
    outdir.mkdir(parents=True, exist_ok=True)

    full_path = outdir / f"{name}_full.json"
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"  [full]     {full_path} ({full_path.stat().st_size:,} bytes)")

    trunc_path = outdir / f"{name}.json"
    with open(trunc_path, "w", encoding="utf-8") as f:
        json.dump(truncate(data), f, ensure_ascii=False, indent=2, default=str)
    print(f"  [example]  {trunc_path}")


def dump_sales(client, outdir):
    print("\n--- sales (1 lote) ---")
    hoy = datetime.now()
    hace_7 = hoy - timedelta(days=7)
    data = client.sales.get_raw(
        fecha_desde=hace_7.strftime("%Y-%m-%d"),
        fecha_hasta=hoy.strftime("%Y-%m-%d"),
    )
    save(outdir, "sales", data)


def dump_articles(client, outdir):
    print("\n--- articles (1 lote) ---")
    data = client.inventory.get_articles_raw()
    save(outdir, "articles", data)


def dump_stock(client, outdir):
    print("\n--- stock (deposito 1) ---")
    data = client.inventory.get_stock_raw(id_deposito=1)
    save(outdir, "stock", data)


def dump_customers(client, outdir):
    print("\n--- customers (todos los lotes) ---")
    data = client.customers.get(raw=True)
    save(outdir, "customers", data)


def dump_orders(client, outdir):
    print("\n--- orders ---")
    hoy = datetime.now()
    data = client.orders.get_raw(
        fecha_pedido=hoy.strftime("%Y-%m-%d"),
    )
    save(outdir, "orders", data)


def dump_staff(client, outdir):
    print("\n--- staff ---")
    data = client.staff.get_raw()
    save(outdir, "staff", data)


def dump_routes(client, outdir):
    print("\n--- routes (todas las sucursales) ---")
    staff_data = client.staff.get_raw()
    staff_list = staff_data.get("PersonalComercial", {}).get("ePersCom", [])
    sucursales = sorted(set(s["idSucursal"] for s in staff_list))
    print(f"  Sucursales detectadas: {sucursales}")

    all_routes = {}
    for suc in sucursales:
        try:
            data = client.routes.get_raw(sucursal=suc)
            all_routes[f"sucursal_{suc}"] = data
            rutas = data.get("RutasVenta", {}).get("eRutasVenta", [])
            print(f"  Sucursal {suc}: {len(rutas)} rutas")
        except Exception as e:
            print(f"  Sucursal {suc}: ERROR - {e}")
            all_routes[f"sucursal_{suc}"] = {"error": str(e)}

    save(outdir, "routes", all_routes)


def dump_marketing(client, outdir):
    print("\n--- marketing ---")
    data = client.marketing.get_raw()
    save(outdir, "marketing", data)


def dump_price_lists(web_client, outdir):
    print("\n--- price_lists (web) ---")
    data = web_client.pricing.get_lists_raw()
    save(outdir, "price_lists", data)

    listas = data.get("eListaPrecios", []) if isinstance(data, dict) else data if isinstance(data, list) else []

    if listas:
        primera = listas[0]
        id_lista = primera.get("listaspre")
        id_vigencia = primera.get("idvigencia")
        if id_lista and id_vigencia:
            print(f"\n--- price_list_items (lista={id_lista}, vigencia={id_vigencia}) ---")
            items = web_client.pricing.get_items_raw(
                id_lista=id_lista,
                id_vigencia=id_vigencia,
            )
            save(outdir, "price_list_items", items)


ENDPOINTS = {
    "sales": dump_sales,
    "articles": dump_articles,
    "stock": dump_stock,
    "customers": dump_customers,
    "orders": dump_orders,
    "staff": dump_staff,
    "routes": dump_routes,
    "marketing": dump_marketing,
    "price_lists": dump_price_lists,
}


def main():
    parser = argparse.ArgumentParser(description="Dump JSON examples from ChessERP API")
    parser.add_argument("--prefix", required=True, help="Env var prefix (e.g. EMPRESA1_)")
    parser.add_argument("--outdir", default="data/examples", help="Output directory")
    parser.add_argument("--only", default="", help="Comma-separated endpoints to dump (default: all)")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    selected = [s.strip() for s in args.only.split(",") if s.strip()] if args.only else list(ENDPOINTS.keys())

    invalid = [s for s in selected if s not in ENDPOINTS]
    if invalid:
        print(f"Endpoints no válidos: {invalid}")
        print(f"Disponibles: {list(ENDPOINTS.keys())}")
        sys.exit(1)

    client = ChessClient.from_env(prefix=args.prefix)
    web_client = ChessWebClient.from_env(prefix=args.prefix)

    print(f"Dumping {len(selected)} endpoints to {outdir}/")
    print(f"API: {client.api_url}")

    for name in selected:
        fn = ENDPOINTS[name]
        try:
            if name == "price_lists":
                fn(web_client, outdir)
            else:
                fn(client, outdir)
        except Exception as e:
            print(f"\n  [ERROR] {name}: {e}")

    print(f"\nListo. Ejemplos en {outdir}/")


if __name__ == "__main__":
    main()
