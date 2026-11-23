"""Pruebas de los proveedores concretos (Gemini, Groq).

Se mockea el SDK subyacente para verificar la traducción de errores
a las excepciones de la capa (ErrorSaturado, ErrorCuota, etc.).
"""

from unittest.mock import MagicMock, patch

import pytest

from src.ai.proveedores.base import (
    ErrorCredenciales,
    ErrorCuota,
    ErrorModeloNoDisponible,
    ErrorProveedorIA,
    ErrorSaturado,
)
from src.ai.proveedores.gemini import GeminiProvider
from src.ai.proveedores.groq import GroqProvider


# ---------------------------------------------------------------------------
# GeminiProvider
# ---------------------------------------------------------------------------

class TestGeminiProvider:
    def _provider(self, api_key="fake"):
        return GeminiProvider(api_key=api_key, modelo="gemini-3.8-flash")

    def test_disponible_con_key(self):
        assert self._provider().disponible() is True

    def test_no_disponible_sin_key(self):
        assert GeminiProvider(api_key="").disponible() is False

    def test_sin_key_falla(self):
        p = GeminiProvider(api_key="", modelo="x")
        with pytest.raises(ErrorCredenciales):
            p.generar("hola")

    @patch("src.ai.proveedores.gemini.GeminiProvider._get_cliente")
    def test_exitoso(self, mock_cliente):
        respuesta = MagicMock()
        respuesta.text = "hola mundo"
        mock_cliente.return_value.models.generate_content.return_value = respuesta
        p = self._provider()
        assert p.generar("hola") == "hola mundo"

    @patch("src.ai.proveedores.gemini.GeminiProvider._get_cliente")
    def test_error_503_es_saturado(self, mock_cliente):
        mock_cliente.return_value.models.generate_content.side_effect = Exception(
            "503 UNAVAILABLE"
        )
        with pytest.raises(ErrorSaturado):
            self._provider().generar("hola")

    @patch("src.ai.proveedores.gemini.GeminiProvider._get_cliente")
    def test_error_429_es_cuota(self, mock_cliente):
        mock_cliente.return_value.models.generate_content.side_effect = Exception(
            "429 RESOURCE_EXHAUSTED"
        )
        with pytest.raises(ErrorCuota):
            self._provider().generar("hola")

    @patch("src.ai.proveedores.gemini.GeminiProvider._get_cliente")
    def test_error_404_es_modelo(self, mock_cliente):
        mock_cliente.return_value.models.generate_content.side_effect = Exception(
            "404 NOT_FOUND"
        )
        with pytest.raises(ErrorModeloNoDisponible):
            self._provider().generar("hola")

    @patch("src.ai.proveedores.gemini.GeminiProvider._get_cliente")
    def test_error_401_es_credenciales(self, mock_cliente):
        mock_cliente.return_value.models.generate_content.side_effect = Exception(
            "401 UNAUTHENTICATED"
        )
        with pytest.raises(ErrorCredenciales):
            self._provider().generar("hola")

    @patch("src.ai.proveedores.gemini.GeminiProvider._get_cliente")
    def test_respuesta_vacia(self, mock_cliente):
        respuesta = MagicMock()
        respuesta.text = ""
        mock_cliente.return_value.models.generate_content.return_value = respuesta
        with pytest.raises(ErrorProveedorIA, match="vacía"):
            self._provider().generar("hola")


# ---------------------------------------------------------------------------
# GroqProvider
# ---------------------------------------------------------------------------

class TestGroqProvider:
    def _provider(self, api_key="fake"):
        return GroqProvider(api_key=api_key, modelo="llama-3.3-70b-versatile")

    def test_disponible_con_key(self):
        assert self._provider().disponible() is True

    def test_no_disponible_sin_key(self):
        assert GroqProvider(api_key="").disponible() is False

    def test_sin_key_falla(self):
        p = GroqProvider(api_key="", modelo="x")
        with pytest.raises(ErrorCredenciales):
            p.generar("hola")

    @patch("src.ai.proveedores.groq.GroqProvider._get_cliente")
    def test_exitoso(self, mock_cliente):
        mensaje = MagicMock()
        mensaje.message.content = "hola mundo"
        respuesta = MagicMock()
        respuesta.choices = [mensaje]
        mock_cliente.return_value.chat.completions.create.return_value = respuesta
        p = self._provider()
        assert p.generar("hola") == "hola mundo"

    @patch("src.ai.proveedores.groq.GroqProvider._get_cliente")
    def test_error_503_es_saturado(self, mock_cliente):
        mock_cliente.return_value.chat.completions.create.side_effect = Exception(
            "503 unavailable"
        )
        with pytest.raises(ErrorSaturado):
            self._provider().generar("hola")

    @patch("src.ai.proveedores.groq.GroqProvider._get_cliente")
    def test_error_429_es_cuota(self, mock_cliente):
        mock_cliente.return_value.chat.completions.create.side_effect = Exception(
            "429 rate_limit_exceeded"
        )
        with pytest.raises(ErrorCuota):
            self._provider().generar("hola")

    @patch("src.ai.proveedores.groq.GroqProvider._get_cliente")
    def test_error_404_es_modelo(self, mock_cliente):
        mock_cliente.return_value.chat.completions.create.side_effect = Exception(
            "404 model not found"
        )
        with pytest.raises(ErrorModeloNoDisponible):
            self._provider().generar("hola")

    @patch("src.ai.proveedores.groq.GroqProvider._get_cliente")
    def test_error_401_es_credenciales(self, mock_cliente):
        mock_cliente.return_value.chat.completions.create.side_effect = Exception(
            "401 invalid_api_key"
        )
        with pytest.raises(ErrorCredenciales):
            self._provider().generar("hola")

    @patch("src.ai.proveedores.groq.GroqProvider._get_cliente")
    def test_respuesta_vacia(self, mock_cliente):
        respuesta = MagicMock()
        respuesta.choices = []
        mock_cliente.return_value.chat.completions.create.return_value = respuesta
        with pytest.raises(ErrorProveedorIA, match="vacía"):
            self._provider().generar("hola") 