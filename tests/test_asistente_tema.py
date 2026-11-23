"""Pruebas del asistente de IA para la sección Tema."""

from unittest.mock import patch

import pytest

from src.ai.asistente_tema import (
    generar_justificacion,
    generar_resumen_ejecutivo,
    sugerir_enunciado,
)


# ---------------------------------------------------------------------------
# sugerir_enunciado
# ---------------------------------------------------------------------------

class TestSugerirEnunciado:
    @patch("src.ai.asistente_tema._generar")
    def test_exitoso(self, mock_generar):
        mock_generar.return_value = "## Enunciado\n..."
        resultado = sugerir_enunciado(
            pregunta="¿Cómo afecta la informalidad al salario juvenil?",
            fenomeno="informalidad laboral",
            poblacion="jóvenes",
            periodo="2010-2024",
            espacio="México",
        )
        assert "Enunciado" in resultado

    def test_pregunta_vacia_falla(self):
        with pytest.raises(ValueError):
            sugerir_enunciado(pregunta="")

    def test_solo_espacios_falla(self):
        with pytest.raises(ValueError):
            sugerir_enunciado(pregunta="   ")

    @patch("src.ai.asistente_tema._generar")
    def test_incluye_delimitacion_en_prompt(self, mock_generar):
        mock_generar.return_value = "## Enunciado"
        sugerir_enunciado(
            pregunta="¿Pregunta?",
            fenomeno="informalidad laboral",
            poblacion="jóvenes",
            periodo="2010-2024",
            espacio="México",
            variables="salario, edad",
        )
        prompt = mock_generar.call_args.args[0]
        assert "informalidad laboral" in prompt
        assert "jóvenes" in prompt
        assert "2010-2024" in prompt
        assert "México" in prompt

    @patch("src.ai.asistente_tema._generar")
    def test_propaga_connection_error(self, mock_generar):
        mock_generar.side_effect = ConnectionError("saturado")
        with pytest.raises(ConnectionError, match="saturado"):
            sugerir_enunciado(pregunta="¿Pregunta?")


# ---------------------------------------------------------------------------
# generar_justificacion
# ---------------------------------------------------------------------------

class TestGenerarJustificacion:
    @patch("src.ai.asistente_tema._generar")
    def test_exitoso(self, mock_generar):
        mock_generar.return_value = "## Pertinencia\n..."
        resultado = generar_justificacion(pregunta="¿Pregunta?")
        assert "Pertinencia" in resultado

    def test_pregunta_vacia_falla(self):
        with pytest.raises(ValueError):
            generar_justificacion(pregunta="")

    @patch("src.ai.asistente_tema._generar")
    def test_propaga_value_error(self, mock_generar):
        mock_generar.side_effect = ValueError("respuesta vacía")
        with pytest.raises(ValueError, match="vacía"):
            generar_justificacion(pregunta="¿Pregunta?")


# ---------------------------------------------------------------------------
# generar_resumen_ejecutivo
# ---------------------------------------------------------------------------

class TestGenerarResumenEjecutivo:
    @patch("src.ai.asistente_tema._generar")
    def test_exitoso(self, mock_generar):
        mock_generar.return_value = "# Resumen ejecutivo\n..."
        resultado = generar_resumen_ejecutivo(
            pregunta="¿Pregunta?",
            enunciado="Informalidad laboral juvenil en México, 2010-2024",
        )
        assert "Resumen ejecutivo" in resultado

    def test_pregunta_vacia_falla(self):
        with pytest.raises(ValueError):
            generar_resumen_ejecutivo(pregunta="", enunciado="X")

    def test_enunciado_vacio_falla(self):
        with pytest.raises(ValueError):
            generar_resumen_ejecutivo(pregunta="¿Pregunta?", enunciado="")

    @patch("src.ai.asistente_tema._generar")
    def test_incluye_enunciado_en_prompt(self, mock_generar):
        mock_generar.return_value = "# Resumen"
        generar_resumen_ejecutivo(
            pregunta="¿Pregunta?",
            enunciado="Informalidad laboral juvenil en México",
        )
        prompt = mock_generar.call_args.args[0]
        assert "Informalidad laboral juvenil en México" in prompt 