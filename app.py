import streamlit as st

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
        "Aquí encontrarás o subirás los datos de tu investigación"
    )
    st.info("Esta sección sigue desarrollándose")

elif seccion == "Tema":
    st.header("🎯 Tema")
    st.write(
        "Aquí integrarás los hallazgos para construir y delimitar tu tema"
    )
    st.info("Esta sección sigue desarrollándose")

# ----- Píe de Página -----

st.divider()
st.caption("Versión 0.1 - Semana 1 de desarrollo")
