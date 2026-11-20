"""Versiones cacheadas de las funciones de IA para la UI."""

import json

import pandas as pd
import streamlit as st

from src.ai.asistente_literatura import (
    evaluar_corpus,
    sugerir_keywords,
)


@st.cache_data(ttl=86400, show_spinner=False)
def sugerir_keywords_cached(tema: str, pregunta: str = "") -> str:
    """Versión cacheada de sugerir_keywords (24h)."""
    return sugerir_keywords(tema, pregunta)


@st.cache_data(ttl=3600, show_spinner=False)
def evaluar_corpus_cached(pregunta: str, corpus_json: str) -> str:
    """Versión cacheada de evaluar_corpus (1h)."""
    corpus_df = pd.DataFrame(json.loads(corpus_json))
    return evaluar_corpus(pregunta, corpus_df)