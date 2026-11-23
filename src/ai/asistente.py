"""Asistente de investigación con IA (Pregunta).

Este módulo encapsula las llamadas a la capa de proveedor de IA
(Groq → Gemini con fallback) y expone funciones de alto nivel para
la interfaz de Streamlit.
"""

from __future__ import annotations

from src.ai.prompts import (
    PROMPT_SUGERIR_PREGUNTAS,
    PROMPT_SUGERIR_OBJETIVOS,
    PROMPT_GENERAR_PROTOCOLO,
)
from src.ai.proveedor import generar_con_fallback


# ---------------------------------------------------------------------------
# Generación (capa de proveedor)
# ---------------------------------------------------------------------------

def _generar(prompt: str) -> str:
    """Genera texto usando la capa de proveedor con fallback."""
    return generar_con_fallback(prompt, max_tokens=2048)


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def sugerir_preguntas(tema: str) -> str:
    """Sugiere 5 preguntas de investigación a partir de un tema."""
    if not tema or not tema.strip():
        raise ValueError("Debes escribir un tema antes de pedir sugerencias.")
    prompt = PROMPT_SUGERIR_PREGUNTAS.format(tema=tema.strip())
    return _generar(prompt)


def sugerir_objetivos(pregunta: str) -> str:
    """Sugiere objetivo general y específicos a partir de una pregunta."""
    if not pregunta or not pregunta.strip():
        raise ValueError("Debes escribir una pregunta antes de pedir objetivos.")
    prompt = PROMPT_SUGERIR_OBJETIVOS.format(pregunta=pregunta.strip())
    return _generar(prompt)


def generar_protocolo(tema: str, pregunta: str, objetivos: str) -> str:
    """Genera un borrador de protocolo de investigación."""
    if not tema or not pregunta:
        raise ValueError("Necesitas tema y pregunta para generar el protocolo.")
    prompt = PROMPT_GENERAR_PROTOCOLO.format(
        tema=tema.strip(),
        pregunta=pregunta.strip(),
        objetivos=objetivos.strip() if objetivos else "(pendiente)",
    )
    return _generar(prompt) 