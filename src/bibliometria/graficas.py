"""Gráficas Plotly para la sección Bibliometría.

Cada función recibe un DataFrame ya calculado por `metricas.py`
y devuelve una figura Plotly lista para `st.plotly_chart`.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


PALETA = px.colors.qualitative.Set2


def grafica_produccion_anual(df_prod: pd.DataFrame) -> go.Figure:
    """Línea de producción por año."""
    if df_prod.empty:
        return _figura_vacia("Sin datos de producción anual")
    fig = px.line(
        df_prod,
        x="anio",
        y="n_trabajos",
        markers=True,
        title="Producción por año",
        labels={"anio": "Año", "n_trabajos": "Nº de trabajos"},
        color_discrete_sequence=[PALETA[0]],
    )
    fig.update_layout(
        xaxis=dict(tickmode="linear", dtick=1),
        hovermode="x unified",
    )
    return fig


def grafica_barras_horizontal(
    df: pd.DataFrame,
    columna: str,
    valor: str,
    titulo: str,
    color_idx: int = 1,
) -> go.Figure:
    """Barras horizontales genéricas (para top autores, instituciones, etc.)."""
    if df.empty:
        return _figura_vacia(f"Sin datos para {titulo}")
    fig = px.bar(
        df.sort_values(valor, ascending=True),
        x=valor,
        y=columna,
        orientation="h",
        title=titulo,
        labels={valor: "Nº de trabajos", columna: ""},
        color_discrete_sequence=[PALETA[color_idx % len(PALETA)]],
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return fig


def grafica_top_conceptos(df_conceptos: pd.DataFrame) -> go.Figure:
    """Barras horizontales de top conceptos."""
    return grafica_barras_horizontal(
        df_conceptos, columna="concepto", valor="n_trabajos",
        titulo="Top conceptos / palabras clave", color_idx=2,
    )


def grafica_ley_bradford(df_bradford: pd.DataFrame) -> go.Figure:
    """Barras agrupadas para la Ley de Bradford (zonas)."""
    if df_bradford.empty:
        return _figura_vacia("Sin datos para Ley de Bradford")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Nº fuentes", x=df_bradford["zona"], y=df_bradford["n_fuentes"],
        marker_color=PALETA[3],
    ))
    fig.add_trace(go.Bar(
        name="Nº trabajos", x=df_bradford["zona"], y=df_bradford["n_trabajos"],
        marker_color=PALETA[4],
    ))
    fig.update_layout(
        title="Ley de Bradford (dispersión por fuentes)",
        barmode="group",
        xaxis_title="Zona",
        yaxis_title="Cantidad",
    )
    return fig


def grafica_ley_lotka(df_lotka: pd.DataFrame) -> go.Figure:
    """Barras log-log para Ley de Lotka."""
    if df_lotka.empty:
        return _figura_vacia("Sin datos para Ley de Lotka")
    fig = px.bar(
        df_lotka,
        x="n_trabajos",
        y="n_autores",
        title="Ley de Lotka (productividad de autores)",
        labels={"n_trabajos": "Nº de trabajos por autor", "n_autores": "Nº de autores"},
        color_discrete_sequence=[PALETA[5]],
    )
    return fig


def grafica_distribucion_citas(df_citas: pd.DataFrame) -> go.Figure:
    """Histograma de citas."""
    if df_citas.empty:
        return _figura_vacia("Sin datos de citas")
    fig = px.histogram(
        df_citas,
        x="citas",
        nbins=30,
        title="Distribución de citas por trabajo",
        labels={"citas": "Nº de citas", "count": "Nº de trabajos"},
        color_discrete_sequence=[PALETA[6]],
    )
    return fig


def grafica_scatter_citas_anio(df_citas: pd.DataFrame) -> go.Figure:
    """Scatter citas vs año (para ver papers clásicos)."""
    if df_citas.empty:
        return _figura_vacia("Sin datos")
    fig = px.scatter(
        df_citas,
        x="anio",
        y="citas",
        hover_data=["titulo"],
        title="Citas vs. año de publicación",
        labels={"anio": "Año", "citas": "Nº de citas"},
        color_discrete_sequence=[PALETA[7]],
    )
    return fig


def _figura_vacia(mensaje: str) -> go.Figure:
    """Devuelve una figura vacía con un mensaje."""
    fig = go.Figure()
    fig.add_annotation(
        text=mensaje, xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
    )
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
    )
    return fig