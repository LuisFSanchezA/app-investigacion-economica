"""Conector para tesis académicas.

Estrategia:
1. OpenAlex con `type:dissertation` + `language:es` + keywords de economía.
2. Enlaces prefabricados a TesiuNAM, Dialnet y RIUD para búsqueda manual.

Inspirado en NodOS (https://nodosmap.com), pero adaptado a Streamlit:
no hay mapa semántico ni embeddings, solo búsqueda y enlaces.
"""

from __future__ import annotations

from urllib.parse import quote

import pandas as pd

from src.fuentes.metadatos import Metadatos
from src.fuentes.openalex import OpenAlex


# ---------------------------------------------------------------------------
# Catálogos de enlaces externos
# ---------------------------------------------------------------------------

REPOSITORIOS = {
    "TesiuNAM": {
        "url_base": "https://tesiunam.dgb.unam.mx/F",
        "plantilla": (
            "?func=find-b&find_code=WRD&request={query}"
            "&local_base=TES01"
        ),
        "descripcion": "Tesis de la UNAM (licenciatura, maestría, doctorado)",
    },
    "Dialnet": {
        "url_base": "https://dialnet.unirioja.es/buscar/tesis",
        "plantilla": "?querys-DX={query}",
        "descripcion": "Tesis de universidades de habla hispana",
    },
    "RIUD": {
        "url_base": "https://riud.conacyt.mx",
        "plantilla": "/buscar?q={query}",
        "descripcion": "Repositorio Nacional (CONACYT)",
    },
}


# ---------------------------------------------------------------------------
# Conector
# ---------------------------------------------------------------------------

class Tesis:
    """Conector para tesis académicas.

    Combina OpenAlex (búsqueda en vivo) con enlaces prefabricados
    a repositorios especializados (TesiuNAM, Dialnet, RIUD).
    """

    @property
    def nombre(self) -> str:
        return "Tesis (OpenAlex + repositorios)"

    def buscar(
        self,
        keywords: list[str],
        desde: int | None = None,
        hasta: int | None = None,
        limite: int = 100,
    ) -> tuple[pd.DataFrame, Metadatos]:
        """Busca tesis en OpenAlex.

        Parámetros
        ----------
        keywords : list[str]
            Palabras clave de búsqueda.
        desde, hasta : int, opcional
            Rango de años.
        limite : int
            Máximo de resultados (default 100).

        Devuelve
        -------
        tuple[pd.DataFrame, Metadatos]
            DataFrame con columnas de tesis + metadatos de la consulta.
        """
        if not keywords or not [k for k in keywords if k.strip()]:
            raise ValueError("Debes proporcionar al menos una palabra clave.")

        # Delegar en OpenAlex, forzando type:dissertation
        conector = OpenAlex()
        df, meta = conector.buscar(
            keywords=keywords,
            desde=desde,
            hasta=hasta,
            tipos=["dissertation"],
            idiomas=["es", "en", "pt"],
            limite=limite,
        )

        # Añadir columnas específicas de tesis
        df = df.copy()
        df["nivel"] = df["tipo"].apply(self._inferir_nivel)
        df["enlace_tesunam"] = df["titulo"].apply(
            lambda t: self._enlace_repositorio("TesiuNAM", t)
        )
        df["enlace_dialnet"] = df["titulo"].apply(
            lambda t: self._enlace_repositorio("Dialnet", t)
        )
        df["enlace_riud"] = df["titulo"].apply(
            lambda t: self._enlace_repositorio("RIUD", t)
        )

        # Metadatos extendidos
        meta.notas = (
            f"Tesis encontradas en OpenAlex: {len(df)}. "
            f"Filtros: type=dissertation, idiomas=es/en/pt. "
            f"Enlaces a TesiuNAM, Dialnet y RIUD generados a partir del título."
        )

        return df, meta

    # ------------------------------------------------------------------
    # Utilidades públicas
    # ------------------------------------------------------------------

    @staticmethod
    def _inferir_nivel(tipo: str) -> str:
        """Infiere el nivel (licenciatura/maestría/doctorado) desde el tipo.

        OpenAlex usa `dissertation` para todos los niveles. No hay forma
        fiable de distinguir desde el título. Devolvemos "Tesis" genérico.
        """
        return "Tesis"

    @staticmethod
    def _enlace_repositorio(nombre: str, titulo: str) -> str:
        """Genera un enlace prefabricado a un repositorio.

        Limpia el título (quita comillas, puntos, etc.) y lo URL-encodea.
        """
        if not titulo or not isinstance(titulo, str):
            return ""
        # Limpiar: quitar comillas, puntos suspensivos, etc.
        limpio = titulo.strip().strip('"').strip("'")
        if len(limpio) > 80:
            limpio = limpio[:80].rsplit(" ", 1)[0]
        query = quote(limpio)
        repo = REPOSITORIOS.get(nombre)
        if not repo:
            return ""
        return f"{repo['url_base']}{repo['plantilla'].format(query=query)}"

    @staticmethod
    def enlaces_prefabricados(keywords: list[str]) -> dict[str, str]:
        """Genera enlaces de búsqueda para cada repositorio.

        Útil para mostrar botones "Buscar en TesiuNAM" con la query ya armada.

        Devuelve dict nombre_repo -> url.
        """
        if not keywords:
            return {}
        query = quote(" ".join(k for k in keywords if k.strip()))
        enlaces = {}
        for nombre, repo in REPOSITORIOS.items():
            enlaces[nombre] = f"{repo['url_base']}{repo['plantilla'].format(query=query)}"
        return enlaces

    @staticmethod
    def descripcion_repositorios() -> dict[str, str]:
        """Devuelve la descripción de cada repositorio."""
        return {nombre: repo["descripcion"] for nombre, repo in REPOSITORIOS.items()}