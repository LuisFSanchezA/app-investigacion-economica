"""Pruebas del asistente de IA para Literatura."""

from unittest.mock import patch

import pandas as pd
import pytest

from src.ai.asistente_literatura import (
    clasificar_papers,
    detectar_vacios,
    evaluar_corpus,
    sintetizar_corpus,
    sugerir_keywords,
)


# ---------------------------------------------------------------------------
# sugerir_keywords
# ---------------------------------------------------------------------------

class TestSugerirKeywords:
    @patch("src.ai.asistente_literatura._generar")
    def test_exitoso(self, mock_generar):
        mock_generar.return_value = "## Keywords\n- informalidad (informality)"
        resultado = sugerir_keywords("informalidad laboral en México")
        assert "informalidad" in resultado.lower()

    def test_tema_vacio_falla(self):
        with pytest.raises(ValueError):
            sugerir_keywords("")

    def test_solo_espacios_falla(self):
        with pytest.raises(ValueError):
            sugerir_keywords("   ")

    @patch("src.ai.asistente_literatura._generar")
    def test_incluye_pregunta_en_prompt(self, mock_generar):
        mock_generar.return_value = "## Keywords"
        sugerir_keywords("informalidad", pregunta="¿Cómo afecta el salario?")
        prompt = mock_generar.call_args.args[0]
        assert "informalidad" in prompt
        assert "salario" in prompt

    @patch("src.ai.asistente_literatura._generar")
    def test_propaga_connection_error(self, mock_generar):
        mock_generar.side_effect = ConnectionError("saturado")
        with pytest.raises(ConnectionError, match="saturado"):
            sugerir_keywords("informalidad")


# ---------------------------------------------------------------------------
# evaluar_corpus
# ---------------------------------------------------------------------------

class TestEvaluarCorpus:
    def _corpus(self):
        return pd.DataFrame([
            {"titulo": "Informalidad en México", "anio": 2020, "tipo": "article", "citas": 10},
            {"titulo": "Labor informality", "anio": 2018, "tipo": "review", "citas": 5},
        ])

    @patch("src.ai.asistente_literatura._generar")
    def test_exitoso(self, mock_generar):
        mock_generar.return_value = "## Diagnóstico\n..."
        resultado = evaluar_corpus("¿Qué determina la informalidad?", self._corpus())
        assert "Diagnóstico" in resultado

    def test_pregunta_vacia_falla(self):
        with pytest.raises(ValueError):
            evaluar_corpus("", self._corpus())

    def test_corpus_vacio_falla(self):
        with pytest.raises(ValueError):
            evaluar_corpus("¿Pregunta?", pd.DataFrame())

    def test_columnas_faltantes_falla(self):
        df = pd.DataFrame([{"titulo": "X", "anio": 2020}])
        with pytest.raises(ValueError, match="columnas"):
            evaluar_corpus("¿Pregunta?", df)

    @patch("src.ai.asistente_literatura._generar")
    def test_limita_a_40_trabajos(self, mock_generar):
        mock_generar.return_value = "## Diagnóstico"
        df = pd.DataFrame([
            {"titulo": f"T{i}", "anio": 2000 + i, "tipo": "article", "citas": i}
            for i in range(50)
        ])
        evaluar_corpus("¿Pregunta?", df)
        prompt = mock_generar.call_args.args[0]
        assert "Se muestran 40 de 50" in prompt


# ---------------------------------------------------------------------------
# Funciones avanzadas (F4)
# ---------------------------------------------------------------------------

class TestSintetizarCorpus:
    def _corpus(self):
        return pd.DataFrame([
            {"titulo": "Informalidad en México", "anio": 2020, "tipo": "article", "citas": 10, "conceptos": "informalidad"},
            {"titulo": "Labor informality", "anio": 2018, "tipo": "review", "citas": 5, "conceptos": "informalidad; empleo"},
        ])

    @patch("src.ai.asistente_literatura._generar")
    def test_exitoso(self, mock_generar):
        mock_generar.return_value = "## Temas dominantes\n..."
        resultado = sintetizar_corpus("¿Qué determina la informalidad?", self._corpus())
        assert "Temas dominantes" in resultado

    def test_pregunta_vacia_falla(self):
        with pytest.raises(ValueError):
            sintetizar_corpus("", self._corpus())

    def test_corpus_vacio_falla(self):
        with pytest.raises(ValueError):
            sintetizar_corpus("¿Pregunta?", pd.DataFrame())

    def test_sin_columna_titulo_falla(self):
        df = pd.DataFrame([{"anio": 2020}])
        with pytest.raises(ValueError, match="titulo"):
            sintetizar_corpus("¿Pregunta?", df)


class TestDetectarVacios:
    def _corpus(self):
        return pd.DataFrame([
            {"titulo": "Informalidad en México", "anio": 2020, "tipo": "article", "citas": 10, "conceptos": "informalidad"},
        ])

    @patch("src.ai.asistente_literatura._generar")
    def test_exitoso(self, mock_generar):
        mock_generar.return_value = "## Vacíos\n..."
        resultado = detectar_vacios("¿Qué determina la informalidad?", self._corpus())
        assert "Vacíos" in resultado

    def test_pregunta_vacia_falla(self):
        with pytest.raises(ValueError):
            detectar_vacios("", self._corpus())


class TestClasificarPapers:
    def _corpus(self):
        return pd.DataFrame([
            {"titulo": "Informalidad en México", "anio": 2020, "tipo": "article", "citas": 10, "conceptos": "informalidad"},
            {"titulo": "Teoría de la informalidad", "anio": 2015, "tipo": "book", "citas": 50, "conceptos": "teoría"},
        ])

    @patch("src.ai.asistente_literatura._generar")
    def test_exitoso(self, mock_generar):
        mock_generar.return_value = "| ID | Título | Categoría |\n|---|---|---|"
        resultado = clasificar_papers("¿Qué determina la informalidad?", self._corpus())
        assert "Categoría" in resultado

    def test_corpus_vacio_falla(self):
        with pytest.raises(ValueError):
            clasificar_papers("¿Pregunta?", pd.DataFrame()) 