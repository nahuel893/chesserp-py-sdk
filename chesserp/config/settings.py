"""
Configuración opcional para ChessERP API.

NOTA: El ChessClient ya no requiere este módulo.
Puede recibir credenciales directamente o usar ChessClient.from_env().

Este módulo se mantiene para compatibilidad con código existente
y para configuración avanzada (logging, paths, etc).
"""
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class LogLevel(str, Enum):
    """Niveles de logging válidos"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class PathConfig(BaseModel):
    """Configuración de rutas del proyecto"""

    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: str = Field(default="data", description="Directorio de datos")
    logs_dir: str = Field(default="logs", description="Directorio de logs")

    @property
    def data_path(self) -> Path:
        return self.project_root / self.data_dir

    @property
    def logs_path(self) -> Path:
        return self.project_root / self.logs_dir

    def create_directories(self) -> None:
        """Crea todos los directorios necesarios"""
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)


class Settings(BaseModel):
    """
    Configuración opcional de la librería.

    El ChessClient NO requiere esta clase para funcionar.
    Se proporciona para configuración avanzada.
    """

    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_file: Optional[str] = Field(default=None)

    # Paths
    paths: PathConfig = Field(default_factory=PathConfig)

    # API paths (defaults de ChessERP)
    api_path: str = Field(default="/web/api/chess/v1/")
    login_path: str = Field(default="/web/api/chess/v1/auth/login")


# Instancia por defecto (lazy, no requiere .env)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Obtiene la configuración global (crea una si no existe)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
