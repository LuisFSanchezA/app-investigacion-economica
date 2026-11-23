"""Capa de abstracción de proveedor de IA.

Lee AI_PROVIDER (orden de preferencia) de secrets/env y construye la
cadena de proveedores con fallback automático ante errores temporales.
"""

from __future__ import annotations

import os

from .proveedores.base import (
    ErrorCuota,
    ErrorProveedorIA,
    ErrorSaturado,
    ProveedorIA,
)
from .proveedores.gemini import GeminiProvider
from .proveedores.groq import GroqProvider

# Registro de proveedores disponibles.
_REGISTRO = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
}

# Orden por defecto si AI_PROVIDER no está definido.
_ORDEN_POR_DEFECTO = ["groq", "gemini"]


def _leer_orden() -> list[str]:
    try:
        import streamlit as st
        raw = st.secrets.get("AI_PROVIDER", "")
        if raw:
            return [p.strip() for p in raw.split(",") if p.strip()]
    except Exception:
        pass
    raw = os.environ.get("AI_PROVIDER", "")
    if raw:
        return [p.strip() for p in raw.split(",") if p.strip()]
    return _ORDEN_POR_DEFECTO


def construir_cadena() -> list[ProveedorIA]:
    """Construye la lista de proveedores en orden, solo los disponibles."""
    cadena: list[ProveedorIA] = []
    for nombre in _leer_orden():
        cls = _REGISTRO.get(nombre)
        if cls is None:
            continue
        p = cls()
        if p.disponible():
            cadena.append(p)
    return cadena


def generar_con_fallback(
    prompt: str,
    max_tokens: int = 1024,
    max_reintentos_por_proveedor: int = 2,
    espera_segundos: int = 5,
) -> str:
    """Genera texto probando proveedores en orden hasta que uno responda.

    Reintenta ante saturación (503) hasta `max_reintentos_por_proveedor`.
    Si un proveedor falla con error no recuperable (credenciales, modelo),
    pasa al siguiente inmediatamente.
    """
    import time

    cadena = construir_cadena()
    if not cadena:
        raise ErrorProveedorIA(
            "No hay proveedor de IA configurado. "
            "Define GROQ_API_KEY o GEMINI_API_KEY en secrets."
        )

    ultimo_error: Exception | None = None
    for proveedor in cadena:
        for intento in range(1, max_reintentos_por_proveedor + 1):
            try:
                return proveedor.generar(prompt, max_tokens=max_tokens)
            except ErrorSaturado as e:
                ultimo_error = e
                if intento < max_reintentos_por_proveedor:
                    time.sleep(espera_segundos)
                    continue
                break  # reintentos agotados, siguiente proveedor
            except ErrorCuota as e:
                ultimo_error = e
                break  # cuota agotada, siguiente proveedor
            except ErrorProveedorIA as e:
                ultimo_error = e
                break  # error no recuperable, siguiente proveedor
            except Exception as e:  # defensa: cualquier error inesperado
                ultimo_error = e
                break

    raise ErrorProveedorIA(
        f"Todos los proveedores fallaron. Último error: {ultimo_error}"
    )