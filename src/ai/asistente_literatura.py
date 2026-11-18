"""Asistente de IA para la sección Literatura.

Funciones:
- sugerir_keywords(tema, pregunta) -> str
- evaluar_corpus(pregunta, corpus_df) -> str

Ambas usan Google Gemini con reintentos automáticos (3 intentos, 5s)
para manejar saturación del modelo (error 503).
"""

from __future__ import annotations

import time
from typing import Any

import pandas as pd

from src.ai.config import get_modelo
from src.ai.prompts_literatura import PROMPT_EVALUAR_CORPUS, PROMPT_KEYWORDS

MODELO = get_modelo()
MAX_REINTENTOS = 3
ESPERA_SEGUNDOS = 10


def _get_cliente():
    """Crea el cliente de Gemini leyendo GEMINI_API_KEY de st.secrets o env."""
    import os

    try:
        from google import genai
    except ImportError:
        raise ValueError(
            "El SDK google-genai no está instalado. "
            "Ejecuta: pip install google-genai"
        )

    api_key = None
    try:
        import streamlit as st
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "No se encontró GEMINI_API_KEY. Configúrala en "
            ".streamlit/secrets.toml o como variable de entorno."
        )

    return genai.Client(api_key=api_key)


def _generar_con_reintentos(prompt: str) -> str:
    """Llama a Gemini con reintentos ante 503 (saturación)."""
    cliente = _get_cliente()

    ultimo_error: Exception | None = None
    for intento in range(1, MAX_REINTENTOS + 1):
        try:
            respuesta = cliente.models.generate_content(
                model=MODELO,
                contents=prompt,
            )
            texto = getattr(respuesta, "text", None)
            if not texto:
                raise ValueError("Gemini devolvió una respuesta vacía.")
            return texto
        except Exception as e:
            mensaje = str(e)
            if "503" in mensaje or "UNAVAILABLE" in mensaje:
                ultimo_error = e
                if intento < MAX_REINTENTOS:
                    time.sleep(ESPERA_SEGUNDOS)
                    continue
                raise ConnectionError(
                    f"El modelo de IA está saturado tras {MAX_REINTENTOS} "
                    f"intentos. Intenta de nuevo en unos minutos."
                )
            if "404" in mensaje or "NOT_FOUND" in mensaje:
                raise ConnectionError(
                    f"El modelo '{MODELO}' no está disponible. "
                    f"Revisa el nombre del modelo en asistente_literatura.py."
                )
            if "401" in mensaje or "UNAUTHENTICATED" in mensaje:
                raise ConnectionError(
                    "La API key de Gemini no es válida. "
                    "Revisa .streamlit/secrets.toml."
                )
            if "429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje:
                raise ConnectionError(
                    "Cuota de la API de Gemini agotada. "
                    "Espera unos minutos o revisa tu plan."
                )
            raise ValueError(f"Error de la API de Gemini: {mensaje}")

    raise ConnectionError(
        f"El modelo de IA está saturado tras {MAX_REINTENTOS} intentos."
    )


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def sugerir_keywords(tema: str, pregunta: str = "") -> str:
    """Sugiere palabras clave para búsqueda bibliográfica.

    Parámetros
    ----------
    tema : str
        Tema amplio de interés.
    pregunta : str, opcional
        Pregunta de investigación ya refinada (si existe).

    Devuelve
    -------
    str
        Markdown con keywords organizadas, operadores y nota pedagógica.

    Levanta
    ------
    ValueError
        Si falta tema o la respuesta es inválida.
    ConnectionError
        Si hay problemas de red, cuota o saturación.
    """
    if not tema or not tema.strip():
        raise ValueError("Debes proporcionar un tema para sugerir keywords.")

    prompt = PROMPT_KEYWORDS.format(
        tema=tema.strip(),
        pregunta=(pregunta or "(sin pregunta definida aún)").strip(),
    )
    return _generar_con_reintentos(prompt)


def evaluar_corpus(pregunta: str, corpus_df: pd.DataFrame) -> str:
    """Evalúa críticamente el corpus de literatura del estudiante.

    Parámetros
    ----------
    pregunta : str
        Pregunta de investigación.
    corpus_df : pd.DataFrame
        Corpus con al menos columnas: titulo, anio, tipo, citas.

    Devuelve
    -------
    str
        Markdown con diagnóstico, vacíos, riesgos y recomendaciones.
    """
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

    # Limitar a 40 trabajos para no exceder contexto del modelo
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
    return _generar_con_reintentos(prompt)