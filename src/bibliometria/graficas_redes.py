"""Gráficas Plotly para redes bibliométricas.

Convierte un `nx.Graph` en una figura Plotly interactiva.
Usa layout spring (force-directed) por defecto.
"""

from __future__ import annotations

import networkx as nx
import plotly.graph_objects as go

PALETA = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]


def grafica_red(
    grafo: nx.Graph,
    titulo: str,
    max_nodos: int = 50,
) -> go.Figure:
    """Convierte un grafo en figura Plotly interactiva.

    Parámetros
    ----------
    grafo : nx.Graph
    titulo : str
    max_nodos : int
        Si el grafo tiene más nodos, se queda con los de mayor grado.

    Devuelve
    -------
    go.Figure
    """
    if grafo.number_of_nodes() == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Red vacía", xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
        )
        fig.update_layout(xaxis={"visible": False}, yaxis={"visible": False})
        return fig

    # Limitar nodos
    if grafo.number_of_nodes() > max_nodos:
        grados = dict(grafo.degree())
        top = sorted(grados, key=grados.get, reverse=True)[:max_nodos]
        grafo = grafo.subgraph(top).copy()

    # Layout
    pos = nx.spring_layout(grafo, seed=42, k=0.5)

    # Aristas
    edge_x, edge_y = [], []
    for u, v in grafo.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    # Nodos
    node_x, node_y, node_text, node_size, node_color = [], [], [], [], []
    for nodo in grafo.nodes():
        x, y = pos[nodo]
        node_x.append(x)
        node_y.append(y)
        grado = grafo.degree(nodo)
        n_trabajos = grafo.nodes[nodo].get("n_trabajos", 0)
        node_text.append(f"{nodo}<br>Grado: {grado}<br>Trabajos: {n_trabajos}")
        node_size.append(10 + 3 * grado)
        node_color.append(PALETA[grado % len(PALETA)])

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        hoverinfo="text",
        text=[n for n in grafo.nodes()],
        textposition="top center",
        textfont=dict(size=8),
        hovertext=node_text,
        marker=dict(
            size=node_size,
            color=node_color,
            line=dict(width=1, color="#333"),
        ),
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=titulo,
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )
    return fig