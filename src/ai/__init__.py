"""Módulo de asistencia con IA para la plataforma de investigación."""

from src.ai.asistente import (
    sugerir_preguntas,
    sugerir_objetivos,
    generar_protocolo,
)
from src.ai.asistente_literatura import (
    sugerir_keywords,
    evaluar_corpus,
)

__all__ = [
    "sugerir_preguntas",
    "sugerir_objetivos",
    "generar_protocolo",
    "sugerir_keywords",
    "evaluar_corpus",
]