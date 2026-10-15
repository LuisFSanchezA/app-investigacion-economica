import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_validation import validate_dataframe

# ---- Configuración de la página inicial ----

st.set_page_config(
    page_title= "Plataforma de Investigación Económica",
    page_icon= "📊",
    layout= "wide"
)

# ---- Encabezado ----

st.title("📊 Plataforma de Investigación Económica")
st.markdown(
    """
    Herramientas para organizar y explorar el proceso de investigación económica:
    desde la pregunta inicial hasta el análisis de datos y la construicción del
    diseño de investigación.
    """
)

st.divider()

# ---- Menú lateral ----

st.sidebar.title("Menú de opciones:")
seccion = st.sidebar.radio(
    "Selecciona una opción:",
    (
        "Pregunta general",
        "Análisis de Literatura",
        "Datos",
        "Tema",
    ),
)

# ---- Secciones ---- 

if seccion == "Pregunta general":
    st.header("❓ Pregunta de investigación")
    st.write(
        "Aquí definirás y refinarás tu pregunta general, la guía de tu investigación"
    )
    st.info("Esta sección sigue desarrollándose")

elif seccion == "Análisis de Literatura":
    st.header("📚 Análisis de Literatura")
    st.write(
        "Aquí analizarás y organizarás las fuentes académicas para tu investigación"
    )
    st.info("Esta sección sigue desarrollándose")

elif seccion == "Datos":
    st.header("📈 Datos")
    st.write(
        "Aquí cargarás, validarás y visualizarás los datos económicos de tu investigación."
    )

    ruta_csv = "data/raw/pib_empleo_demo.csv"
    columnas_requeridas = ["entidad", "anio", "pib_millones", "empleo_miles"]

    try:
        df = pd.read_csv(ruta_csv)
        validate_dataframe(df, columnas_requeridas)

        st.success("Datos cargados y validados correctamente.")

        # --- Métricas resumidas ---
        st.subheader("Resumen")
        col1, col2, col3 = st.columns(3)
        col1.metric("Filas", df.shape[0])
        col2.metric("Columnas", df.shape[1])
        col3.metric("Valores faltantes", int(df.isna().sum().sum()))

        # --- Filtro por rango de años ---
        st.subheader("Filtro")
        anio_min = int(df["anio"].min())
        anio_max = int(df["anio"].max())

        rango_anios = st.slider(
            "Selecciona el rango de años:",
            min_value=anio_min,
            max_value=anio_max,
            value=(anio_min, anio_max),
            step=1,
        )

        df_filtrado = df[
            (df["anio"] >= rango_anios[0]) & (df["anio"] <= rango_anios[1])
        ]

        st.caption(
            f"Mostrando {df_filtrado.shape[0]} de {df.shape[0]} observaciones."
        )

        # --- Gráfica del PIB ---
        st.subheader("Evolución del PIB por año")
        fig_pib = px.line(
            df_filtrado,
            x="anio",
            y="pib_millones",
            markers=True,
            title="PIB en millones (datos ficticios de prueba)",
            labels={
                "anio": "Año",
                "pib_millones": "PIB (millones)",
            },
        )
        fig_pib.update_layout(
            xaxis=dict(tickmode="linear", dtick=1),
            hovermode="x unified",
        )
        st.plotly_chart(fig_pib, use_container_width=True)

        # --- Gráfica del empleo ---
        st.subheader("Evolución del empleo por año")
        fig_empleo = px.line(
            df_filtrado,
            x="anio",
            y="empleo_miles",
            markers=True,
            title="Empleo en miles de personas (datos ficticios de prueba)",
            labels={
                "anio": "Año",
                "empleo_miles": "Empleo (miles)",
            },
        )
        fig_empleo.update_layout(
            xaxis=dict(tickmode="linear", dtick=1),
            hovermode="x unified",
        )
        st.plotly_chart(fig_empleo, use_container_width=True)

        # --- Documentación de variables ---
        with st.expander("📖 ¿Qué representa cada variable?"):
            st.markdown(
                """
                - **entidad**: nombre del país o entidad federativa (texto).
                - **anio**: año de la observación (entero).
                - **pib_millones**: Producto Interno Bruto en millones de unidades monetarias.
                - **empleo_miles**: población ocupada en miles de personas.

                **Nota:** los datos de este archivo son ficticios y solo se usan
                para probar el flujo de lectura, validación y visualización.
                """
            )

        # --- Tabla de datos ---
        st.subheader("Tabla de datos")
        st.dataframe(df_filtrado, use_container_width=True)

        # --- Estadísticas descriptivas ---
        st.subheader("Estadísticas descriptivas")
        st.dataframe(df_filtrado.describe(), use_container_width=True)

    except FileNotFoundError:
        st.error(f"No se encontró el archivo: {ruta_csv}")
    except ValueError as e:
        st.error(f"Error de validación: {e}")
    except Exception as e:
        st.error(f"Error inesperado: {e}")

elif seccion == "Tema":
    st.header("🎯 Tema")
    st.write(
        "Aquí integrarás los hallazgos para construir y delimitar tu tema"
    )
    st.info("Esta sección sigue desarrollándose")

# ----- Píe de Página -----

st.divider()
st.caption("Versión 0.1 - Semana 1 de desarrollo")
