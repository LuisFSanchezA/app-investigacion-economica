"""Pruebas del asistente de investigación (Pregunta).

Con la capa de proveedor, ya no se mockea Gemini directamente:
se mockea `_generar` (la función interna del asistente que llama a
`generar_con_fallback`). Así los tests no dependen de qué proveedor
esté detrás.
"""

from unittest.mock import patch

import pytest

from src.ai import asistente


# ---------------------------------------------------------------------------
# sugerir_preguntas
# ---------------------------------------------------------------------------

class TestSugerirPreguntas:
    @patch("src.ai.asistente._generar")
    def test_exitoso(self, mock_generar):
        mock_generar.return_value = (
            "1. Pregunta A\n2. Pregunta B\n3. Pregunta C"
        )
        resultado = asistente.sugerir_preguntas("informalidad laboral")
        assert "Pregunta A" in resultado
        assert "Pregunta B" in resultado
        mock_generar.assert_called_once()

    def test_tema_vacio_falla(self):
        with pytest.raises(ValueError, match="tema"):
            asistente.sugerir_preguntas("")

    def test_solo_espacios_falla(self):
        with pytest.raises(ValueError, match="tema"):
            asistente.sugerir_preguntas("   ")

    @patch("src.ai.asistente._generar")
    def test_incluye_tema_en_prompt(self, mock_generar):
        mock_generar.return_value = "1. X"
        asistente.sugerir_preguntas("informalidad laboral")
        prompt = mock_generar.call_args.args[0]
        assert "informalidad laboral" in prompt

    @patch("src.ai.asistente._generar")
    def test_propaga_connection_error(self, mock_generar):
        mock_generar.side_effect = ConnectionError("saturado")
        with pytest.raises(ConnectionError, match="saturado"):
            asistente.sugerir_preguntas("informalidad")


# ---------------------------------------------------------------------------
# sugerir_objetivos
# ---------------------------------------------------------------------------

class TestSugerirObjetivos:
    @patch("src.ai.asistente._generar")
    def test_exitoso(self, mock_generar):
        mock_generar.return_value = (
            "Objetivo general: ...\nObjetivos específicos: 1. ... 2. ..."
        )
        resultado = asistente.sugerir_objetivos(
            "¿Cómo evolucionó la informalidad?"
        )
        assert "Objetivo general" in resultado

    def test_pregunta_vacia_falla(self):
        with pytest.raises(ValueError, match="pregunta"):
            asistente.sugerir_objetivos("")

    @patch("src.ai.asistente._generar")
    def test_propaga_value_error(self, mock_generar):
        mock_generar.side_effect = ValueError("respuesta vacía")
        with pytest.raises(ValueError, match="vacía"):
            asistente.sugerir_objetivos("¿Pregunta?")


# ---------------------------------------------------------------------------
# generar_protocolo
# ---------------------------------------------------------------------------

class TestGenerarProtocolo:
    @patch("src.ai.asistente._generar")
    def test_exitoso(self, mock_generar):
        mock_generar.return_value = "# Protocolo\n## 1. Título\n..."
        resultado = asistente.generar_protocolo(
            tema="informalidad",
            pregunta="¿Cómo evolucionó?",
            objetivos="Analizar...",
        )
        assert "Protocolo" in resultado

    def test_sin_tema_falla(self):
        with pytest.raises(ValueError):
            asistente.generar_protocolo("", "pregunta", "objetivos")

    def test_sin_pregunta_falla(self):
        with pytest.raises(ValueError):
            asistente.generar_protocolo("tema", "", "objetivos")

    @patch("src.ai.asistente._generar")
    def test_incluye_objetivos_pendientes(self, mock_generar):
        mock_generar.return_value = "# Protocolo"
        asistente.generar_protocolo("tema", "pregunta", "")
        prompt = mock_generar.call_args.args[0]
        assert "(pendiente)" in prompt  