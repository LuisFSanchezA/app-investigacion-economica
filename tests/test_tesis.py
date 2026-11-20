"""Pruebas del conector de tesis."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.fuentes.tesis import REPOSITORIOS, Tesis


@pytest.fixture
def df_tesis():
    return pd.DataFrame([
        {
            "titulo": "Informalidad laboral en México: un análisis de género",
            "autores": "Ana Pérez",
            "anio": 2020,
            "tipo": "dissertation",
            "citas": 3,
            "instituciones": "UNAM",
            "paises": "MX",
            "fuente": "UNAM",
            "idioma": "es",
            "doi": "",
            "conceptos": "informalidad; género",
            "open_access": True,
        },
    ])


class TestEnlacesRepositorios:
    def test_tesunam(self):
        url = Tesis._enlace_repositorio("TesiuNAM", "Informalidad laboral")
        assert "tesiunam" in url.lower()
        assert "Informalidad" in url or "informalidad" in url

    def test_dialnet(self):
        url = Tesis._enlace_repositorio("Dialnet", "Informalidad laboral")
        assert "dialnet" in url.lower()

    def test_riud(self):
        url = Tesis._enlace_repositorio("RIUD", "Informalidad laboral")
        assert "riud" in url.lower()

    def test_titulo_vacio(self):
        url = Tesis._enlace_repositorio("TesiuNAM", "")
        assert url == ""

    def test_titulo_muy_largo_se_trunca(self):
        titulo = "A" * 200
        url = Tesis._enlace_repositorio("TesiuNAM", titulo)
        # El título truncado a 80 chars
        assert len(url) < 500

    def test_repositorio_inexistente(self):
        url = Tesis._enlace_repositorio("NoExiste", "Título")
        assert url == ""


class TestEnlacesPrefabricados:
    def test_genera_3_enlaces(self):
        enlaces = Tesis.enlaces_prefabricados(["informalidad laboral"])
        assert len(enlaces) == 3
        assert "TesiuNAM" in enlaces
        assert "Dialnet" in enlaces
        assert "RIUD" in enlaces

    def test_query_en_url(self):
        enlaces = Tesis.enlaces_prefabricados(["informalidad", "laboral"])
        for url in enlaces.values():
            assert "informalidad" in url.lower()

    def test_lista_vacia(self):
        enlaces = Tesis.enlaces_prefabricados([])
        assert enlaces == {}


class TestBuscar:
    @patch("src.fuentes.tesis.OpenAlex")
    def test_exitoso(self, mock_openalex_cls, df_tesis):
        mock_conector = MagicMock()
        mock_meta = MagicMock()
        mock_meta.notas = ""
        mock_conector.buscar.return_value = (df_tesis, mock_meta)
        mock_openalex_cls.return_value = mock_conector

        conector = Tesis()
        df, meta = conector.buscar(keywords=["informalidad"], limite=10)

        assert len(df) == 1
        assert "enlace_tesunam" in df.columns
        assert "enlace_dialnet" in df.columns
        assert "enlace_riud" in df.columns
        assert "nivel" in df.columns

    @patch("src.fuentes.tesis.OpenAlex")
    def test_fuerza_tipo_dissertation(self, mock_openalex_cls, df_tesis):
        mock_conector = MagicMock()
        mock_conector.buscar.return_value = (df_tesis, MagicMock())
        mock_openalex_cls.return_value = mock_conector

        conector = Tesis()
        conector.buscar(keywords=["informalidad"])

        # Verificar que se llamó con tipos=["dissertation"]
        call_args = mock_conector.buscar.call_args
        assert call_args.kwargs["tipos"] == ["dissertation"]

    def test_sin_keywords_falla(self):
        conector = Tesis()
        with pytest.raises(ValueError):
            conector.buscar(keywords=[])

    def test_keywords_vacias_falla(self):
        conector = Tesis()
        with pytest.raises(ValueError):
            conector.buscar(keywords=["", "  "])


class TestCatalogo:
    def test_repositorios_definidos(self):
        assert "TesiuNAM" in REPOSITORIOS
        assert "Dialnet" in REPOSITORIOS
        assert "RIUD" in REPOSITORIOS

    def test_descripciones(self):
        desc = Tesis.descripcion_repositorios()
        assert len(desc) == 3
        assert "UNAM" in desc["TesiuNAM"]