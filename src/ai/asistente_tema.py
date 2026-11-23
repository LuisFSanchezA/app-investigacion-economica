"""Asistente de IA para la sección Tema."""

from __future__ import annotations

from src.ai.prompts_tema import (
    PROMPT_ENUNCIADO,
    PROMPT_JUSTIFICACION,
    PROMPT_RESUMEN_EJECUTIVO,
)
from src.ai.proveedor import generar_con_fallback


# ---------------------------------------------------------------------------
# Generación (capa de proveedor)
# ---------------------------------------------------------------------------

def _generar(prompt: str) -> str:
    """Genera texto usando la capa de proveedor con fallback."""
    return generar_con_fallback(prompt, max_tokens=1024)


# ---------------------------------------------------------------------------
# Contexto común
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

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
    """Sugiere un enunciado de tema delimitado."""
    if not pregunta or not pregunta.strip():
        raise ValueError("Debes proporcionar una pregunta de investigación.")

    ctx = _contexto(
        pregunta, objetivos, n_corpus, datos,
        fenomeno, poblacion, periodo, espacio, variables,
    )
    prompt = PROMPT_ENUNCIADO.format(**ctx)
    return _generar(prompt)


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
    return _generar(prompt)


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
    return _generar(prompt) 