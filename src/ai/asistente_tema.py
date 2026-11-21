"""Asistente de IA para la sección Tema."""

from __future__ import annotations

import time

import pandas as pd

from src.ai.config import get_modelo
from src.ai.prompts_tema import (
    PROMPT_ENUNCIADO,
    PROMPT_JUSTIFICACION,
    PROMPT_RESUMEN_EJECUTIVO,
)

MODELO = get_modelo()
MAX_REINTENTOS = 3
ESPERA_SEGUNDOS = 5


def _get_cliente():
    """Crea el cliente de Gemini leyendo GEMINI_API_KEY de secrets o env."""
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

    return genai.Client(
        api_key=api_key,
        http_options={"timeout": 30000},
    )


def _generar_con_reintentos(prompt: str) -> str:
    """Llama a Gemini con reintentos ante 503 (saturación)."""
    cliente = _get_cliente()

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
                    f"Revisa el nombre del modelo en asistente_tema.py."
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


def _contexto(
    pregunta: str,
    objetivos: str,
    n_corpus: int,
    datos: str,
    fenomeno: str,
    poblacion: str,
    periodo: str,
    espacio: str,
    variables: str,
) -> dict:
    """Devuelve un dict con el contexto común a los 3 prompts."""
    return {
        "pregunta": pregunta or "(sin definir)",
        "objetivos": objetivos or "(sin definir)",
        "n_corpus": n_corpus,
        "datos": datos or "(sin datos consultados)",
        "fenomeno": fenomeno or "(sin delimitar)",
        "poblacion": poblacion or "(sin delimitar)",
        "periodo": periodo or "(sin delimitar)",
        "espacio": espacio or "(sin delimitar)",
        "variables": variables or "(sin delimitar)",
    }


def sugerir_enunciado(
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
    """Sugiere un enunciado de tema delimitado.

    Levanta ValueError si falta la pregunta.
    """
    if not pregunta or not pregunta.strip():
        raise ValueError("Debes proporcionar una pregunta de investigación.")

    ctx = _contexto(
        pregunta, objetivos, n_corpus, datos,
        fenomeno, poblacion, periodo, espacio, variables,
    )
    prompt = PROMPT_ENUNCIADO.format(**ctx)
    return _generar_con_reintentos(prompt)


def generar_justificacion(
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
    """Genera un borrador de justificación (pertinencia, viabilidad, originalidad)."""
    if not pregunta or not pregunta.strip():
        raise ValueError("Debes proporcionar una pregunta de investigación.")

    ctx = _contexto(
        pregunta, objetivos, n_corpus, datos,
        fenomeno, poblacion, periodo, espacio, variables,
    )
    prompt = PROMPT_JUSTIFICACION.format(**ctx)
    return _generar_con_reintentos(prompt)


def generar_resumen_ejecutivo(
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
    """Genera un resumen ejecutivo de 1 página del proyecto."""
    if not pregunta or not pregunta.strip():
        raise ValueError("Debes proporcionar una pregunta de investigación.")
    if not enunciado or not enunciado.strip():
        raise ValueError("Debes proporcionar un enunciado del tema.")

    ctx = _contexto(
        pregunta, objetivos, n_corpus, datos,
        fenomeno, poblacion, periodo, espacio, variables,
    )
    ctx["enunciado"] = enunciado
    prompt = PROMPT_RESUMEN_EJECUTIVO.format(**ctx)
    return _generar_con_reintentos(prompt)