import logging

import numpy as np
from src.endpoints import Endpoints
import pandas as pd
import os
from dotenv import load_dotenv
from src.logger import get_logger

logger = get_logger(__name__, level=logging.DEBUG)

class StockData:
    def __init__(self, endpoint):

        self.data_dir = os.path.abspath(os.path.join((os.getcwd()), "data"))
        self.endpoint = endpoint
        self.stock = pd.DataFrame()
        logger.info("StockData initialized")
        logger.debug("Endpoint: %s", endpoint)

    def load_extra_data(
        self,
        df_deposits_path: str,
        df_bloat_articles_path: str,
        df_categories_path: str,
        deposits_col: str = "Deposito",
        bloat_articles_id_col: str = "CODIGO",
        bloat_articles_col_flag: str = "SIRVE",
        categories_id_col: str = "CODIGO",
        categories_col: str = "GENERICO"
    ) -> None:
        """
        Loads and processes additional data required for stock management, including deposits, bloat articles, and categories.
        Args:
            df_deposits_path (str): Path to the CSV file containing deposit information. Relation id/description
            df_bloat_articles_path (str): Path to the Excel file containing bloat articles information.
            df_categories_path (str): Path to the Excel file containing article categories.
            deposits_col (str, optional): Name of the column in the deposits file to be used as the deposit ID. Defaults to "Deposito".
            bloat_articles_col (str, optional): Name of the column in the bloat articles file to be used as the article ID. Defaults to "CODIGO".
            categories_col (str, optional): Name of the column in the categories file to be used as the article ID. Defaults to "CODIGO".
        Side Effects:
            Loads the data from the specified files and assigns processed DataFrames to the instance attributes:
                - self.df_deposits
                - self.df_bloat_articles
                - self.df_categories
            Renames relevant columns for consistency across DataFrames.
        """
        # Load deposits and rename column
        self.df_deposits = pd.read_csv(df_deposits_path, sep=";")
        self.df_deposits.rename(
            columns={deposits_col: 'idDeposito'}, inplace=True)

        # Load bloat articles and rename column
        self.df_bloat_articles = pd.read_csv(df_bloat_articles_path, sep=";")
        self.df_bloat_articles = self.df_bloat_articles[[bloat_articles_id_col, 'SIRVE']]
        self.df_bloat_articles.rename(columns={bloat_articles_id_col: 'idArticulo'}, inplace=True)

        # Load categories and rename column
        self.df_categories = pd.read_csv(df_categories_path, sep=";")
        self.df_categories.rename(
            columns={categories_id_col: 'idArticulo'}, inplace=True)
        self.categories_col = categories_col

        print("df_deposits")
        print(self.df_deposits.head())
        print("df_bloat_articles")
        print(self.df_bloat_articles.head())
        print("df_categories")
        print(self.df_categories.head())

    def transform_data(self) -> None:
        #Add deposit description and branch description
        art_test = 4220

        logger.debug("Stocks not transformed")
        mask = art_test in self.stock['idArticulo'].values
        logger.debug(f"If Article: {art_test} in stock?: {mask}" )

        self.stock = pd.merge(
            self.stock,
            self.df_deposits,
            on='idDeposito',
            how='left'
        ).reset_index()

        logger.debug("Stock merged with deposists")
        mask = art_test in self.stock['idArticulo'].values
        logger.debug(f"If Article: {art_test} in stock?: {mask}" )
        print(len(self.stock['idArticulo'].unique()), "articles in stock")

        #Delete bloat articles
        self.stock = self.stock[~self.stock['idArticulo'].isin(
            self.df_bloat_articles["idArticulo"])]
 
        # Add categorization
        self.stock = pd.merge(
            self.stock,
            self.df_categories[['idArticulo', 'GENERICO']],
            on='idArticulo',
            how='left'
        )
        
        logger.debug("Stock merged with categories")
        mask = art_test in self.stock['idArticulo'].values
        logger.debug(f"If Article: {art_test} in stock?: {mask}" )
        print(len(self.stock['idArticulo'].unique()), "articles in stock")
        # Order by Sucursal
        self.stock.sort_values(by="Sucursal", inplace=True)

        logger.debug("Stock sorted by Sucursal")
        mask = art_test in self.stock['idArticulo'].values
        logger.debug(f"If Article: {art_test} in stock?: {mask}" )
        print(len(self.stock['idArticulo'].unique()), "articles in stock")

        self.stock.to_excel(os.path.join(r"C:\Users\nahuel\Desktop\chesserp-api-main\data" + r"\stock_crudo.xlsx"), index=False)
        # Pivot Stock, columns by Sucursal
        self.stock = self.stock.pivot_table(
            values='cantBultos',
            index=['idArticulo', 'dsArticulo', 'GENERICO'],
            columns='Sucursal',
            aggfunc='sum',
        ).reset_index()
        
        logger.debug("Stock pivoted")
        mask = art_test in self.stock['idArticulo'].values
        logger.debug(f"If Article: {art_test} in stock?: {mask}" )
        print(len(self.stock['idArticulo'].unique()), "articles in stock")
        self.stock['MARCA'] = np.nan

    def get_stock_default(self) -> pd.DataFrame:
        self.stock = self.__to_df(self.endpoint.get_stock())
        return self.stock

    def __to_df(self, dic: dict) -> pd.DataFrame:
        columns = ["idDeposito", "idArticulo",
                   "dsArticulo", "cantBultos", "cantUnidades"]
        df = pd.DataFrame(dic['dsStockFisicoApi']['dsStock'])[columns]
        return df

    def get_stock(self, date: str, idDep: str) -> pd.DataFrame:
        self.stock = self.__to_df(self.endpoint.get_stock(date, idDep))
        return self.stock

    def get_stocks(self) -> pd.DataFrame:
        list_ = []
        if self.df_deposits.empty:
            logger.error("Deposits DataFrame is empty. Please load deposits data first.")
            return pd.DataFrame()

        for index, row in self.df_deposits.iterrows():
            list_.append(self.__to_df(
                self.endpoint.get_stock(idDeposito=row['idDeposito'])))
            logger.info("Fetching stock data for each deposit..." + str(row["idDeposito"]))

        self.stock = pd.concat(list_, ignore_index=True)

        return self.stock

    def to_excel(self, name: str = "stock") -> None:
        self.stock.to_excel(os.path.join(self.data_dir, f"{name}.xlsx"))

    def to_csv(self, name: str = "stock") -> None:
        self.stock.to_csv(os.path.join(self.data_dir, f"{name}.csv"), encoding='utf-8')


if __name__ == "__main__":
    load_dotenv()
    endp = Endpoints(os.getenv("API_URL_S"), os.getenv(
        "USERNAME_S"), os.getenv("PASSWORD_S"))
    endp.login()
    stock = StockData(endp)
    stock.get_stocks()
    stock.to_excel()
