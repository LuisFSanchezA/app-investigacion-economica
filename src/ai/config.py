"""Configuración compartida del módulo de IA.

Centraliza el nombre del modelo de Gemini para que un cambio de modelo
no requiera tocar código en varios archivos.

Prioridad de lectura:
1. st.secrets["GEMINI_MODEL"] (Streamlit)
2. Variable de entorno GEMINI_MODEL
3. Fallback: gemini-3.8-flash
"""

import os


MODELO_POR_DEFECTO = "gemini-3.8-flash"

# Valores que indican "no configurado" y deben ignorarse.
_PLACEHOLDERS = {"", "tu_modelo_real", "tu_modelo", "TODO", "CAMBIAME"}


def get_modelo() -> str:
    """Devuelve el nombre del modelo de Gemini a usar."""
    # 1. Streamlit secrets
    try:
        import streamlit as st
        modelo = (st.secrets.get("GEMINI_MODEL", "") or "").strip()
        if modelo and modelo not in _PLACEHOLDERS:
            return modelo
    except Exception:
        pass

    # 2. Variable de entorno
    modelo = (os.environ.get("GEMINI_MODEL", "") or "").strip()
    if modelo and modelo not in _PLACEHOLDERS:
        return modelo

    # 3. Fallback
    return MODELO_POR_DEFECTO