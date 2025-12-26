"""
Configuración centralizada del proyecto ChessERP API
Utiliza Pydantic para validación automática de variables de entorno
"""
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, field_validator, Field, AnyHttpUrl, ConfigDict
from pydantic_settings import BaseSettings
from enum import Enum


class Environment(str, Enum):
    """Entornos de ejecución válidos"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Niveles de logging válidos"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ChessInstanceConfig(BaseSettings):
    """Configuración para una instancia de Chess ERP"""

    api_url: AnyHttpUrl = Field(..., description="URL base de la API Chess")
    username: str = Field(..., min_length=1, description="Usuario para autenticación")
    password: str = Field(..., min_length=1, description="Contraseña para autenticación")

    # Configuración de timeouts y reintentos
    timeout: int = Field(default=30, ge=1, le=300, description="Timeout en segundos")
    max_retries: int = Field(default=3, ge=0, le=10, description="Máximo número de reintentos")

    @field_validator('api_url')
    def validate_api_url(cls, v):
        """Valida que la URL termine sin barra final"""
        return str(v).rstrip('/')


class PathConfig(BaseSettings):
    """Configuración de rutas del proyecto"""

    project_root: Path = Field(default_factory=lambda:Path(__file__).parent.parent.parent)
    data_dir: str = Field(default="data", description="Directorio de datos")
    logs_dir: str = Field(default="logs", description="Directorio de logs")

    @property
    def data_path(self) -> Path:
        return self.project_root / self.data_dir

    @property
    def original_data_path(self) -> Path:
        return self.data_path / "original"

    @property
    def processed_data_path(self) -> Path:
        return self.data_path / "processed"

    def create_directories(self) -> None:
        """Crea todos los directorios necesarios"""
        for path in [self.data_path, self.original_data_path, self.processed_data_path]:
            path.mkdir(parents=True, exist_ok=True)


class ETLConfig(BaseSettings):
    """Configuración específica del ETL"""

    chunk_size: int = Field(default=1000, ge=100, description="Tamaño de chunk paraprocesamiento")
    csv_separator: str = Field(default=";", description="Separador para archivos CSV")
    csv_encoding: str = Field(default="utf-8", description="Encoding para archivos CSV")

    # Columnas importantes movidas desde endpoints.py
    important_columns: List[str] = Field(
        default=[
            "Descripcion Empresa", "Descripcion Comprobante", "Letra",
            "Codigo de Articulo", "Descripcion de Articulo", "MARCA",
            "GENERICO", "Bultos Total", "Sucursal", "Fecha Comprobante"
            # ... resto de columnas
        ]
    )


class Settings(BaseSettings):
    """Configuración principal de la aplicación"""

    # Configuración general
    app_name: str = Field(default="ChessERP API", description="Nombre de la aplicación")
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)

    # Configuración de logging
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_file: str = Field(default="chesserp.log")

    # Instancias de Chess ERP
    chess_s_api_url: AnyHttpUrl = Field(alias="API_URL_S")
    chess_s_username: str = Field(alias="USERNAME_S")
    chess_s_password: str = Field(alias="PASSWORD_S")

    chess_b_api_url: AnyHttpUrl = Field(alias="API_URL_B")
    chess_b_username: str = Field(alias="USERNAME_B")
    chess_b_password: str = Field(alias="PASSWORD_B")

    # API paths
    api_path: str = Field(default="/web/api/chess/v1/", description="Path base de la API")
    api_path_login: str = Field(default="/web/api/chess/v1/auth/login", description="Path completo de login")

    @field_validator('api_path_login')
    def validate_api_path_login(cls, v):
        """Quita barra final del path de login para evitar redirects"""
        return v.rstrip('/')

    # Configuraciones embebidas
    paths: PathConfig = Field(default_factory=PathConfig)
    etl: ETLConfig = Field(default_factory=ETLConfig)

    @property
    def chess_s(self) -> ChessInstanceConfig:
        """Configuración para Chess S"""
        return ChessInstanceConfig(
            api_url=self.chess_s_api_url,
            username=self.chess_s_username,
            password=self.chess_s_password
        )

    @property
    def chess_b(self) -> ChessInstanceConfig:
        """Configuración para Chess B"""
        return ChessInstanceConfig(
            api_url=self.chess_b_api_url,
            username=self.chess_b_username,
            password=self.chess_b_password
        )

    def get_instance_config(self, instance_name: str) -> ChessInstanceConfig:
        """Obtiene configuración de una instancia específica"""
        if instance_name.lower() == 's':
            return self.chess_s
        elif instance_name.lower() == 'b':
            return self.chess_b
        else:
            raise ValueError(f"Instancia desconocida: {instance_name}")

    def setup_directories(self) -> None:
        """Configura todos los directorios necesarios"""
        self.paths.create_directories()


# Instancia global de configuración
settings = Settings()

def get_settings() -> Settings:
    """Factory function para obtener configuración"""
    return settings
