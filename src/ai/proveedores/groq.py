"""Proveedor Groq (inferencia ultrarrápida de modelos open-source)."""

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


class GroqProvider(ProveedorIA):
    nombre = "groq"

    def __init__(self, api_key: str | None = None, modelo: str | None = None):
        self.api_key = self._leer_key() if api_key is None else api_key
        self.modelo = self._leer_modelo() if modelo is None else modelo
        self._cliente = None

    def _leer_key(self) -> str:
        try:
            import streamlit as st
            key = st.secrets.get("GROQ_API_KEY", "")
            if key:
                return key
        except Exception:
            pass
        return os.environ.get("GROQ_API_KEY", "")

    def _leer_modelo(self) -> str:
        try:
            import streamlit as st
            m = st.secrets.get("GROQ_MODEL", "")
            if m:
                return m
        except Exception:
            pass
        return os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    def disponible(self) -> bool:
        return bool(self.api_key)

    def _get_cliente(self):
        if self._cliente is None:
            try:
                from groq import Groq
            except ImportError as e:
                raise ErrorProveedorIA(
                    "El SDK groq no está instalado. "
                    "Ejecuta: pip install groq"
                ) from e
            self._cliente = Groq(api_key=self.api_key, timeout=60.0)
        return self._cliente

    def generar(self, prompt: str, max_tokens: int = 1024) -> str:
        if not self.api_key:
            raise ErrorCredenciales("Falta GROQ_API_KEY.")
        try:
            resp = self._get_cliente().chat.completions.create(
                model=self.modelo,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
        except Exception as e:
            msg = str(e).lower()
            if "503" in msg or "unavailable" in msg:
                raise ErrorSaturado(f"Groq saturado: {e}") from e
            if "429" in msg or "rate_limit" in msg:
                raise ErrorCuota(f"Cuota Groq agotada: {e}") from e
            if "404" in msg or "not found" in msg:
                raise ErrorModeloNoDisponible(
                    f"Modelo '{self.modelo}' no disponible: {e}"
                ) from e
            if "401" in msg or "invalid_api_key" in msg:
                raise ErrorCredenciales(f"API key Groq inválida: {e}") from e
            raise ErrorProveedorIA(f"Error Groq: {e}") from e
        texto = (
            resp.choices[0].message.content if resp.choices else None
        )
        if not texto:
            raise ErrorProveedorIA("Groq devolvió respuesta vacía.")
        return texto 