import logging
import os
import pandas as pd
import numpy as np
from typing import List

from src.client import ChessClient
from src.models.inventory import StockFisico
from src.logger import get_logger

logger = get_logger(__name__, level=logging.DEBUG)

class StockData:
    def __init__(self, client: ChessClient):
        self.data_dir = os.path.abspath(os.path.join((os.getcwd()), "data"))
        self.client = client
        self.stock = pd.DataFrame()
        
        # Dataframes auxiliares
        self.df_deposits = pd.DataFrame()
        self.df_bloat_articles = pd.DataFrame()
        self.df_categories = pd.DataFrame()
        
        logger.info("StockData initialized")

    def load_extra_data(
        self,
        df_deposits_path: str,
        df_bloat_articles_path: str,
        df_categories_path: str,
        deposits_col: str = "Deposito",
        bloat_articles_id_col: str = "CODIGO",
        categories_id_col: str = "CODIGO",
        categories_col: str = "GENERICO"
    ) -> None:
        """
        Loads and processes additional data required for stock management.
        """
        # Load deposits
        self.df_deposits = pd.read_csv(df_deposits_path, sep=";")
        self.df_deposits.rename(columns={deposits_col: 'idDeposito'}, inplace=True)

        # Load bloat articles
        self.df_bloat_articles = pd.read_csv(df_bloat_articles_path, sep=";")
        self.df_bloat_articles = self.df_bloat_articles[[bloat_articles_id_col, 'SIRVE']]
        self.df_bloat_articles.rename(columns={bloat_articles_id_col: 'idArticulo'}, inplace=True)

        # Load categories
        self.df_categories = pd.read_csv(df_categories_path, sep=";")
        self.df_categories.rename(columns={categories_id_col: 'idArticulo'}, inplace=True)
        self.categories_col = categories_col

        logger.debug("Extra data loaded:")
        logger.debug(f"Deposits: {self.df_deposits.head()}")
        logger.debug(f"Bloat Articles: {self.df_bloat_articles.head()}")
        logger.debug(f"Categories: {self.df_categories.head()}")

    def transform_data(self) -> None:
        """
        Aplica transformaciones, merge con catálogos y pivoteo.
        """
        if self.stock.empty:
            logger.warning("Stock DataFrame is empty. Cannot transform.")
            return

        art_test = 4220
        logger.debug(f"Checking test article {art_test} presence before transform: {art_test in self.stock['idArticulo'].values}")

        # Merge Deposits
        if not self.df_deposits.empty:
            self.stock = pd.merge(
                self.stock,
                self.df_deposits,
                on='idDeposito',
                how='left'
            )
        else:
            logger.warning("Deposits data not loaded. Skipping merge.")

        # Filter Bloat Articles
        if not self.df_bloat_articles.empty:
            self.stock = self.stock[~self.stock['idArticulo'].isin(
                self.df_bloat_articles["idArticulo"])]

        # Merge Categories
        if not self.df_categories.empty:
            self.stock = pd.merge(
                self.stock,
                self.df_categories[['idArticulo', 'GENERICO']],
                on='idArticulo',
                how='left'
            )

        # Order by Sucursal if exists (it comes from deposits merge)
        if "Sucursal" in self.stock.columns:
            self.stock.sort_values(by="Sucursal", inplace=True)
        
        # Export raw data for debug
        os.makedirs(self.data_dir, exist_ok=True)
        self.stock.to_excel(os.path.join(self.data_dir, "stock_crudo.xlsx"), index=False)

        # Pivot
        index_cols = ['idArticulo', 'dsArticulo']
        if 'GENERICO' in self.stock.columns:
            index_cols.append('GENERICO')
            
        if 'Sucursal' in self.stock.columns:
            self.stock = self.stock.pivot_table(
                values='cantBultos',
                index=index_cols,
                columns='Sucursal',
                aggfunc='sum',
            ).reset_index()
            
            self.stock['MARCA'] = np.nan
            logger.info("Stock pivoted successfully.")
        else:
            logger.warning("'Sucursal' column missing. Skipping pivot.")

    def _pydantic_to_df(self, stock_list: List[StockFisico]) -> pd.DataFrame:
        """Converts list of Pydantic models to DataFrame."""
        if not stock_list:
            return pd.DataFrame(columns=["idDeposito", "idArticulo", "dsArticulo", "cantBultos", "cantUnidades"])
            
        data = [item.dict() for item in stock_list]
        df = pd.DataFrame(data)
        return df[["idDeposito", "idArticulo", "dsArticulo", "cantBultos", "cantUnidades"]]

    def get_stock(self, id_deposito: int, fecha: str = "") -> pd.DataFrame:
        """Gets stock for a single deposit."""
        stock_list = self.client.get_stock(id_deposito=id_deposito, fecha=fecha)
        self.stock = self._pydantic_to_df(stock_list)
        return self.stock

    def get_stocks_all_deposits(self) -> pd.DataFrame:
        """Iterates over loaded deposits and fetches stock for each."""
        if self.df_deposits.empty:
            logger.error("Deposits DataFrame is empty. Please load deposits data first.")
            return pd.DataFrame()

        frames = []
        for _, row in self.df_deposits.iterrows():
            id_dep = row['idDeposito']
            logger.info(f"Fetching stock for deposit {id_dep}...")
            
            try:
                stock_list = self.client.get_stock(id_deposito=int(id_dep))
                df_dep = self._pydantic_to_df(stock_list)
                frames.append(df_dep)
            except Exception as e:
                logger.error(f"Error fetching stock for deposit {id_dep}: {e}")

        if frames:
            self.stock = pd.concat(frames, ignore_index=True)
        else:
            self.stock = pd.DataFrame()
            
        return self.stock

    def to_excel(self, name: str = "stock") -> None:
        path = os.path.join(self.data_dir, f"{name}.xlsx")
        self.stock.to_excel(path)
        logger.info(f"Saved stock to {path}")

    def to_csv(self, name: str = "stock") -> None:
        path = os.path.join(self.data_dir, f"{name}.csv")
        self.stock.to_csv(path, encoding='utf-8')
        logger.info(f"Saved stock to {path}")

if __name__ == "__main__":
    # Ejemplo de uso
    try:
        # Inicializar cliente (toma credenciales de .env)
        client = ChessClient(instance='s') 
        stock_manager = StockData(client)
        
        # Cargar metadatos (paths ficticios, ajustar según entorno real)
        # stock_manager.load_extra_data(...) 
        
        # Obtener stock de un depósito de prueba
        df = stock_manager.get_stock(id_deposito=1)
        print(f"Stock obtained: {len(df)} rows")
        
    except Exception as e:
        logger.error(f"Execution failed: {e}")