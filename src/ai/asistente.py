"""Asistente de investigación con IA (Google Gemini).

Este módulo encapsula las llamadas a la API de Gemini y expone
funciones de alto nivel para la interfaz de Streamlit.
"""

import streamlit as st
from google import genai
from google.genai import errors as genai_errors

from src.ai.prompts import (
    PROMPT_SUGERIR_PREGUNTAS,
    PROMPT_SUGERIR_OBJETIVOS,
    PROMPT_GENERAR_PROTOCOLO,
)


MODELO_POR_DEFECTO = "gemini-3.8-flash"


def _get_client() -> genai.Client:
    """Crea el cliente de Gemini usando la API key de secrets.toml."""
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except (KeyError, FileNotFoundError):
        raise ValueError(
            "No se encontró GEMINI_API_KEY en .streamlit/secrets.toml. "
            "Configura tu API key de Gemini antes de usar el asistente."
        )
    return genai.Client(api_key=api_key)


def _llamar_modelo(
    prompt: str,
    modelo: str = MODELO_POR_DEFECTO,
    intentos: int = 3,
    espera_segundos: int = 5,
) -> str:
    """Llama a Gemini con reintentos automáticos en caso de saturación.

    Maneja errores comunes de la API con mensajes claros.
    """
    import time

    client = _get_client()

    ultimo_error = None
    for intento in range(1, intentos + 1):
        try:
            response = client.models.generate_content(
                model=modelo,
                contents=prompt,
            )
            return response.text
        except genai_errors.ClientError as e:
            if "404" in str(e) or "NOT_FOUND" in str(e):
                raise ConnectionError(
                    f"El modelo {modelo} no está disponible. "
                    f"Verifica el nombre del modelo en la documentación de Gemini."
                )
            raise ConnectionError(f"Error de la API de Gemini: {e}")
        except genai_errors.ServerError as e:
            ultimo_error = e
            if intento < intentos:
                time.sleep(espera_segundos)
                continue
            raise ConnectionError(
                f"El modelo está saturado después de {intentos} intentos. "
                f"Intenta de nuevo en unos minutos. ({e})"
            )
        except Exception as e:
            raise ConnectionError(f"Error inesperado al llamar a Gemini: {e}")

    raise ConnectionError(f"Error inesperado: {ultimo_error}")


def sugerir_preguntas(tema: str) -> str:
    """Sugiere 5 preguntas de investigación a partir de un tema."""
    if not tema or not tema.strip():
        raise ValueError("Debes escribir un tema antes de pedir sugerencias.")
    prompt = PROMPT_SUGERIR_PREGUNTAS.format(tema=tema.strip())
    return _llamar_modelo(prompt)


def sugerir_objetivos(pregunta: str) -> str:
    """Sugiere objetivo general y específicos a partir de una pregunta."""
    if not pregunta or not pregunta.strip():
        raise ValueError("Debes escribir una pregunta antes de pedir objetivos.")
    prompt = PROMPT_SUGERIR_OBJETIVOS.format(pregunta=pregunta.strip())
    return _llamar_modelo(prompt)


def generar_protocolo(tema: str, pregunta: str, objetivos: str) -> str:
    """Genera un borrador de protocolo de investigación."""
    if not tema or not pregunta:
        raise ValueError("Necesitas tema y pregunta para generar el protocolo.")
    prompt = PROMPT_GENERAR_PROTOCOLO.format(
        tema=tema.strip(),
        pregunta=pregunta.strip(),
        objetivos=objetivos.strip() if objetivos else "(pendiente)",
    )
    return _llamar_modelo(prompt)