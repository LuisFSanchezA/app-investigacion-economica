"""Pruebas de las redes bibliométricas."""

import networkx as nx
import pandas as pd
import pytest

from src.bibliometria.redes import (
    metricas_red,
    nodos_centrales,
    red_coautoria,
    red_copalabras,
)


@pytest.fixture
def corpus_ejemplo():
    return pd.DataFrame([
        {"autores": "Ana; Luis", "conceptos": "informalidad; empleo"},
        {"autores": "Ana; María", "conceptos": "informalidad"},
        {"autores": "Luis", "conceptos": "empleo"},
        {"autores": "María; Pedro", "conceptos": "género; informalidad"},
    ])


class TestRedCoautoria:
    def test_nodos_y_aristas(self, corpus_ejemplo):
        g = red_coautoria(corpus_ejemplo)
        assert "Ana" in g.nodes
        assert "Luis" in g.nodes
        assert g.has_edge("Ana", "Luis")
        assert g["Ana"]["Luis"]["weight"] == 1

    def test_peso_acumulado(self, corpus_ejemplo):
        # Ana y Luis firman juntos 1 vez
        g = red_coautoria(corpus_ejemplo)
        assert g["Ana"]["Luis"]["weight"] == 1

    def test_autor_solitario_es_nodo(self, corpus_ejemplo):
        g = red_coautoria(corpus_ejemplo)
        assert "Pedro" in g.nodes
        # Pedro solo firma con María, no está aislado
        assert g.degree("Pedro") == 1

    def test_frecuencia_nodos(self, corpus_ejemplo):
        g = red_coautoria(corpus_ejemplo)
        assert g.nodes["Ana"]["n_trabajos"] == 2
        assert g.nodes["Luis"]["n_trabajos"] == 2

    def test_min_peso_filtra(self, corpus_ejemplo):
        g = red_coautoria(corpus_ejemplo, min_peso=2)
        # Ninguna arista tiene peso 2, así que se borran todas
        assert g.number_of_edges() == 0
        # Pero los nodos se conservan
        assert g.number_of_nodes() == 4

    def test_corpus_vacio_falla(self):
        with pytest.raises(ValueError):
            red_coautoria(pd.DataFrame())


class TestRedCopalabras:
    def test_nodos_y_aristas(self, corpus_ejemplo):
        g = red_copalabras(corpus_ejemplo)
        assert "informalidad" in g.nodes
        assert "empleo" in g.nodes
        assert g.has_edge("informalidad", "empleo")

    def test_frecuencia(self, corpus_ejemplo):
        g = red_copalabras(corpus_ejemplo)
        assert g.nodes["informalidad"]["n_trabajos"] == 3
        assert g.nodes["empleo"]["n_trabajos"] == 2

    def test_corpus_vacio_falla(self):
        with pytest.raises(ValueError):
            red_copalabras(pd.DataFrame())


class TestMetricasRed:
    def test_metricas_basicas(self, corpus_ejemplo):
        g = red_coautoria(corpus_ejemplo)
        m = metricas_red(g)
        assert m["n_nodos"] == 4
        assert m["n_aristas"] == 3
        assert 0 < m["densidad"] < 1
        assert m["n_componentes"] == 1  # todos conectados

    def test_red_vacia(self):
        g = nx.Graph()
        m = metricas_red(g)
        assert m["n_nodos"] == 0
        assert m["densidad"] == 0.0

    def test_nodos_centrales(self, corpus_ejemplo):
        g = red_coautoria(corpus_ejemplo)
        df = nodos_centrales(g, n=3)
        assert len(df) <= 3
        assert "nodo" in df.columns
        assert "grado" in df.columns
        # Ana, Luis y María tienen grado 2; Pedro grado 1
        assert df.iloc[0]["grado"] == 2