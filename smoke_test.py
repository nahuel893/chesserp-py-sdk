"""
Smoke test para validar todos los endpoints del ChessClient y ChessWebClient.
Usa la nueva API de services (0.2.0).

Uso:
    python smoke_test.py --prefix EMPRESA1_
    python smoke_test.py --prefix EMPRESA1_ --test sales
    python smoke_test.py --prefix EMPRESA1_ --test quick
    python smoke_test.py --prefix EMPRESA1_ --test pricing
"""

import argparse
from datetime import date, timedelta, datetime
from dotenv import load_dotenv

load_dotenv()

from chesserp.client import ChessClient
from chesserp.web_client import ChessWebClient
from chesserp.logger import setup_logger, get_logger

logger = setup_logger(log_file="smoke_test.log")


class SmokeTest:

    def __init__(self, prefix: str = ""):
        logger.info(f'{"SMOKE TEST — ChessERP SDK 0.2.0":=^60}')
        self.client = ChessClient.from_env(prefix=prefix)
        self.web_client = ChessWebClient.from_env(prefix=prefix)
        self.results = {}

    def _run(self, name, fn):
        logger.info(f'{"":─^60}')
        logger.info(f"TEST: {name}")
        start = datetime.now()
        try:
            result = fn()
            elapsed = (datetime.now() - start).total_seconds()
            count = len(result) if isinstance(result, (list, dict)) else "ok"
            logger.info(f"  OK — {count} registros en {elapsed:.2f}s")
            self.results[name] = ("OK", count, elapsed)
            return result
        except Exception as e:
            elapsed = (datetime.now() - start).total_seconds()
            logger.error(f"  FAIL — {e} ({elapsed:.2f}s)")
            self.results[name] = ("FAIL", str(e), elapsed)
            return None

    # ── Official API (ChessClient) ───────────────────────────────

    def sales(self):
        def _test():
            hace_7 = date.today() - timedelta(days=7)
            hoy = date.today()
            return self.client.sales.get(
                fecha_desde=hace_7.strftime("%Y-%m-%d"),
                fecha_hasta=hoy.strftime("%Y-%m-%d"),
            )
        return self._run("sales.get", _test)

    def sales_raw(self):
        def _test():
            hace_7 = date.today() - timedelta(days=7)
            hoy = date.today()
            return self.client.sales.get_raw(
                fecha_desde=hace_7.strftime("%Y-%m-%d"),
                fecha_hasta=hoy.strftime("%Y-%m-%d"),
            )
        return self._run("sales.get_raw", _test)

    def articles(self):
        return self._run("inventory.get_articles",
                         lambda: self.client.inventory.get_articles())

    def articles_raw(self):
        return self._run("inventory.get_articles_raw",
                         lambda: self.client.inventory.get_articles_raw())

    def stock(self):
        return self._run("inventory.get_stock",
                         lambda: self.client.inventory.get_stock(id_deposito=1))

    def stock_raw(self):
        return self._run("inventory.get_stock_raw",
                         lambda: self.client.inventory.get_stock_raw(id_deposito=1))

    def customers(self):
        return self._run("customers.get (1 lote)",
                         lambda: self.client.customers.get(nro_lote=1))

    def customers_raw(self):
        return self._run("customers.get_raw",
                         lambda: self.client.customers.get_raw())

    def orders(self):
        def _test():
            hoy = date.today().strftime("%Y-%m-%d")
            return self.client.orders.get(fecha_entrega=hoy)
        return self._run("orders.get", _test)

    def orders_raw(self):
        def _test():
            hoy = date.today().strftime("%Y-%m-%d")
            return self.client.orders.get_raw(fecha_entrega=hoy)
        return self._run("orders.get_raw", _test)

    def staff(self):
        return self._run("staff.get",
                         lambda: self.client.staff.get())

    def staff_raw(self):
        return self._run("staff.get_raw",
                         lambda: self.client.staff.get_raw())

    def routes(self):
        return self._run("routes.get (suc=1)",
                         lambda: self.client.routes.get(sucursal=1))

    def routes_raw(self):
        return self._run("routes.get_raw (suc=1)",
                         lambda: self.client.routes.get_raw(sucursal=1))

    def marketing(self):
        return self._run("marketing.get",
                         lambda: self.client.marketing.get())

    def marketing_raw(self):
        return self._run("marketing.get_raw",
                         lambda: self.client.marketing.get_raw())

    # ── Web API (ChessWebClient) ─────────────────────────────────

    def price_lists(self):
        return self._run("pricing.get_lists",
                         lambda: self.web_client.pricing.get_lists())

    def price_lists_raw(self):
        return self._run("pricing.get_lists_raw",
                         lambda: self.web_client.pricing.get_lists_raw())

    def price_items(self):
        def _test():
            listas = self.web_client.pricing.get_lists()
            if not listas:
                return []
            primera = listas[0]
            return self.web_client.pricing.get_items(
                id_lista=primera.id_lista,
                id_vigencia=primera.id_vigencia,
            )
        return self._run("pricing.get_items", _test)

    # ── Runners ──────────────────────────────────────────────────

    def run_all(self):
        self.sales()
        self.sales_raw()
        self.articles()
        self.articles_raw()
        self.stock()
        self.stock_raw()
        self.customers()
        self.customers_raw()
        self.orders()
        self.orders_raw()
        self.staff()
        self.staff_raw()
        self.routes()
        self.routes_raw()
        self.marketing()
        self.marketing_raw()
        self.price_lists()
        self.price_lists_raw()
        self.price_items()
        self._summary()

    def run_quick(self):
        """Endpoints no paginados, rápido."""
        self.stock()
        self.staff()
        self.routes()
        self.marketing()
        self.price_lists()
        self._summary()

    def run_parsed(self):
        """Solo métodos parsed (no raw)."""
        self.sales()
        self.articles()
        self.stock()
        self.customers()
        self.orders()
        self.staff()
        self.routes()
        self.marketing()
        self.price_lists()
        self.price_items()
        self._summary()

    def run_pricing(self):
        """Solo endpoints de pricing (web client)."""
        self.price_lists()
        self.price_lists_raw()
        self.price_items()
        self._summary()

    def _summary(self):
        logger.info(f'\n{"":═^60}')
        logger.info(f'{"RESUMEN":^60}')
        logger.info(f'{"":═^60}')

        ok = sum(1 for s, _, _ in self.results.values() if s == "OK")
        fail = sum(1 for s, _, _ in self.results.values() if s == "FAIL")
        total_time = sum(t for _, _, t in self.results.values())

        for name, (status, detail, elapsed) in self.results.items():
            icon = "OK" if status == "OK" else "FAIL"
            logger.info(f"  [{icon:>4}] {name:<35} {detail!s:>10}  ({elapsed:.2f}s)")

        logger.info(f'{"":─^60}')
        logger.info(f"  Total: {len(self.results)} | OK: {ok} | FAIL: {fail} | Tiempo: {total_time:.2f}s")
        logger.info(f'{"":═^60}')


TESTS = [
    "all", "quick", "parsed", "pricing",
    "sales", "articles", "stock", "customers",
    "orders", "staff", "routes", "marketing",
    "price_lists", "price_items",
]


def main():
    parser = argparse.ArgumentParser(description="Smoke test — ChessERP SDK 0.2.0")
    parser.add_argument("--prefix", "-p", default="", help="Env var prefix")
    parser.add_argument("--test", "-t", default="all", choices=TESTS, help="Test to run")
    args = parser.parse_args()

    tester = SmokeTest(prefix=args.prefix)

    if args.test == "all":
        tester.run_all()
    elif args.test == "quick":
        tester.run_quick()
    elif args.test == "parsed":
        tester.run_parsed()
    elif args.test == "pricing":
        tester.run_pricing()
    else:
        method = getattr(tester, args.test, None)
        if method:
            method()
            tester._summary()
        else:
            logger.error(f"Test '{args.test}' no encontrado")


if __name__ == "__main__":
    main()
