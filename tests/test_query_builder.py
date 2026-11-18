"""Pruebas del generador de queries bibliográficas."""

import pytest

from src.bibliometria.query_builder import (
    construir_query_google_scholar,
    construir_query_openalex,
    construir_query_scopus,
    construir_query_wos,
    formatear_keywords,
)


# --------------------------- formatear_keywords ---------------------------

class TestFormatearKeywords:
    def test_lista_simple(self):
        assert formatear_keywords(["informalidad", "empleo"]) == [
            "informalidad",
            "empleo",
        ]

    def test_frases_con_espacios_se_entrecomillan(self):
        assert formatear_keywords(["informalidad laboral"]) == [
            '"informalidad laboral"'
        ]

    def test_deduplica_case_insensitive(self):
        assert formatear_keywords(["Empleo", "empleo", "EMPLEO"]) == ["Empleo"]

    def test_quita_espacios_sobrantes(self):
        assert formatear_keywords(["  informalidad   laboral  "]) == [
            '"informalidad laboral"'
        ]

    def test_descarta_vacias(self):
        assert formatear_keywords(["", "  ", "empleo"]) == ["empleo"]

    def test_lista_vacia(self):
        assert formatear_keywords([]) == []


# ------------------------------ WoS --------------------------------------

class TestQueryWoS:
    def test_basica(self):
        q = construir_query_wos(["informalidad laboral"], desde=2015, hasta=2025)
        assert "TS=(" in q
        assert '"informalidad laboral"' in q
        assert "PY=(2015-2025)" in q
        assert "AND" in q

    def test_con_tipos_e_idiomas(self):
        q = construir_query_wos(
            ["informalidad"],
            desde=2015,
            hasta=2025,
            tipos=["Article", "Review"],
            idiomas=["Spanish", "English"],
        )
        assert "DT=(Article OR Review)" in q
        assert "LA=(Spanish OR English)" in q

    def test_sin_keywords_falla(self):
        with pytest.raises(ValueError):
            construir_query_wos([], desde=2015, hasta=2025)

    def test_rango_invertido_falla(self):
        with pytest.raises(ValueError):
            construir_query_wos(["x"], desde=2025, hasta=2015)


# ------------------------------ Scopus -----------------------------------

class TestQueryScopus:
    def test_basica(self):
        q = construir_query_scopus(["informalidad"], desde=2015, hasta=2025)
        assert "TITLE-ABS-KEY(" in q
        assert "PUBYEAR > 2014" in q
        assert "PUBYEAR < 2026" in q

    def test_con_tipos_e_idiomas(self):
        q = construir_query_scopus(
            ["informalidad"],
            desde=2015,
            hasta=2025,
            tipos=["ar", "re"],
            idiomas=["spa", "eng"],
        )
        assert "DOCTYPE(ar OR re)" in q
        assert "LANGUAGE(spa OR eng)" in q


# ------------------------------ OpenAlex ---------------------------------

class TestQueryOpenAlex:
    def test_basica(self):
        q = construir_query_openalex(["informalidad laboral"], desde=2015, hasta=2025)
        assert "informalidad laboral" in q
        assert "from_publication_date:2015-01-01" in q
        assert "to_publication_date:2025-12-31" in q

    def test_con_tipos_e_idiomas(self):
        q = construir_query_openalex(
            ["informalidad"],
            desde=2015,
            hasta=2025,
            tipos=["article", "review"],
            idiomas=["es", "en"],
        )
        assert "type:article|review" in q
        assert "language:es|en" in q

    def test_sin_keywords_falla(self):
        with pytest.raises(ValueError):
            construir_query_openalex([], desde=2015, hasta=2025)


# -------------------------- Google Scholar -------------------------------

class TestQueryGoogleScholar:
    def test_basica(self):
        q = construir_query_google_scholar(["informalidad"], desde=2015, hasta=2025)
        assert "informalidad" in q
        assert "2015-2025" in q

    def test_sin_keywords_falla(self):
        with pytest.raises(ValueError):
            construir_query_google_scholar([])