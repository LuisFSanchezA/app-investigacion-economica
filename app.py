import streamlit as st
import pandas as pd
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

        # Métricas resumidas
        st.subheader("Resumen")
        col1, col2, col3 = st.columns(3)
        col1.metric("Filas", df.shape[0])
        col2.metric("Columnas", df.shape[1])
        col3.metric("Valores faltantes", int(df.isna().sum().sum()))

        # Tabla de datos
        st.subheader("Tabla de datos")
        st.dataframe(df, use_container_width=True)

        # Estadísticas descriptivas
        st.subheader("Estadísticas descriptivas")
        st.dataframe(df.describe(), use_container_width=True)

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
