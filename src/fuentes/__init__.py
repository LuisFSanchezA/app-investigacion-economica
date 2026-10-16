"""Módulo de fuentes de datos externas."""

from src.fuentes.base import FuenteBase
from src.fuentes.metadatos import Metadatos
from src.fuentes.world_bank import BancoMundial, INDICADORES, PAISES

__all__ = [
    "FuenteBase",
    "Metadatos",
    "BancoMundial",
    "INDICADORES",
    "PAISES",
]