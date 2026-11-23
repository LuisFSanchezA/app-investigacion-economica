"""Interfaz abstracta para proveedores de IA."""

from __future__ import annotations

from abc import ABC, abstractmethod


class ErrorProveedorIA(Exception):
    """Error genérico de un proveedor de IA."""


class ErrorSaturado(ErrorProveedorIA):
    """El proveedor está saturado (503, rate limit temporal)."""


class ErrorCuota(ErrorProveedorIA):
    """Cuota agotada (429)."""


class ErrorModeloNoDisponible(ErrorProveedorIA):
    """El modelo no existe (404)."""


class ErrorCredenciales(ErrorProveedorIA):
    """API key inválida o ausente (401)."""


class ProveedorIA(ABC):
    """Interfaz que todo proveedor debe implementar."""

    nombre: str = "base"

    @abstractmethod
    def generar(self, prompt: str, max_tokens: int = 1024) -> str:
        """Genera texto a partir de un prompt.

        Devuelve el texto generado.
        Levanta las excepciones de arriba según el error.
        """

    @abstractmethod
    def disponible(self) -> bool:
        """True si el proveedor tiene credenciales configuradas."""