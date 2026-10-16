"""Clase base para conectores de fuentes de datos.

Cada fuente (Banco Mundial, INEGI, Banxico, etc.) debe implementar esta
interfaz para que la interfaz de usuario pueda tratarlas de forma uniforme.
"""

from abc import ABC, abstractmethod

import pandas as pd

from src.fuentes.metadatos import Metadatos


class FuenteBase(ABC):
    """Interfaz común para todas las fuentes de datos."""

    @property
    @abstractmethod
    def nombre(self) -> str:
        """Nombre legible de la fuente. Ej: 'Banco Mundial'."""
        ...

    @abstractmethod
    def consultar(
        self,
        indicador: str,
        pais: str,
        periodo_inicio: int,
        periodo_fin: int,
    ) -> tuple[pd.DataFrame, Metadatos]:
        """Consulta una serie y devuelve (DataFrame, Metadatos)."""
        ...