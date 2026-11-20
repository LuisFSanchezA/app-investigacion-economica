"""Módulo de fuentes de datos externas."""

from src.fuentes.base import FuenteBase
from src.fuentes.metadatos import Metadatos
from src.fuentes.normalizacion import (
    normalizar_serie,
    normalizar_serie_fechas,
    detectar_duplicados,
    detectar_faltantes,
    resumen_calidad,
)
from src.fuentes.world_bank import BancoMundial, INDICADORES, PAISES
from src.fuentes.banxico import Banxico, SERIES
from src.fuentes.openalex import OpenAlex
from src.fuentes.tesis import Tesis
from src.fuentes.inegi import INEGI, INDICADORES_INEGI

__all__ = [
    "FuenteBase",
    "Metadatos",
    "normalizar_serie",
    "normalizar_serie_fechas",
    "detectar_duplicados",
    "detectar_faltantes",
    "resumen_calidad",
    "BancoMundial",
    "INDICADORES",
    "PAISES",
    "Banxico",
    "SERIES",
    "OpenAlex",
    "Tesis",
    "INEGI",
    "INDICADORES_INEGI",
]