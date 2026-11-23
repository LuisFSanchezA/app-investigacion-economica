"""Asistente de IA para la sección Literatura.

Funciones:
- sugerir_keywords(tema, pregunta) -> str
- evaluar_corpus(pregunta, corpus_df) -> str
- sintetizar_corpus, detectar_vacios, clasificar_papers

La generación pasa por la capa de proveedor (Groq → Gemini con fallback).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ai.prompts_literatura import (
    PROMPT_CLASIFICAR,
    PROMPT_EVALUAR_CORPUS,
    PROMPT_KEYWORDS,
    PROMPT_SINTESIS,
    PROMPT_VACIOS,
)
from src.ai.proveedor import generar_con_fallback


# ---------------------------------------------------------------------------
# Generación (capa de proveedor)
# ---------------------------------------------------------------------------

def _generar(prompt: str) -> str:
    """Genera texto usando la capa de proveedor con fallback."""
    return generar_con_fallback(prompt, max_tokens=1024)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def sugerir_keywords(tema: str, pregunta: str = "") -> str:
    """Sugiere palabras clave para búsqueda bibliográfica."""
    if not tema or not tema.strip():
        raise ValueError("Debes proporcionar un tema para sugerir keywords.")

    prompt = PROMPT_KEYWORDS.format(
        tema=tema.strip(),
        pregunta=(pregunta or "(sin pregunta definida aún)").strip(),
    )
    return _generar(prompt)


def evaluar_corpus(pregunta: str, corpus_df: pd.DataFrame) -> str:
    """Evalúa críticamente el corpus de literatura del estudiante."""
    if not pregunta or not pregunta.strip():
        raise ValueError("Debes proporcionar una pregunta de investigación.")

    if corpus_df is None or corpus_df.empty:
        raise ValueError("El corpus está vacío. Añade trabajos antes de evaluar.")

    columnas = ["titulo", "anio", "tipo", "citas"]
    faltantes = [c for c in columnas if c not in corpus_df.columns]
    if faltantes:
        raise ValueError(
            f"El corpus no tiene las columnas requeridas: {faltantes}."
        )

    muestra = corpus_df.head(40)
    lineas = []
    for _, row in muestra.iterrows():
        lineas.append(
            f"- {row['titulo']} | {row['anio']} | {row['tipo']} | "
            f"{row['citas']} citas"
        )
    corpus_texto = "\n".join(lineas)

    if len(corpus_df) > 40:
        corpus_texto += f"\n\n(Se muestran 40 de {len(corpus_df)} trabajos.)"

    prompt = PROMPT_EVALUAR_CORPUS.format(
        corpus=corpus_texto,
        pregunta=pregunta.strip(),
    )
    return _generar(prompt)


# ---------------------------------------------------------------------------
# Funciones avanzadas (F4)
# ---------------------------------------------------------------------------

def _corpus_a_texto(corpus_df: pd.DataFrame, max_items: int = 40) -> str:
    """Convierte el corpus en texto plano para pasarlo a la IA."""
    muestra = corpus_df.head(max_items)
    lineas = []
    for i, (_, row) in enumerate(muestra.iterrows(), start=1):
        titulo = str(row.get("titulo", ""))[:120]
        anio = row.get("anio", "")
        tipo = row.get("tipo", "")
        citas = row.get("citas", 0)
        conceptos = str(row.get("conceptos", ""))[:80]
        lineas.append(
            f"{i}. {titulo} | {anio} | {tipo} | {citas} citas | {conceptos}"
        )
    if len(corpus_df) > max_items:
        lineas.append(f"\n(Se muestran {max_items} de {len(corpus_df)} trabajos.)")
    return "\n".join(lineas)


def sintetizar_corpus(pregunta: str, corpus_df: pd.DataFrame) -> str:
    """Sintetiza el estado del arte del corpus."""
    if not pregunta or not pregunta.strip():
        raise ValueError("Debes proporcionar una pregunta de investigación.")
    if corpus_df is None or corpus_df.empty:
        raise ValueError("El corpus está vacío.")
    if "titulo" not in corpus_df.columns:
        raise ValueError("El corpus debe tener columna 'titulo'.")

    prompt = PROMPT_SINTESIS.format(
        pregunta=pregunta.strip(),
        corpus=_corpus_a_texto(corpus_df),
    )
    return _generar(prompt)


def detectar_vacios(pregunta: str, corpus_df: pd.DataFrame) -> str:
    """Detecta vacíos de investigación en el corpus."""
    if not pregunta or not pregunta.strip():
        raise ValueError("Debes proporcionar una pregunta de investigación.")
    if corpus_df is None or corpus_df.empty:
        raise ValueError("El corpus está vacío.")
    if "titulo" not in corpus_df.columns:
        raise ValueError("El corpus debe tener columna 'titulo'.")

    prompt = PROMPT_VACIOS.format(
        pregunta=pregunta.strip(),
        corpus=_corpus_a_texto(corpus_df),
    )
    return _generar(prompt)


def clasificar_papers(pregunta: str, corpus_df: pd.DataFrame) -> str:
    """Clasifica cada paper del corpus por su rol en la investigación."""
    if not pregunta or not pregunta.strip():
        raise ValueError("Debes proporcionar una pregunta de investigación.")
    if corpus_df is None or corpus_df.empty:
        raise ValueError("El corpus está vacío.")
    if "titulo" not in corpus_df.columns:
        raise ValueError("El corpus debe tener columna 'titulo'.")

    prompt = PROMPT_CLASIFICAR.format(
        pregunta=pregunta.strip(),
        corpus=_corpus_a_texto(corpus_df),
    )
    return _generar(prompt)


# ---------------------------------------------------------------------------
# Versiones cacheadas para la UI
# ---------------------------------------------------------------------------

@st.cache_data(ttl=86400, show_spinner=False)
def sugerir_keywords_cached(tema: str, pregunta: str = "") -> str:
    """Versión cacheada de sugerir_keywords (24h)."""
    return sugerir_keywords(tema, pregunta)


@st.cache_data(ttl=3600, show_spinner=False)
def evaluar_corpus_cached(pregunta: str, corpus_json: str) -> str:
    """Versión cacheada de evaluar_corpus (1h)."""
    import json
    corpus_df = pd.DataFrame(json.loads(corpus_json))
    return evaluar_corpus(pregunta, corpus_df) 