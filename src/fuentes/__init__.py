"""Módulo de fuentes de datos externas."""

from src.fuentes.base import FuenteBase
from src.fuentes.metadatos import Metadatos
from src.fuentes.normalizacion import (
    normalizar_serie,
    detectar_duplicados,
    detectar_faltantes,
    resumen_calidad,
)
from src.fuentes.world_bank import BancoMundial, INDICADORES, PAISES
from src.fuentes.banxico import Banxico, SERIES

__all__ = [
    "FuenteBase",
    "Metadatos",
    "normalizar_serie",
    "detectar_duplicados",
    "detectar_faltantes",
    "resumen_calidad",
    "BancoMundial",
    "INDICADORES",
    "PAISES",
    "Banxico",
    "SERIES",
]