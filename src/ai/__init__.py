"""Módulo de asistencia con IA para la plataforma de investigación."""

from src.ai.asistente import (
    sugerir_preguntas,
    sugerir_objetivos,
    generar_protocolo,
)
from src.ai.asistente_literatura import (
    sugerir_keywords,
    evaluar_corpus,
    sintetizar_corpus,
    detectar_vacios,
    clasificar_papers,
)
from src.ai.asistente_tema import (
    sugerir_enunciado,
    generar_justificacion,
    generar_resumen_ejecutivo,
)
from src.ai.cache_literatura import (
    sugerir_keywords_cached,
    evaluar_corpus_cached,
)

__all__ = [
    "sugerir_preguntas",
    "sugerir_objetivos",
    "generar_protocolo",
    "sugerir_keywords",
    "evaluar_corpus",
    "sintetizar_corpus",
    "detectar_vacios",
    "clasificar_papers",
    "sugerir_enunciado",
    "generar_justificacion",
    "generar_resumen_ejecutivo",
    "sugerir_keywords_cached",
    "evaluar_corpus_cached",
]