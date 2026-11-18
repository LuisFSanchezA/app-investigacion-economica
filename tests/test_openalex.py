"""Pruebas del conector de OpenAlex (con mock de requests)."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.fuentes.openalex import OpenAlex


# --------------------------- Fixtures ------------------------------------

def _respuesta_openalex(items: list[dict], next_cursor: str | None = None) -> dict:
    return {
        "meta": {
            "count": len(items),
            "page": 1,
            "per_page": 200,
            "next_cursor": next_cursor,
        },
        "results": items,
    }


def _trabajo_ejemplo(
    id_: str = "https://openalex.org/W1",
    doi: str | None = "https://doi.org/10.1234/abc",
    titulo: str = "Informalidad laboral en México",
    anio: int = 2020,
    citas: int = 10,
    tipo: str = "article",
    idioma: str = "es",
    oa: bool = True,
) -> dict:
    return {
        "id": id_,
        "doi": doi,
        "title": titulo,
        "display_name": titulo,
        "publication_year": anio,
        "cited_by_count": citas,
        "type": tipo,
        "language": idioma,
        "open_access": {"is_oa": oa},
        "authorships": [
            {
                "author": {"display_name": "Ana Pérez"},
                "institutions": [
                    {"display_name": "UNAM", "country_code": "MX"}
                ],
            },
            {
                "author": {"display_name": "Luis Sánchez"},
                "institutions": [
                    {"display_name": "UNAM", "country_code": "MX"},
                    {"display_name": "Banxico", "country_code": "MX"},
                ],
            },
        ],
        "primary_location": {
            "source": {"display_name": "Economía Mexicana"}
        },
        "concepts": [
            {"display_name": "Informalidad", "score": 0.9},
            {"display_name": "Mercado laboral", "score": 0.8},
        ],
        "referenced_works": ["https://openalex.org/W9"],
        "abstract_inverted_index": {
            "Este": [0],
            "es": [1],
            "un": [2],
            "resumen": [3],
        },
    }


# --------------------------- Tests ---------------------------------------

class TestNormalizacion:
    def test_normaliza_columnas_basicas(self):
        conector = OpenAlex()
        df = conector._normalizar([_trabajo_ejemplo()])
        assert list(df.columns) == [
            "id", "doi", "titulo", "autores", "instituciones", "paises",
            "anio", "tipo", "fuente", "idioma", "citas", "open_access",
            "conceptos", "n_referencias", "referencias", "resumen",
        ]
        assert df.iloc[0]["titulo"] == "Informalidad laboral en México"
        assert df.iloc[0]["anio"] == 2020
        assert df.iloc[0]["citas"] == 10

    def test_autores_e_instituciones_unicas(self):
        conector = OpenAlex()
        df = conector._normalizar([_trabajo_ejemplo()])
        assert df.iloc[0]["autores"] == "Ana Pérez; Luis Sánchez"
        assert df.iloc[0]["instituciones"] == "UNAM; Banxico"
        assert df.iloc[0]["paises"] == "MX"

    def test_reconstruye_resumen(self):
        conector = OpenAlex()
        df = conector._normalizar([_trabajo_ejemplo()])
        assert df.iloc[0]["resumen"] == "Este es un resumen"

    def test_conceptos_ordenados_por_score(self):
        conector = OpenAlex()
        df = conector._normalizar([_trabajo_ejemplo()])
        assert df.iloc[0]["conceptos"] == "Informalidad; Mercado laboral"


class TestDeduplicacion:
    def test_deduplica_por_doi(self):
        conector = OpenAlex()
        df = pd.DataFrame([
            {"doi": "https://doi.org/10.1/a", "titulo": "A"},
            {"doi": "https://doi.org/10.1/a", "titulo": "A duplicado"},
            {"doi": "https://doi.org/10.1/b", "titulo": "B"},
        ])
        resultado = conector._deduplicar(df)
        assert len(resultado) == 2
        assert "A duplicado" not in resultado["titulo"].values

    def test_deduplica_por_titulo_si_no_hay_doi(self):
        conector = OpenAlex()
        df = pd.DataFrame([
            {"doi": "", "titulo": "Informalidad  laboral"},
            {"doi": "", "titulo": "informalidad laboral"},
            {"doi": "", "titulo": "Otro título"},
        ])
        resultado = conector._deduplicar(df)
        assert len(resultado) == 2

    def test_df_vacio(self):
        conector = OpenAlex()
        df = pd.DataFrame(columns=["doi", "titulo"])
        resultado = conector._deduplicar(df)
        assert resultado.empty


class TestBuscar:
    @patch("src.fuentes.openalex.requests.get")
    def test_busqueda_exitosa(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _respuesta_openalex(
            [_trabajo_ejemplo(), _trabajo_ejemplo(id_="W2", doi="https://doi.org/10.1/xyz")]
        )
        mock_get.return_value = mock_resp

        conector = OpenAlex()
        df, meta = conector.buscar(
            keywords=["informalidad laboral"],
            desde=2015,
            hasta=2025,
            limite=10,
        )

        assert len(df) == 2
        assert meta.fuente == "OpenAlex"
        assert "informalidad laboral" in meta.indicador

    @patch("src.fuentes.openalex.requests.get")
    def test_sin_keywords_falla(self, mock_get):
        conector = OpenAlex()
        with pytest.raises(ValueError):
            conector.buscar(keywords=[])

    @patch("src.fuentes.openalex.requests.get")
    def test_rango_invertido_falla(self, mock_get):
        conector = OpenAlex()
        with pytest.raises(ValueError):
            conector.buscar(
                keywords=["x"], desde=2025, hasta=2015
            )

    @patch("src.fuentes.openalex.requests.get")
    def test_error_http(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        conector = OpenAlex()
        with pytest.raises(ConnectionError):
            conector.buscar(keywords=["x"])

    @patch("src.fuentes.openalex.requests.get")
    def test_respuesta_vacia(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _respuesta_openalex([])
        mock_get.return_value = mock_resp

        conector = OpenAlex()
        with pytest.raises(ValueError):
            conector.buscar(keywords=["algo sin resultados"])

    @patch("src.fuentes.openalex.requests.get")
    def test_timeout(self, mock_get):
        import requests as req
        mock_get.side_effect = req.exceptions.Timeout()

        conector = OpenAlex()
        with pytest.raises(ConnectionError):
            conector.buscar(keywords=["x"])