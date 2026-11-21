"""Versiones cacheadas de las funciones de IA para la sección Tema.

Separado de asistente_tema.py para que los tests no dependan de Streamlit.
"""

import streamlit as st

from src.ai.asistente_tema import (
    generar_justificacion,
    generar_resumen_ejecutivo,
    sugerir_enunciado,
)


@st.cache_data(ttl=86400, show_spinner=False)
def sugerir_enunciado_cached(
    pregunta: str,
    objetivos: str = "",
    n_corpus: int = 0,
    datos: str = "",
    fenomeno: str = "",
    poblacion: str = "",
    periodo: str = "",
    espacio: str = "",
    variables: str = "",
) -> str:
    """Versión cacheada de sugerir_enunciado (24h)."""
    return sugerir_enunciado(
        pregunta=pregunta,
        objetivos=objetivos,
        n_corpus=n_corpus,
        datos=datos,
        fenomeno=fenomeno,
        poblacion=poblacion,
        periodo=periodo,
        espacio=espacio,
        variables=variables,
    )


@st.cache_data(ttl=86400, show_spinner=False)
def generar_justificacion_cached(
    pregunta: str,
    objetivos: str = "",
    n_corpus: int = 0,
    datos: str = "",
    fenomeno: str = "",
    poblacion: str = "",
    periodo: str = "",
    espacio: str = "",
    variables: str = "",
) -> str:
    """Versión cacheada de generar_justificacion (24h)."""
    return generar_justificacion(
        pregunta=pregunta,
        objetivos=objetivos,
        n_corpus=n_corpus,
        datos=datos,
        fenomeno=fenomeno,
        poblacion=poblacion,
        periodo=periodo,
        espacio=espacio,
        variables=variables,
    )


@st.cache_data(ttl=86400, show_spinner=False)
def generar_resumen_ejecutivo_cached(
    pregunta: str,
    enunciado: str,
    objetivos: str = "",
    n_corpus: int = 0,
    datos: str = "",
    fenomeno: str = "",
    poblacion: str = "",
    periodo: str = "",
    espacio: str = "",
    variables: str = "",
) -> str:
    """Versión cacheada de generar_resumen_ejecutivo (24h)."""
    return generar_resumen_ejecutivo(
        pregunta=pregunta,
        enunciado=enunciado,
        objetivos=objetivos,
        n_corpus=n_corpus,
        datos=datos,
        fenomeno=fenomeno,
        poblacion=poblacion,
        periodo=periodo,
        espacio=espacio,
        variables=variables,
    )