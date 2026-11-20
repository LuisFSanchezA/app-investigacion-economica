"""Pruebas del asistente de IA para Literatura (con mock de Gemini)."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.ai.asistente_literatura import evaluar_corpus, sugerir_keywords


def _mock_cliente(texto: str = "## Keywords\n- informalidad (informality)"):
    cliente = MagicMock()
    respuesta = MagicMock()
    respuesta.text = texto
    cliente.models.generate_content.return_value = respuesta
    return cliente


# ----------------------- sugerir_keywords -------------------------------

class TestSugerirKeywords:
    @patch("src.ai.asistente_literatura._get_cliente")
    def test_exitoso(self, mock_get_cliente):
        mock_get_cliente.return_value = _mock_cliente()
        resultado = sugerir_keywords("informalidad laboral en México")
        assert "informalidad" in resultado.lower()

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_tema_vacio_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            sugerir_keywords("")

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_solo_espacios_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            sugerir_keywords("   ")

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_incluye_pregunta_en_prompt(self, mock_get_cliente):
        cliente = _mock_cliente()
        mock_get_cliente.return_value = cliente
        sugerir_keywords("informalidad", pregunta="¿Cómo afecta el salario?")
        # Verificar que el prompt contiene ambos
        prompt_usado = cliente.models.generate_content.call_args.kwargs["contents"]
        assert "informalidad" in prompt_usado
        assert "salario" in prompt_usado

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_error_401(self, mock_get_cliente):
        cliente = MagicMock()
        cliente.models.generate_content.side_effect = Exception("401 UNAUTHENTICATED")
        mock_get_cliente.return_value = cliente
        with pytest.raises(ConnectionError, match="API key"):
            sugerir_keywords("informalidad")

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_error_404(self, mock_get_cliente):
        cliente = MagicMock()
        cliente.models.generate_content.side_effect = Exception("404 NOT_FOUND")
        mock_get_cliente.return_value = cliente
        with pytest.raises(ConnectionError, match="modelo"):
            sugerir_keywords("informalidad")

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_error_429(self, mock_get_cliente):
        cliente = MagicMock()
        cliente.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED")
        mock_get_cliente.return_value = cliente
        with pytest.raises(ConnectionError, match="[Cc]uota"):
            sugerir_keywords("informalidad")


# ----------------------- evaluar_corpus ---------------------------------

class TestEvaluarCorpus:
    def _corpus(self):
        return pd.DataFrame([
            {"titulo": "Informalidad en México", "anio": 2020, "tipo": "article", "citas": 10},
            {"titulo": "Labor informality", "anio": 2018, "tipo": "review", "citas": 5},
        ])

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_exitoso(self, mock_get_cliente):
        mock_get_cliente.return_value = _mock_cliente("## Diagnóstico\n...")
        resultado = evaluar_corpus("¿Qué determina la informalidad?", self._corpus())
        assert "Diagnóstico" in resultado

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_pregunta_vacia_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            evaluar_corpus("", self._corpus())

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_corpus_vacio_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            evaluar_corpus("¿Pregunta?", pd.DataFrame())

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_columnas_faltantes_falla(self, mock_get_cliente):
        df = pd.DataFrame([{"titulo": "X", "anio": 2020}])  # falta tipo y citas
        with pytest.raises(ValueError, match="columnas"):
            evaluar_corpus("¿Pregunta?", df)

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_limita_a_40_trabajos(self, mock_get_cliente):
        cliente = _mock_cliente()
        mock_get_cliente.return_value = cliente
        df = pd.DataFrame([
            {"titulo": f"T{i}", "anio": 2000 + i, "tipo": "article", "citas": i}
            for i in range(50)
        ])
        evaluar_corpus("¿Pregunta?", df)
        prompt = cliente.models.generate_content.call_args.kwargs["contents"]
        assert "Se muestran 40 de 50" in prompt

# ----------------------- Funciones avanzadas (F4) -----------------------

from src.ai.asistente_literatura import (
    clasificar_papers,
    detectar_vacios,
    sintetizar_corpus,
)


class TestSintetizarCorpus:
    def _corpus(self):
        return pd.DataFrame([
            {"titulo": "Informalidad en México", "anio": 2020, "tipo": "article", "citas": 10, "conceptos": "informalidad"},
            {"titulo": "Labor informality", "anio": 2018, "tipo": "review", "citas": 5, "conceptos": "informalidad; empleo"},
        ])

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_exitoso(self, mock_get_cliente):
        mock_get_cliente.return_value = _mock_cliente("## Temas dominantes\n...")
        resultado = sintetizar_corpus("¿Qué determina la informalidad?", self._corpus())
        assert "Temas dominantes" in resultado

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_pregunta_vacia_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            sintetizar_corpus("", self._corpus())

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_corpus_vacio_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            sintetizar_corpus("¿Pregunta?", pd.DataFrame())

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_sin_columna_titulo_falla(self, mock_get_cliente):
        df = pd.DataFrame([{"anio": 2020}])
        with pytest.raises(ValueError, match="titulo"):
            sintetizar_corpus("¿Pregunta?", df)


class TestDetectarVacios:
    def _corpus(self):
        return pd.DataFrame([
            {"titulo": "Informalidad en México", "anio": 2020, "tipo": "article", "citas": 10, "conceptos": "informalidad"},
        ])

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_exitoso(self, mock_get_cliente):
        mock_get_cliente.return_value = _mock_cliente("## Vacíos\n...")
        resultado = detectar_vacios("¿Qué determina la informalidad?", self._corpus())
        assert "Vacíos" in resultado

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_pregunta_vacia_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            detectar_vacios("", self._corpus())


class TestClasificarPapers:
    def _corpus(self):
        return pd.DataFrame([
            {"titulo": "Informalidad en México", "anio": 2020, "tipo": "article", "citas": 10, "conceptos": "informalidad"},
            {"titulo": "Teoría de la informalidad", "anio": 2015, "tipo": "book", "citas": 50, "conceptos": "teoría"},
        ])

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_exitoso(self, mock_get_cliente):
        mock_get_cliente.return_value = _mock_cliente("| ID | Título | Categoría |\n|---|---|---|")
        resultado = clasificar_papers("¿Qué determina la informalidad?", self._corpus())
        assert "Categoría" in resultado

    @patch("src.ai.asistente_literatura._get_cliente")
    def test_corpus_vacio_falla(self, mock_get_cliente):
        with pytest.raises(ValueError):
            clasificar_papers("¿Pregunta?", pd.DataFrame())