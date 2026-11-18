import streamlit as st
import pandas as pd
import plotly.express as px

from app.seccion_literatura import render as render_literatura
from src.data_validation import validate_dataframe
from src.fuentes import (
    BancoMundial,
    INDICADORES,
    PAISES,
    Banxico,
    SERIES,
    normalizar_serie,
    normalizar_serie_fechas,
    resumen_calidad,
)

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
    "Selecciona una sección:",
    (
        "Pregunta",
        "Literatura",
        "Fuentes de datos",
        "Datos",
        "Tema",
    ),
)

# ---- Secciones ---- 

if seccion == "Pregunta":
    st.header("❓ Pregunta de investigación")
    st.write(
        "Define tu tema, recibe sugerencias de preguntas y construye un borrador de protocolo."
    )

    # --- Paso 1: Tema ---
    st.subheader("1. Escribe tu tema de interés")
    tema = st.text_area(
        "Puede ser amplio al inicio:",
        placeholder="Ej: informalidad laboral en México",
        height=100,
        key="tema_input",
    )

    # --- Paso 2: Sugerir preguntas ---
    if st.button("Sugerir preguntas de investigación", key="btn_preguntas"):
        if not tema.strip():
            st.warning("Primero escribe un tema.")
        else:
            with st.spinner("Generando sugerencias (puede tomar 10-20 segundos)..."):
                try:
                    from src.ai import sugerir_preguntas
                    sugerencias = sugerir_preguntas(tema)
                    st.session_state["preguntas_sugeridas"] = sugerencias
                    st.session_state["error_ia"] = None
                except (ValueError, ConnectionError) as e:
                    st.session_state["error_ia"] = str(e)

    if st.session_state.get("error_ia"):
        st.error(f"Error: {st.session_state['error_ia']}")

    if st.session_state.get("preguntas_sugeridas"):
        st.markdown(st.session_state["preguntas_sugeridas"])

    # --- Paso 3: Elegir pregunta ---
    st.subheader("2. Elige y refina tu pregunta")
    pregunta_final = st.text_area(
        "Escribe la pregunta que vas a investigar:",
        height=100,
        key="pregunta_final",
    )

    # --- Paso 4: Sugerir objetivos ---
    if st.button("Sugerir objetivos", key="btn_objetivos"):
        if not pregunta_final.strip():
            st.warning("Primero escribe tu pregunta de investigación.")
        else:
            with st.spinner("Generando objetivos..."):
                try:
                    from src.ai import sugerir_objetivos
                    objetivos = sugerir_objetivos(pregunta_final)
                    st.session_state["objetivos_sugeridos"] = objetivos
                    st.session_state["error_ia"] = None
                except (ValueError, ConnectionError) as e:
                    st.session_state["error_ia"] = str(e)

    if st.session_state.get("objetivos_sugeridos"):
        st.markdown(st.session_state["objetivos_sugeridos"])

    # --- Paso 5: Generar protocolo ---
    st.subheader("3. Generar borrador de protocolo")
    st.caption(
        "⚠️ El protocolo es un **borrador** generado con IA. "
        "Debes revisarlo, corregirlo y verificar las fuentes antes de usarlo."
    )

    if st.button("Generar borrador de protocolo", key="btn_protocolo"):
        if not tema.strip() or not pregunta_final.strip():
            st.warning("Necesitas tema y pregunta para generar el protocolo.")
        else:
            with st.spinner("Generando protocolo (puede tomar 20-40 segundos)..."):
                try:
                    from src.ai import generar_protocolo
                    objetivos_actuales = st.session_state.get("objetivos_sugeridos", "")
                    protocolo = generar_protocolo(
                        tema=tema,
                        pregunta=pregunta_final,
                        objetivos=objetivos_actuales,
                    )
                    st.session_state["protocolo"] = protocolo
                    st.session_state["error_ia"] = None
                except (ValueError, ConnectionError) as e:
                    st.session_state["error_ia"] = str(e)

    if st.session_state.get("protocolo"):
        st.markdown(st.session_state["protocolo"])
        st.download_button(
            "Descargar protocolo (Markdown)",
            data=st.session_state["protocolo"],
            file_name="protocolo_borrador.md",
            mime="text/markdown",
            key="btn_descargar_protocolo",
        )

elif seccion == "Literatura":
    render_literatura()

elif seccion == "Fuentes de datos":
    st.header("🌐 Fuentes de datos")
    st.write(
        "Consulta series económicas de fuentes oficiales: Banco Mundial y Banco de México."
    )

    # --- Selector de fuente ---
    fuente = st.radio(
        "Selecciona la fuente:",
        options=["Banco Mundial", "Banxico"],
        horizontal=True,
        key="selector_fuente",  # ← nuevo
    )
    st.divider()

    # --- Controles según la fuente ---
    if fuente == "Banco Mundial":
        col1, col2 = st.columns(2)
        with col1:
            pais_codigo = st.selectbox(
                "País:",
                options=list(PAISES.keys()),
                format_func=lambda x: f"{PAISES[x]} ({x})",
                key="bm_pais",  # ← nuevo
            )
        with col2:
            indicador_codigo = st.selectbox(
                "Indicador:",
                options=list(INDICADORES.keys()),
                format_func=lambda x: INDICADORES[x]["nombre"],
                key="bm_indicador",  # ← nuevo
            )

        col3, col4 = st.columns(2)
        with col3:
            anio_inicio = st.number_input(
                "Año inicial:", min_value=1960, max_value=2024, value=2000,
                key="bm_anio_inicio",  # ← nuevo
            )
        with col4:
            anio_fin = st.number_input(
                "Año final:", min_value=1960, max_value=2024, value=2024,
                key="bm_anio_fin",  # ← nuevo
            )

    else:  # Banxico
        indicador_codigo = st.selectbox(
            "Serie:",
            options=list(SERIES.keys()),
            format_func=lambda x: f"{SERIES[x]['nombre']} ({x})",
            key="bx_serie",  # ← nuevo
        )

        col3, col4 = st.columns(2)
        with col3:
            anio_inicio = st.number_input(
                "Año inicial:", min_value=2000, max_value=2024, value=2024,
                key="bx_anio_inicio",  # ← nuevo
            )
        with col4:
            anio_fin = st.number_input(
                "Año final:", min_value=2000, max_value=2024, value=2024,
                key="bx_anio_fin",  # ← nuevo
            )

        pais_codigo = "MEX"

    # --- Botón de consulta ---
    if st.button("Consultar", key="btn_consultar_datos"):
        with st.spinner(f"Consultando {fuente}..."):
            try:
                if fuente == "Banco Mundial":
                    conector = BancoMundial()
                else:
                    conector = Banxico()

                df, meta = conector.consultar(
                    indicador=indicador_codigo,
                    pais=pais_codigo,
                    periodo_inicio=anio_inicio,
                    periodo_fin=anio_fin,
                )

                # Normalizar según la fuente
                if "fecha" in df.columns:
                    df_norm = normalizar_serie_fechas(df)
                else:
                    df_norm = normalizar_serie(df)

                resumen = resumen_calidad(df_norm, meta)

                st.session_state["df_fuente"] = df_norm
                st.session_state["meta_fuente"] = meta
                st.session_state["resumen_fuente"] = resumen
                st.session_state["error_fuente"] = None

            except (ValueError, ConnectionError) as e:
                st.session_state["df_fuente"] = None
                st.session_state["error_fuente"] = str(e)

    # --- Mostrar resultados ---
    if st.session_state.get("error_fuente"):
        st.error(f"Error en la consulta: {st.session_state['error_fuente']}")

    elif st.session_state.get("df_fuente") is not None:
        df_norm = st.session_state["df_fuente"]
        meta = st.session_state["meta_fuente"]
        resumen = st.session_state["resumen_fuente"]

        st.success(f"Consulta exitosa: {len(df_norm)} observaciones.")

        # --- Metadatos ---
        st.subheader("Metadatos de la fuente")
        st.json(meta.como_dict())

        # --- Resumen de calidad ---
        st.subheader("Resumen de calidad")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Observaciones", resumen["observaciones"])
        col_b.metric("Duplicados", resumen["duplicados"])
        col_c.metric("Faltantes (total)", sum(resumen["faltantes"].values()))

        # --- Contexto de la serie ---
        st.subheader("Contexto de la serie")
        st.markdown(
            f"""
            - **Periodo:** {resumen['anio_min']} – {resumen['anio_max']}
            - **Unidad:** {resumen['unidad']}
            - **Indicador:** {resumen['indicador']}
            """
        )

        # --- Gráfica temporal ---
        st.subheader("Serie temporal")
        fig = px.line(
            df_norm,
            x="anio",
            y="valor",
            markers=True,
            title=f"{resumen['indicador']} — {resumen['fuente']}",
            labels={
                "anio": "Año",
                "valor": f"Valor ({resumen['unidad']})",
            },
        )
        fig.update_layout(
            xaxis=dict(tickmode="linear", dtick=1),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True, key="grafica_fuente")

        # --- Tabla ---
        st.subheader("Datos")
        st.dataframe(df_norm, use_container_width=True)

        # --- Descarga CSV ---
        st.subheader("Descargar")
        csv_bytes = df_norm.to_csv(index=False).encode("utf-8")
        nombre_archivo = (
            f"{meta.codigo_indicador}_{meta.pais}_"
            f"{meta.periodo_inicio}_{meta.periodo_fin}.csv"
        )
        st.download_button(
            label="Descargar CSV",
            data=csv_bytes,
            file_name=nombre_archivo,
            mime="text/csv",
            key="btn_descargar_datos",
        )
    # --- Controles de consulta ---
    col1, col2 = st.columns(2)

    with col1:
        pais_codigo = st.selectbox(
            "País:",
            options=list(PAISES.keys()),
            format_func=lambda x: f"{PAISES[x]} ({x})",
        )

    with col2:
        indicador_codigo = st.selectbox(
            "Indicador:",
            options=list(INDICADORES.keys()),
            format_func=lambda x: INDICADORES[x]["nombre"],
        )

    col3, col4 = st.columns(2)
    with col3:
        anio_inicio = st.number_input(
            "Año inicial:", min_value=1960, max_value=2024, value=2000
        )
    with col4:
        anio_fin = st.number_input(
            "Año final:", min_value=1960, max_value=2024, value=2024
        )

    if st.button("Consultar", key="btn_consultar_fuente"):
        with st.spinner("Consultando al Banco Mundial..."):
            try:
                bm = BancoMundial()
                df, meta = bm.consultar(
                    indicador=indicador_codigo,
                    pais=pais_codigo,
                    periodo_inicio=anio_inicio,
                    periodo_fin=anio_fin,
                )

                df_norm = normalizar_serie(df)
                resumen = resumen_calidad(df_norm, meta)

                st.session_state["df_fuente"] = df_norm
                st.session_state["meta_fuente"] = meta
                st.session_state["resumen_fuente"] = resumen
                st.session_state["error_fuente"] = None

            except (ValueError, ConnectionError) as e:
                st.session_state["df_fuente"] = None
                st.session_state["error_fuente"] = str(e)

    # --- Mostrar resultados ---
    if st.session_state.get("error_fuente"):
        st.error(f"Error en la consulta: {st.session_state['error_fuente']}")

    elif st.session_state.get("df_fuente") is not None:
        df_norm = st.session_state["df_fuente"]
        meta = st.session_state["meta_fuente"]
        resumen = st.session_state["resumen_fuente"]

        st.success(f"Consulta exitosa: {len(df_norm)} observaciones.")

        # --- Metadatos ---
        st.subheader("Metadatos de la fuente")
        st.json(meta.como_dict())

        # --- Resumen de calidad ---
        st.subheader("Resumen de calidad")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Observaciones", resumen["observaciones"])
        col_b.metric("Duplicados", resumen["duplicados"])
        col_c.metric("Faltantes (total)", sum(resumen["faltantes"].values()))

        # --- Contexto de la serie ---
        st.subheader("Contexto de la serie")
        st.markdown(
            f"""
            - **Periodo:** {resumen['anio_min']} – {resumen['anio_max']}
            - **Unidad:** {resumen['unidad']}
            - **Indicador:** {resumen['indicador']}
            """
        )

        # --- Gráfica temporal ---
        st.subheader("Serie temporal")
        fig = px.line(
            df_norm,
            x="anio",
            y="valor",
            markers=True,
            title=f"{resumen['indicador']} — {resumen['fuente']}",
            labels={
                "anio": "Año",
                "valor": f"Valor ({resumen['unidad']})",
            },
        )
        fig.update_layout(
            xaxis=dict(tickmode="linear", dtick=1),
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True, key="grafica_fuente_2")

        # --- Tabla ---
        st.subheader("Datos")
        st.dataframe(df_norm, use_container_width=True)

        # --- Descarga CSV ---
        st.subheader("Descargar")
        csv_bytes = df_norm.to_csv(index=False).encode("utf-8")
        nombre_archivo = (
            f"{meta.codigo_indicador}_{meta.pais}_"
            f"{meta.periodo_inicio}_{meta.periodo_fin}.csv"
        )
        st.download_button(
            label="Descargar CSV",
            data=csv_bytes,
            file_name=nombre_archivo,
            mime="text/csv",
            key="btn_descargar_fuente",
        )

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
        st.plotly_chart(fig_pib, use_container_width=True, key="grafica_pib")

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
        st.plotly_chart(fig_empleo, use_container_width=True, key="grafica_empleo")

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
