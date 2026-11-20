"""Pruebas de las métricas bibliométricas."""

import pandas as pd
import pytest

from src.bibliometria.metricas import (
    distribucion_citas,
    ley_bradford,
    ley_lotka,
    produccion_por_anio,
    resumen_general,
    top_autores,
    top_conceptos,
    top_fuentes,
    top_instituciones,
    top_paises,
)


@pytest.fixture
def corpus_ejemplo():
    return pd.DataFrame([
        {"titulo": "A", "anio": 2020, "autores": "Ana; Luis", "instituciones": "UNAM", "paises": "MX", "fuente": "Revista X", "citas": 10, "tipo": "article", "conceptos": "informalidad; empleo", "open_access": True},
        {"titulo": "B", "anio": 2021, "autores": "Ana; María", "instituciones": "UNAM; Banxico", "paises": "MX", "fuente": "Revista X", "citas": 5, "tipo": "article", "conceptos": "informalidad", "open_access": False},
        {"titulo": "C", "anio": 2021, "autores": "Luis", "instituciones": "IPN", "paises": "MX", "fuente": "Revista Y", "citas": 2, "tipo": "review", "conceptos": "empleo", "open_access": True},
        {"titulo": "D", "anio": 2022, "autores": "María; Pedro", "instituciones": "IPN", "paises": "MX; US", "fuente": "Revista Z", "citas": 1, "tipo": "article", "conceptos": "género", "open_access": False},
    ])


class TestResumenGeneral:
    def test_metricas_basicas(self, corpus_ejemplo):
        r = resumen_general(corpus_ejemplo)
        assert r["n_trabajos"] == 4
        assert r["anio_min"] == 2020
        assert r["anio_max"] == 2022
        assert r["citas_total"] == 18
        assert r["h_index"] == 2
        assert r["pct_open_access"] == 50.0
        assert r["n_autores_unicos"] == 4  # Ana, Luis, María, Pedro
        assert r["n_fuentes_unicas"] == 3  # X, Y, Z

    def test_corpus_vacio_falla(self):
        with pytest.raises(ValueError):
            resumen_general(pd.DataFrame())

    def test_faltan_columnas_falla(self):
        with pytest.raises(ValueError):
            resumen_general(pd.DataFrame([{"titulo": "A"}]))


class TestProduccionAnual:
    def test_agrupa_por_anio(self, corpus_ejemplo):
        df = produccion_por_anio(corpus_ejemplo)
        assert list(df["anio"]) == [2020, 2021, 2022]
        assert list(df["n_trabajos"]) == [1, 2, 1]
        assert list(df["citas_total"]) == [10, 7, 1]


class TestTopAutores:
    def test_top_3(self, corpus_ejemplo):
        df = top_autores(corpus_ejemplo, n=3)
        # Ana y Luis empatan a 2 trabajos; el desempate es por citas
        # (Ana tiene 15, Luis tiene 12) y luego por nombre.
        assert df.iloc[0]["autor"] == "Ana"
        assert df.iloc[0]["n_trabajos"] == 2

    def test_orden_determinista(self, corpus_ejemplo):
        """El orden debe ser estable entre ejecuciones."""
        df1 = top_autores(corpus_ejemplo, n=5)
        df2 = top_autores(corpus_ejemplo, n=5)
        assert list(df1["autor"]) == list(df2["autor"])


class TestTopInstituciones:
    def test_top_3(self, corpus_ejemplo):
        df = top_instituciones(corpus_ejemplo, n=3)
        assert df.iloc[0]["n_trabajos"] == 2


class TestTopPaises:
    def test_mx_es_primero(self, corpus_ejemplo):
        df = top_paises(corpus_ejemplo)
        assert df.iloc[0]["pais"] == "MX"
        assert df.iloc[0]["n_trabajos"] == 4


class TestTopFuentes:
    def test_revista_x_primera(self, corpus_ejemplo):
        df = top_fuentes(corpus_ejemplo)
        assert df.iloc[0]["fuente"] == "Revista X"
        assert df.iloc[0]["n_trabajos"] == 2


class TestTopConceptos:
    def test_informalidad_y_empleo(self, corpus_ejemplo):
        df = top_conceptos(corpus_ejemplo, n=5)
        conceptos = list(df["concepto"])
        assert "informalidad" in conceptos
        assert "empleo" in conceptos


class TestBradford:
    def test_zonas(self, corpus_ejemplo):
        df = ley_bradford(corpus_ejemplo)
        assert not df.empty
        assert "zona" in df.columns
        assert df["n_trabajos"].sum() == 4

    def test_corpus_sin_fuentes(self):
        df = pd.DataFrame({"fuente": ["", "", ""]})
        resultado = ley_bradford(df)
        assert resultado.empty


class TestLotka:
    def test_distribucion(self, corpus_ejemplo):
        df = ley_lotka(corpus_ejemplo)
        assert not df.empty
        # Ana tiene 2, los demás 1
        assert df["n_autores"].sum() == 4


class TestDistribucionCitas:
    def test_columnas(self, corpus_ejemplo):
        df = distribucion_citas(corpus_ejemplo)
        assert list(df.columns) == ["anio", "citas", "titulo"]
        assert len(df) == 4