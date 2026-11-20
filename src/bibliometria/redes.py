"""Redes bibliométricas: co-autoría, co-palabras y co-citas.

Todas las funciones devuelven un `nx.Graph` o `nx.DiGraph` listo para
ser visualizado por `graficas_redes.py`.

Convención:
- Nodos: strings (nombre de autor, palabra clave, id de trabajo).
- Aristas: peso = nº de co-ocurrencias.
- Atributos de nodo: `n_trabajos` (frecuencia) cuando aplique.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import combinations

import networkx as nx
import pandas as pd


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _separar_lista(valor: str | None) -> list[str]:
    """Separa un string con '; ' en lista de strings limpios."""
    if not valor or not isinstance(valor, str):
        return []
    return [x.strip() for x in valor.split(";") if x.strip()]


def _validar_columnas(df: pd.DataFrame, requeridas: list[str]) -> None:
    faltantes = [c for c in requeridas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas en el corpus: {faltantes}")


# ---------------------------------------------------------------------------
# Red de co-autoría
# ---------------------------------------------------------------------------

def red_coautoria(df: pd.DataFrame, min_peso: int = 1) -> nx.Graph:
    """Construye una red de co-autoría.

    Nodos = autores. Arista entre dos autores si firman al menos un
    trabajo juntos. Peso = nº de trabajos en común.

    Parámetros
    ----------
    df : pd.DataFrame
        Corpus con columna `autores` (separados por '; ').
    min_peso : int
        Peso mínimo de arista para incluirla (default 1).

    Devuelve
    -------
    nx.Graph con atributos:
        - nodo: `n_trabajos` (frecuencia del autor en el corpus)
        - arista: `weight` (nº de co-firmas)
    """
    _validar_columnas(df, ["autores"])
    if df.empty:
        raise ValueError("El corpus está vacío.")

    grafo = nx.Graph()
    frecuencia: Counter = Counter()

    for _, row in df.iterrows():
        autores = _separar_lista(row.get("autores", ""))
        if len(autores) < 1:
            continue
        # Frecuencia individual
        for a in autores:
            frecuencia[a] += 1
        # Co-autoría: pares
        if len(autores) >= 2:
            for a, b in combinations(sorted(set(autores)), 2):
                if grafo.has_edge(a, b):
                    grafo[a][b]["weight"] += 1
                else:
                    grafo.add_edge(a, b, weight=1)

    # Añadir nodos aislados (autores que no co-firman con nadie)
    for autor, n in frecuencia.items():
        if autor not in grafo:
            grafo.add_node(autor)
        grafo.nodes[autor]["n_trabajos"] = n

    # Filtrar aristas por peso mínimo
    if min_peso > 1:
        aristas_a_borrar = [
            (u, v) for u, v, d in grafo.edges(data=True) if d["weight"] < min_peso
        ]
        grafo.remove_edges_from(aristas_a_borrar)

    return grafo


# ---------------------------------------------------------------------------
# Red de co-palabras clave (conceptos)
# ---------------------------------------------------------------------------

def red_copalabras(df: pd.DataFrame, min_peso: int = 1) -> nx.Graph:
    """Construye una red de co-ocurrencia de conceptos/palabras clave.

    Nodos = conceptos. Arista entre dos conceptos si aparecen juntos en
    al menos un trabajo. Peso = nº de trabajos en que co-ocurren.

    Parámetros
    ----------
    df : pd.DataFrame
        Corpus con columna `conceptos` (separados por '; ').
    min_peso : int
        Peso mínimo de arista (default 1).

    Devuelve
    -------
    nx.Graph con atributos:
        - nodo: `n_trabajos` (frecuencia del concepto)
        - arista: `weight`
    """
    _validar_columnas(df, ["conceptos"])
    if df.empty:
        raise ValueError("El corpus está vacío.")

    grafo = nx.Graph()
    frecuencia: Counter = Counter()

    for _, row in df.iterrows():
        conceptos = _separar_lista(row.get("conceptos", ""))
        if len(conceptos) < 1:
            continue
        for c in conceptos:
            frecuencia[c] += 1
        if len(conceptos) >= 2:
            for a, b in combinations(sorted(set(conceptos)), 2):
                if grafo.has_edge(a, b):
                    grafo[a][b]["weight"] += 1
                else:
                    grafo.add_edge(a, b, weight=1)

    for concepto, n in frecuencia.items():
        if concepto not in grafo:
            grafo.add_node(concepto)
        grafo.nodes[concepto]["n_trabajos"] = n

    if min_peso > 1:
        aristas_a_borrar = [
            (u, v) for u, v, d in grafo.edges(data=True) if d["weight"] < min_peso
        ]
        grafo.remove_edges_from(aristas_a_borrar)

    return grafo


# ---------------------------------------------------------------------------
# Métricas de red
# ---------------------------------------------------------------------------

def metricas_red(grafo: nx.Graph) -> dict:
    """Devuelve métricas básicas de una red.

    Devuelve
    -------
    dict con:
        - n_nodos, n_aristas
        - densidad
        - n_componentes
        - nodo_mas_conectado (grado)
        - grado_medio
    """
    if grafo.number_of_nodes() == 0:
        return {
            "n_nodos": 0,
            "n_aristas": 0,
            "densidad": 0.0,
            "n_componentes": 0,
            "nodo_mas_conectado": None,
            "grado_medio": 0.0,
        }

    grados = dict(grafo.degree())
    nodo_top = max(grados, key=grados.get) if grados else None

    return {
        "n_nodos": grafo.number_of_nodes(),
        "n_aristas": grafo.number_of_edges(),
        "densidad": round(nx.density(grafo), 4),
        "n_componentes": nx.number_connected_components(grafo),
        "nodo_mas_conectado": nodo_top,
        "grado_medio": round(sum(grados.values()) / len(grados), 2) if grados else 0.0,
    }


def nodos_centrales(grafo: nx.Graph, n: int = 10) -> pd.DataFrame:
    """Top N nodos por grado (nº de conexiones).

    Devuelve DataFrame con: nodo, grado, n_trabajos.
    """
    if grafo.number_of_nodes() == 0:
        return pd.DataFrame(columns=["nodo", "grado", "n_trabajos"])

    filas = []
    for nodo, grado in grafo.degree():
        filas.append({
            "nodo": nodo,
            "grado": grado,
            "n_trabajos": grafo.nodes[nodo].get("n_trabajos", 0),
        })
    df = pd.DataFrame(filas)
    df = df.sort_values(["grado", "n_trabajos", "nodo"], ascending=[False, False, True])
    return df.head(n).reset_index(drop=True)