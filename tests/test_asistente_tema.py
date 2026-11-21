"""Pruebas del asistente de IA para la sección Tema."""

from unittest.mock import MagicMock, patch

import pytest

from src.ai.asistente_tema import (
    generar_justificacion,
    generar_resumen_ejecutivo,
    sugerir_enunciado,
)


def _mock_cliente(texto: str = "## Enunciado\n..."):
    cliente = MagicMock()
    respuesta = MagicMock()
    respuesta.text = texto
    cliente.models.generate_content.return_value = respuesta
    return cliente


# ----------------------- sugerir_enunciado -------------------------------

class TestSugerirEnunciado:
    @patch("src.ai.asistente_tema._get_cliente")
    def test_exitoso(self, mock_get_cliente):
        mock_get_cliente.return_value = _mock_cliente("## Enunciado\n...")
        resultado = sugerir_enunciado(
            pregunta="¿Cómo afecta la informalidad al salario juvenil?",
            fenomeno="informalidad laboral",
            poblacion="jóvenes",
            periodo="2010-2024",
            espacio="México",
        )
        assert "Enunciado" in resultado

    @patch("src.ai.asistente_tema._get_cliente")
    def test_pregunta_vacia_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            sugerir_enunciado(pregunta="")

    @patch("src.ai.asistente_tema._get_cliente")
    def test_solo_espacios_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            sugerir_enunciado(pregunta="   ")

    @patch("src.ai.asistente_tema._get_cliente")
    def test_error_401(self, mock_get_cliente):
        cliente = MagicMock()
        cliente.models.generate_content.side_effect = Exception("401 UNAUTHENTICATED")
        mock_get_cliente.return_value = cliente
        with pytest.raises(ConnectionError, match="API key"):
            sugerir_enunciado(pregunta="¿Pregunta?")

    @patch("src.ai.asistente_tema._get_cliente")
    def test_error_404(self, mock_get_cliente):
        cliente = MagicMock()
        cliente.models.generate_content.side_effect = Exception("404 NOT_FOUND")
        mock_get_cliente.return_value = cliente
        with pytest.raises(ConnectionError, match="modelo"):
            sugerir_enunciado(pregunta="¿Pregunta?")

    @patch("src.ai.asistente_tema._get_cliente")
    def test_error_429(self, mock_get_cliente):
        cliente = MagicMock()
        cliente.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED")
        mock_get_cliente.return_value = cliente
        with pytest.raises(ConnectionError, match="[Cc]uota"):
            sugerir_enunciado(pregunta="¿Pregunta?")


# ---------------------- generar_justificacion ----------------------------

class TestGenerarJustificacion:
    @patch("src.ai.asistente_tema._get_cliente")
    def test_exitoso(self, mock_get_cliente):
        mock_get_cliente.return_value = _mock_cliente("## Pertinencia\n...")
        resultado = generar_justificacion(pregunta="¿Pregunta?")
        assert "Pertinencia" in resultado

    @patch("src.ai.asistente_tema._get_cliente")
    def test_pregunta_vacia_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            generar_justificacion(pregunta="")


# --------------------- generar_resumen_ejecutivo -------------------------

class TestGenerarResumenEjecutivo:
    @patch("src.ai.asistente_tema._get_cliente")
    def test_exitoso(self, mock_get_cliente):
        mock_get_cliente.return_value = _mock_cliente("# Resumen ejecutivo\n...")
        resultado = generar_resumen_ejecutivo(
            pregunta="¿Pregunta?",
            enunciado="Informalidad laboral juvenil en México, 2010-2024",
        )
        assert "Resumen ejecutivo" in resultado

    @patch("src.ai.asistente_tema._get_cliente")
    def test_pregunta_vacia_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            generar_resumen_ejecutivo(pregunta="", enunciado="X")

    @patch("src.ai.asistente_tema._get_cliente")
    def test_enunciado_vacio_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            generar_resumen_ejecutivo(pregunta="¿Pregunta?", enunciado="") 