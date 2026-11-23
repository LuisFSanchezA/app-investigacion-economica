"""Proveedor Gemini (Google AI Studio)."""

from __future__ import annotations

import os

from .base import (
    ErrorCredenciales,
    ErrorCuota,
    ErrorModeloNoDisponible,
    ErrorProveedorIA,
    ErrorSaturado,
    ProveedorIA,
)


class GeminiProvider(ProveedorIA):
    nombre = "gemini"

    def __init__(self, api_key: str | None = None, modelo: str | None = None):
    # None → leer de secrets/env. "" → explícitamente sin key.
        self.api_key = self._leer_key() if api_key is None else api_key
        self.modelo = self._leer_modelo() if modelo is None else modelo
        self._cliente = None

    def _leer_key(self) -> str:
        try:
            import streamlit as st
            key = st.secrets.get("GEMINI_API_KEY", "")
            if key:
                return key
        except Exception:
            pass
        return os.environ.get("GEMINI_API_KEY", "")

    def _leer_modelo(self) -> str:
        try:
            import streamlit as st
            m = st.secrets.get("GEMINI_MODEL", "")
            if m and m not in {"", "tu_modelo_real"}:
                return m
        except Exception:
            pass
        return os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")

    def disponible(self) -> bool:
        return bool(self.api_key)

    def _get_cliente(self):
        if self._cliente is None:
            try:
                from google import genai
            except ImportError as e:
                raise ErrorProveedorIA(
                    "El SDK google-genai no está instalado. "
                    "Ejecuta: pip install google-genai"
                ) from e
            self._cliente = genai.Client(
                api_key=self.api_key,
                http_options={"timeout": 60000},
            )
        return self._cliente

    def generar(self, prompt: str, max_tokens: int = 1024) -> str:
        if not self.api_key:
            raise ErrorCredenciales("Falta GEMINI_API_KEY.")
        try:
            resp = self._get_cliente().models.generate_content(
                model=self.modelo,
                contents=prompt,
            )
        except Exception as e:
            msg = str(e)
            if "503" in msg or "UNAVAILABLE" in msg:
                raise ErrorSaturado(f"Gemini saturado: {msg}") from e
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                raise ErrorCuota(f"Cuota Gemini agotada: {msg}") from e
            if "404" in msg or "NOT_FOUND" in msg:
                raise ErrorModeloNoDisponible(
                    f"Modelo '{self.modelo}' no disponible: {msg}"
                ) from e
            if "401" in msg or "UNAUTHENTICATED" in msg:
                raise ErrorCredenciales(
                    f"API key Gemini inválida: {msg}"
                ) from e
            raise ErrorProveedorIA(f"Error Gemini: {msg}") from e
        texto = getattr(resp, "text", None)
        if not texto:
            raise ErrorProveedorIA("Gemini devolvió respuesta vacía.")
        return texto 