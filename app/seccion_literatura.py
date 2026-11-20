"""Sección Literatura: búsqueda bibliográfica, queries y corpus.

Pestañas:
- Buscar: keywords IA + OpenAlex + añadir al corpus
- Queries: generador para WoS/Scopus/OpenAlex/Scholar
- Corpus: tabla del corpus acumulado + exportar CSV
"""

import json

import pandas as pd
import streamlit as st
import plotly.express as px

from src.bibliometria import graficas, graficas_redes, metricas, redes
from src.bibliometria import metricas, graficas
from src.fuentes.tesis import Tesis
from src.ai import (
    clasificar_papers,
    detectar_vacios,
    sintetizar_corpus,
    sugerir_keywords_cached,
)

from src.bibliometria import (
    construir_query_google_scholar,
    construir_query_openalex,
    construir_query_scopus,
    construir_query_wos,
)
from src.fuentes import OpenAlex

# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def _init_session_state():
    """Inicializa las claves necesarias en session_state."""
    if "lit_corpus" not in st.session_state:
        st.session_state["lit_corpus"] = []
    if "lit_keywords_ia" not in st.session_state:
        st.session_state["lit_keywords_ia"] = ""
    if "lit_resultados" not in st.session_state:
        st.session_state["lit_resultados"] = None
    if "lit_error" not in st.session_state:
        st.session_state["lit_error"] = None


def _corpus_como_df() -> pd.DataFrame:
    """Devuelve el corpus como DataFrame."""
    corpus = st.session_state.get("lit_corpus", [])
    if not corpus:
        return pd.DataFrame()
    return pd.DataFrame(corpus)


def _añadir_al_corpus(df_nuevos: pd.DataFrame) -> int:
    """Añade trabajos al corpus deduplicando por DOI o título.

    Devuelve el número de trabajos realmente añadidos.
    """
    corpus_actual = st.session_state.get("lit_corpus", [])
    claves_existentes = set()
    for item in corpus_actual:
        doi = (item.get("doi") or "").strip().lower()
        titulo = (item.get("titulo") or "").strip().lower()
        claves_existentes.add(doi if doi else titulo)

    añadidos = 0
    for _, row in df_nuevos.iterrows():
        doi = (row.get("doi") or "").strip().lower()
        titulo = (row.get("titulo") or "").strip().lower()
        clave = doi if doi else titulo
        if clave in claves_existentes:
            continue
        # Convertir referencias (lista) a algo serializable
        item = row.to_dict()
        if isinstance(item.get("referencias"), list):
            item["referencias"] = item["referencias"]
        corpus_actual.append(item)
        claves_existentes.add(clave)
        añadidos += 1

    st.session_state["lit_corpus"] = corpus_actual
    return añadidos


# ---------------------------------------------------------------------------
# Pestaña: Buscar
# ---------------------------------------------------------------------------

def _render_buscar():
    st.subheader("🔎 Buscar literatura en OpenAlex")

    # --- Contexto: pregunta activa ---
    pregunta_activa = st.session_state.get("pregunta_final", "")
    if pregunta_activa:
        st.info(f"📌 Pregunta activa: *{pregunta_activa}*")
    else:
        st.caption(
            "💡 Tip: define tu pregunta en la sección **Pregunta** para "
            "que la IA use ese contexto."
        )

    # --- Tema ---
    tema = st.text_area(
        "Tema de búsqueda:",
        value=st.session_state.get("lit_tema", ""),
        placeholder="Ej: informalidad laboral en México",
        height=80,
        key="lit_tema",
    )

    # --- Botón IA ---
    col_ia, col_limpiar = st.columns([1, 3])
    with col_ia:
        if st.button("🤖 Sugerir keywords con IA", key="lit_btn_ia"):
            if not tema.strip():
                st.warning("Primero escribe un tema.")
            else:
                with st.spinner("Generando keywords... puede tomar 30-60s en hora pico."):
                    try:
                        resultado = sugerir_keywords_cached(
                            tema=tema.strip(),
                            pregunta=pregunta_activa,
                        )
                        st.session_state["lit_keywords_ia"] = resultado
                        st.session_state["lit_error"] = None
                    except (ValueError, ConnectionError) as e:
                        st.session_state["lit_error"] = str(e)
    with col_limpiar:
        if st.button("🗑️ Limpiar keywords IA", key="lit_btn_limpiar_ia"):
            st.session_state["lit_keywords_ia"] = ""

    if st.session_state.get("lit_error"):
        st.error(f"⚠️ {st.session_state['lit_error']}")
        st.info(
            "💡 Si la IA falla, puedes escribir las keywords manualmente abajo."
        )

    # --- Mostrar keywords IA ---
    if st.session_state.get("lit_keywords_ia"):
        with st.expander("🤖 Sugerencias de IA (borrador — verificar)", expanded=True):
            st.markdown(st.session_state["lit_keywords_ia"])

    # --- Keywords manuales ---
    st.markdown("**Keywords para la búsqueda** (una por línea):")
    keywords_texto = st.text_area(
        "Keywords:",
        value=st.session_state.get("lit_keywords_texto", "informalidad laboral"),
        height=100,
        key="lit_keywords_texto",
        label_visibility="collapsed",
    )

    # --- Filtros ---
    st.markdown("**Filtros:**")
    col1, col2 = st.columns(2)
    with col1:
        desde = st.number_input(
            "Año desde:", min_value=1900, max_value=2026, value=2015,
            key="lit_desde",
        )
    with col2:
        hasta = st.number_input(
            "Año hasta:", min_value=1900, max_value=2026, value=2026,
            key="lit_hasta",
        )

    col3, col4, col5 = st.columns(3)
    with col3:
        tipos = st.multiselect(
            "Tipos:",
            options=["article", "review", "book", "book-chapter", "dissertation", "report"],
            default=["article", "review"],
            key="lit_tipos",
        )
    with col4:
        idiomas = st.multiselect(
            "Idiomas:",
            options=["es", "en", "pt"],
            default=["es", "en"],
            key="lit_idiomas",
        )
    with col5:
        solo_oa = st.checkbox("Solo acceso abierto", value=False, key="lit_oa")

    # --- Botón buscar ---
    if st.button("🔍 Buscar en OpenAlex", key="lit_btn_buscar", type="primary"):
        kws = [k.strip() for k in keywords_texto.splitlines() if k.strip()]
        if not kws:
            st.warning("Escribe al menos una keyword.")
        elif desde > hasta:
            st.warning("El año inicial no puede ser mayor que el final.")
        else:
            with st.spinner(f"Consultando OpenAlex ({len(kws)} keywords)..."):
                try:
                    conector = OpenAlex()
                    df, meta = conector.buscar(
                        keywords=kws,
                        desde=int(desde),
                        hasta=int(hasta),
                        tipos=tipos or None,
                        idiomas=idiomas or None,
                        open_access=True if solo_oa else None,
                        limite=200,
                    )
                    st.session_state["lit_resultados"] = df
                    st.session_state["lit_meta"] = meta
                    st.session_state["lit_error"] = None
                except (ValueError, ConnectionError) as e:
                    st.session_state["lit_resultados"] = None
                    st.session_state["lit_error"] = str(e)

    if st.session_state.get("lit_error"):
        st.error(f"⚠️ {st.session_state['lit_error']}")

    # --- Mostrar resultados ---
    df = st.session_state.get("lit_resultados")
    if df is not None and not df.empty:
        meta = st.session_state.get("lit_meta")
        st.success(f"✅ {len(df)} trabajos encontrados.")
        if meta:
            with st.expander("🔗 URL de la consulta"):
                st.code(meta.url_fuente, language="text")

        # Tabla con selección
        columnas_mostrar = ["titulo", "anio", "autores", "fuente", "citas", "doi", "tipo", "idioma"]
        columnas_disponibles = [c for c in columnas_mostrar if c in df.columns]
        df_mostrar = df[columnas_disponibles].copy()
        df_mostrar.insert(0, "seleccionar", False)

        edited = st.data_editor(
            df_mostrar,
            hide_index=True,
            use_container_width=True,
            key="lit_tabla_resultados",
            column_config={
                "seleccionar": st.column_config.CheckboxColumn("✓"),
                "titulo": st.column_config.TextColumn("Título", width="large"),
                "anio": st.column_config.NumberColumn("Año", width="small"),
                "autores": st.column_config.TextColumn("Autores", width="medium"),
                "fuente": st.column_config.TextColumn("Fuente", width="medium"),
                "citas": st.column_config.NumberColumn("Citas", width="small"),
                "doi": st.column_config.TextColumn("DOI", width="medium"),
                "tipo": st.column_config.TextColumn("Tipo", width="small"),
                "idioma": st.column_config.TextColumn("Idioma", width="small"),
            },
        )

        seleccionados = edited[edited["seleccionar"] == True]
        n_sel = len(seleccionados)

        if n_sel > 0:
            if st.button(f"➕ Añadir {n_sel} al corpus", key="lit_btn_añadir", type="primary"):
                indices = seleccionados.index
                df_sel = df.loc[indices].reset_index(drop=True)
                añadidos = _añadir_al_corpus(df_sel)
                st.success(f"✅ {añadidos} trabajos añadidos al corpus.")
                st.rerun()

    # --- Corpus actual ---
    corpus_df = _corpus_como_df()
    st.divider()
    st.caption(f"📚 Corpus actual: **{len(corpus_df)}** trabajos.")


# ---------------------------------------------------------------------------
# Pestaña: Queries
# ---------------------------------------------------------------------------

def _render_queries():
    st.subheader("🔧 Generador de queries")
    st.markdown(
        "Genera la sintaxis exacta para pegar en cada base. "
        "**WoS y Scopus no se consultan por API** (son de pago), "
        "pero puedes pegar estas queries en su interfaz web."
    )

    tema = st.text_input(
        "Tema o keywords (separadas por coma):",
        value=st.session_state.get("lit_query_tema", "informalidad laboral, informal employment"),
        key="lit_query_tema",
    )

    col1, col2 = st.columns(2)
    with col1:
        desde = st.number_input("Desde:", min_value=1900, max_value=2026, value=2015, key="lit_q_desde")
    with col2:
        hasta = st.number_input("Hasta:", min_value=1900, max_value=2026, value=2026, key="lit_q_hasta")

    if st.button("Generar queries", key="lit_btn_queries"):
        kws = [k.strip() for k in tema.split(",") if k.strip()]
        if not kws:
            st.warning("Escribe al menos una keyword.")
        else:
            try:
                q_wos = construir_query_wos(
                    kws, desde=int(desde), hasta=int(hasta),
                    tipos=["Article", "Review"], idiomas=["Spanish", "English"],
                )
                q_scopus = construir_query_scopus(
                    kws, desde=int(desde), hasta=int(hasta),
                    tipos=["ar", "re"], idiomas=["spa", "eng"],
                )
                q_openalex = construir_query_openalex(
                    kws, desde=int(desde), hasta=int(hasta),
                    tipos=["article", "review"], idiomas=["es", "en"],
                )
                q_scholar = construir_query_google_scholar(
                    kws, desde=int(desde), hasta=int(hasta),
                )

                st.markdown("### 📚 Web of Science")
                st.code(q_wos, language="text")

                st.markdown("### 📚 Scopus")
                st.code(q_scopus, language="text")

                st.markdown("### 📚 OpenAlex (parámetro filter)")
                st.code(q_openalex, language="text")

                st.markdown("### 📚 Google Scholar")
                st.code(q_scholar, language="text")

            except ValueError as e:
                st.error(f"Error: {e}")


# ---------------------------------------------------------------------------
# Pestaña: Corpus
# ---------------------------------------------------------------------------

def _render_corpus():
    st.subheader("📚 Corpus acumulado")
    df = _corpus_como_df()

    if df.empty:
        st.info(
            "Aún no hay trabajos en el corpus. Ve a la pestaña **Buscar**, "
            "selecciona trabajos y pulsa **Añadir al corpus**."
        )
        return

    st.success(f"✅ {len(df)} trabajos en el corpus.")

    columnas_mostrar = ["titulo", "anio", "autores", "fuente", "citas", "doi", "tipo"]
    columnas_disponibles = [c for c in columnas_mostrar if c in df.columns]
    st.dataframe(df[columnas_disponibles], use_container_width=True, hide_index=True)

    # Exportar CSV
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Exportar corpus (CSV)",
        data=csv_bytes,
        file_name="corpus_literatura.csv",
        mime="text/csv",
        key="lit_btn_export_corpus",
    )

    # Vaciar corpus
    if st.button("🗑️ Vaciar corpus", key="lit_btn_vaciar"):
        st.session_state["lit_corpus"] = []
        st.rerun()

def _render_bibliometria():
    st.subheader("📊 Bibliometría del corpus")
    df = _corpus_como_df()

    if df.empty:
        st.info(
            "Aún no hay trabajos en el corpus. Ve a la pestaña **Buscar** "
            "y añade algunos para ver las métricas."
        )
        return

    if len(df) < 3:
        st.warning(
            f"El corpus tiene solo {len(df)} trabajos. "
            "Añade al menos 5-10 para que las métricas sean interpretables."
        )

    try:
        resumen = metricas.resumen_general(df)
    except ValueError as e:
        st.error(f"Error al calcular métricas: {e}")
        return

    # --- Métricas generales ---
    st.markdown("### Resumen general")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Trabajos", resumen["n_trabajos"])
    c2.metric("Citas totales", resumen["citas_total"])
    c3.metric("h-index", resumen["h_index"])
    c4.metric("% Open Access", f"{resumen['pct_open_access']}%")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Año mín.", resumen["anio_min"] or "—")
    c6.metric("Año máx.", resumen["anio_max"] or "—")
    c7.metric("Autores únicos", resumen["n_autores_unicos"])
    c8.metric("Fuentes únicas", resumen["n_fuentes_unicas"])

    # --- Producción por año ---
    st.markdown("### Producción por año")
    df_prod = metricas.produccion_por_anio(df)
    st.plotly_chart(
        graficas.grafica_produccion_anual(df_prod),
        use_container_width=True,
        key="lit_graf_produccion",
    )

    # --- Top autores / instituciones / países / fuentes ---
    st.markdown("### Top 10")
    col_a, col_b = st.columns(2)
    with col_a:
        df_aut = metricas.top_autores(df, n=10)
        st.plotly_chart(
            graficas.grafica_barras_horizontal(
                df_aut, "autor", "n_trabajos", "Top 10 autores", color_idx=1
            ),
            use_container_width=True, key="lit_graf_autores",
        )
    with col_b:
        df_inst = metricas.top_instituciones(df, n=10)
        st.plotly_chart(
            graficas.grafica_barras_horizontal(
                df_inst, "institucion", "n_trabajos", "Top 10 instituciones", color_idx=2
            ),
            use_container_width=True, key="lit_graf_instituciones",
        )

    col_c, col_d = st.columns(2)
    with col_c:
        df_pais = metricas.top_paises(df, n=10)
        st.plotly_chart(
            graficas.grafica_barras_horizontal(
                df_pais, "pais", "n_trabajos", "Top 10 países", color_idx=3
            ),
            use_container_width=True, key="lit_graf_paises",
        )
    with col_d:
        df_fuente = metricas.top_fuentes(df, n=10)
        st.plotly_chart(
            graficas.grafica_barras_horizontal(
                df_fuente, "fuente", "n_trabajos", "Top 10 fuentes", color_idx=4
            ),
            use_container_width=True, key="lit_graf_fuentes",
        )

    # --- Top conceptos ---
    st.markdown("### Conceptos / palabras clave")
    df_conc = metricas.top_conceptos(df, n=20)
    st.plotly_chart(
        graficas.grafica_top_conceptos(df_conc),
        use_container_width=True,
        key="lit_graf_conceptos",
    )

    # --- Ley de Bradford ---
    st.markdown("### Ley de Bradford")
    st.caption(
        "Distribución de la literatura por fuentes: la zona núcleo concentra "
        "pocas fuentes con muchos trabajos; la periferia, muchas fuentes con pocos."
    )
    df_brad = metricas.ley_bradford(df)
    st.plotly_chart(
        graficas.grafica_ley_bradford(df_brad),
        use_container_width=True,
        key="lit_graf_bradford",
    )

    # --- Ley de Lotka ---
    st.markdown("### Ley de Lotka")
    st.caption(
        "Productividad de autores: la mayoría publica poco; unos pocos "
        "publican mucho."
    )
    df_lotka = metricas.ley_lotka(df)
    st.plotly_chart(
        graficas.grafica_ley_lotka(df_lotka),
        use_container_width=True,
        key="lit_graf_lotka",
    )

    # --- Citas ---
    st.markdown("### Citas")
    col_e, col_f = st.columns(2)
    with col_e:
        df_citas = metricas.distribucion_citas(df)
        st.plotly_chart(
            graficas.grafica_distribucion_citas(df_citas),
            use_container_width=True, key="lit_graf_citas_hist",
        )
    with col_f:
        st.plotly_chart(
            graficas.grafica_scatter_citas_anio(df_citas),
            use_container_width=True, key="lit_graf_citas_scatter",
        )

    # --- Exportar ---
    st.markdown("### Exportar")
    st.download_button(
        "⬇️ Exportar métricas (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="corpus_metricas.csv",
        mime="text/csv",
        key="lit_btn_export_metricas",
    )


def _render_redes():
    st.subheader("🕸️ Redes bibliométricas")
    df = _corpus_como_df()

    if df.empty:
        st.info(
            "Aún no hay trabajos en el corpus. Ve a la pestaña **Buscar** "
            "y añade algunos para construir redes."
        )
        return

    if len(df) < 3:
        st.warning(
            f"El corpus tiene solo {len(df)} trabajos. "
            "Añade al menos 5-10 para que las redes sean interpretables."
        )

    # --- Selector de tipo de red ---
    tipo = st.radio(
        "Tipo de red:",
        options=["Co-autoría", "Co-palabras clave"],
        horizontal=True,
        key="lit_tipo_red",
    )

    min_peso = st.slider(
        "Peso mínimo de arista (nº de co-ocurrencias):",
        min_value=1, max_value=5, value=1, step=1,
        key="lit_min_peso_red",
    )

    max_nodos = st.slider(
        "Máximo de nodos a mostrar:",
        min_value=10, max_value=100, value=50, step=10,
        key="lit_max_nodos_red",
    )

    try:
        if tipo == "Co-autoría":
            grafo = redes.red_coautoria(df, min_peso=min_peso)
            titulo = "Red de co-autoría"
        else:
            grafo = redes.red_copalabras(df, min_peso=min_peso)
            titulo = "Red de co-palabras clave"
    except ValueError as e:
        st.error(f"Error al construir la red: {e}")
        return

    # --- Métricas de red ---
    m = redes.metricas_red(grafo)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Nodos", m["n_nodos"])
    c2.metric("Aristas", m["n_aristas"])
    c3.metric("Densidad", m["densidad"])
    c4.metric("Componentes", m["n_componentes"])
    c5.metric("Grado medio", m["grado_medio"])

    # --- Gráfica ---
    fig = graficas_redes.grafica_red(grafo, titulo=titulo, max_nodos=max_nodos)
    st.plotly_chart(fig, use_container_width=True, key="lit_graf_red")

    # --- Top nodos ---
    st.markdown("### Nodos más conectados")
    df_top = redes.nodos_centrales(grafo, n=10)
    st.dataframe(df_top, use_container_width=True, hide_index=True)

    # --- Exportar aristas ---
    st.markdown("### Exportar red")
    if grafo.number_of_edges() > 0:
        aristas = [
            {"origen": u, "destino": v, "peso": d["weight"]}
            for u, v, d in grafo.edges(data=True)
        ]
        df_aristas = pd.DataFrame(aristas)
        st.download_button(
            "⬇️ Exportar aristas (CSV)",
            data=df_aristas.to_csv(index=False).encode("utf-8"),
            file_name=f"red_{tipo.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            key="lit_btn_export_red",
        )
    else:
        st.caption("La red no tiene aristas con el peso mínimo seleccionado.")


def _render_evaluar():
    st.subheader("🤖 Evaluación del corpus con IA")
    st.caption(
        "⚠️ Todos los análisis son **borradores generados con IA**. "
        "Debes revisarlos, corregirlos y verificar las fuentes."
    )

    df = _corpus_como_df()
    if df.empty:
        st.info(
            "Aún no hay trabajos en el corpus. Ve a la pestaña **Buscar** "
            "y añade algunos para evaluarlos con IA."
        )
        return

    pregunta = st.session_state.get("pregunta_final", "")
    if not pregunta:
        st.warning(
            "No hay pregunta de investigación activa. Ve a la sección "
            "**Pregunta** y define una para que la IA tenga contexto."
        )
        pregunta = st.text_input(
            "O escribe la pregunta aquí:",
            key="lit_eval_pregunta_manual",
        )
        if not pregunta:
            return

    st.info(f"📌 Pregunta: *{pregunta}*")
    st.caption(f"📚 Corpus: {len(df)} trabajos.")

    analisis = st.radio(
        "Tipo de análisis:",
        options=[
            "Síntesis del estado del arte",
            "Detección de vacíos",
            "Clasificación de papers",
        ],
        horizontal=True,
        key="lit_eval_tipo",
    )

    if st.button("🤖 Ejecutar análisis", key="lit_btn_ejecutar_ia", type="primary"):
        with st.spinner("Analizando corpus... puede tomar 30-60s en hora pico."):
            try:
                if analisis == "Síntesis del estado del arte":
                    resultado = sintetizar_corpus(pregunta, df)
                elif analisis == "Detección de vacíos":
                    resultado = detectar_vacios(pregunta, df)
                else:
                    resultado = clasificar_papers(pregunta, df)
                st.session_state["lit_eval_resultado"] = resultado
                st.session_state["lit_eval_error"] = None
            except (ValueError, ConnectionError) as e:
                st.session_state["lit_eval_error"] = str(e)

    if st.session_state.get("lit_eval_error"):
        st.error(f"⚠️ {st.session_state['lit_eval_error']}")

    if st.session_state.get("lit_eval_resultado"):
        st.markdown("---")
        st.markdown(st.session_state["lit_eval_resultado"])
        st.download_button(
            "⬇️ Descargar análisis (Markdown)",
            data=st.session_state["lit_eval_resultado"],
            file_name=f"evaluacion_{analisis.lower().replace(' ', '_')}.md",
            mime="text/markdown",
            key="lit_btn_export_eval",
        )

def _render_tesis():
    st.subheader("🎓 Tesis académicas")
    st.markdown(
        "Busca tesis en OpenAlex y accede a repositorios especializados "
        "(TesiuNAM, Dialnet, RIUD) con la query ya armada."
    )
    st.caption(
        "💡 Inspirado en [NodOS](https://nodosmap.com), pero adaptado a "
        "búsqueda + enlaces. El mapa semántico vendrá después."
    )

    # --- Keywords ---
    pregunta = st.session_state.get("pregunta_final", "")
    keywords_default = ""
    if pregunta:
        keywords_default = pregunta[:100]

    keywords_texto = st.text_area(
        "Keywords para buscar tesis (una por línea):",
        value=st.session_state.get("lit_tesis_keywords", keywords_default),
        height=80,
        key="lit_tesis_keywords",
    )

    # --- Filtros ---
    col1, col2 = st.columns(2)
    with col1:
        desde = st.number_input(
            "Año desde:", min_value=1900, max_value=2026, value=2010,
            key="lit_tesis_desde",
        )
    with col2:
        hasta = st.number_input(
            "Año hasta:", min_value=1900, max_value=2026, value=2026,
            key="lit_tesis_hasta",
        )

    # --- Enlaces prefabricados ---
    st.markdown("### 🔗 Buscar en repositorios especializados")
    st.caption(
        "Haz clic en cada repositorio para buscar manualmente. "
        "La query ya está armada."
    )
    kws = [k.strip() for k in keywords_texto.splitlines() if k.strip()]
    if kws:
        enlaces = Tesis.enlaces_prefabricados(kws)
        descripciones = Tesis.descripcion_repositorios()
        cols = st.columns(3)
        for i, (nombre, url) in enumerate(enlaces.items()):
            with cols[i]:
                st.markdown(f"**{nombre}**")
                st.caption(descripciones.get(nombre, ""))
                st.link_button(f"Abrir {nombre}", url, key=f"lit_tesis_link_{nombre}")
    else:
        st.caption("Escribe al menos una keyword para generar los enlaces.")

    # --- Botón buscar en OpenAlex ---
    if st.button("🔍 Buscar tesis en OpenAlex", key="lit_btn_buscar_tesis", type="primary"):
        if not kws:
            st.warning("Escribe al menos una keyword.")
        elif desde > hasta:
            st.warning("El año inicial no puede ser mayor que el final.")
        else:
            with st.spinner(f"Buscando tesis ({len(kws)} keywords)..."):
                try:
                    conector = Tesis()
                    df, meta = conector.buscar(
                        keywords=kws,
                        desde=int(desde),
                        hasta=int(hasta),
                        limite=100,
                    )
                    st.session_state["lit_tesis_resultados"] = df
                    st.session_state["lit_tesis_meta"] = meta
                    st.session_state["lit_tesis_error"] = None
                except (ValueError, ConnectionError) as e:
                    st.session_state["lit_tesis_resultados"] = None
                    st.session_state["lit_tesis_error"] = str(e)

    if st.session_state.get("lit_tesis_error"):
        st.error(f"⚠️ {st.session_state['lit_tesis_error']}")

    # --- Resultados ---
    df = st.session_state.get("lit_tesis_resultados")
    if df is not None and not df.empty:
        st.success(f"✅ {len(df)} tesis encontradas en OpenAlex.")

        # Métricas
        st.markdown("### Resumen")
        c1, c2, c3 = st.columns(3)
        c1.metric("Tesis", len(df))
        anios = pd.to_numeric(df["anio"], errors="coerce").dropna()
        c2.metric("Año mín.", int(anios.min()) if not anios.empty else "—")
        c3.metric("Año máx.", int(anios.max()) if not anios.empty else "—")

        # Tesis por año
        if not anios.empty:
            st.markdown("### Tesis por año")
            df_anio = (
                df.assign(anio=anios.astype(int))
                .groupby("anio")
                .size()
                .reset_index(name="n_tesis")
            )
            fig = px.bar(
                df_anio, x="anio", y="n_tesis",
                title="Tesis por año",
                labels={"anio": "Año", "n_tesis": "Nº de tesis"},
            )
            st.plotly_chart(fig, use_container_width=True, key="lit_graf_tesis_anio")

        # Tabla con enlaces
        st.markdown("### Tesis encontradas")
        columnas = ["titulo", "autores", "anio", "instituciones", "enlace_tesunam", "enlace_dialnet"]
        columnas = [c for c in columnas if c in df.columns]
        st.dataframe(
            df[columnas],
            use_container_width=True,
            hide_index=True,
            column_config={
                "titulo": st.column_config.TextColumn("Título", width="large"),
                "autores": st.column_config.TextColumn("Autores", width="medium"),
                "anio": st.column_config.NumberColumn("Año", width="small"),
                "instituciones": st.column_config.TextColumn("Institución", width="medium"),
                "enlace_tesunam": st.column_config.LinkColumn("TesiuNAM", display_text="Abrir"),
                "enlace_dialnet": st.column_config.LinkColumn("Dialnet", display_text="Abrir"),
            },
        )

        # Exportar
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Exportar tesis (CSV)",
            data=csv_bytes,
            file_name="tesis_openalex.csv",
            mime="text/csv",
            key="lit_btn_export_tesis",
        )

    # --- Nota pedagógica ---
    with st.expander("📖 ¿Por qué buscar tesis?"):
        st.markdown(
            """
            Las tesis son **literatura gris**: no pasan por revisión por pares
            como los artículos, pero son valiosas porque:

            - **Muestran el estado del arte local**: qué se está investigando
            en tu universidad o país.
            - **Aportan metodologías aplicadas**: cómo otros resolvieron
            problemas similares.
            - **Revelan vacíos**: temas que nadie ha tocado aún.

            **Advertencia:** una tesis no es una fuente revisada por pares.
            Úsala como contexto, no como evidencia definitiva.
            """
        )


# ---------------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------------

def render():
    """Renderiza la sección Literatura completa."""
    _init_session_state()

    st.header("📚 Literatura")
    st.markdown(
        "Busca papers reales en OpenAlex, genera queries para WoS/Scopus "
        "y construye tu corpus bibliográfico."
    )

    (
        tab_buscar,
        tab_biblio,
        tab_redes,
        tab_eval,
        tab_tesis,
        tab_queries,
        tab_corpus,
    ) = st.tabs(
        [
            "🔎 Buscar",
            "📊 Bibliometría",
            "🕸️ Redes",
            "🤖 Evaluar",
            "🎓 Tesis",
            "🔧 Queries",
            "📚 Corpus",
        ]
    )
    with tab_buscar:
        _render_buscar()
    with tab_biblio:
        _render_bibliometria()
    with tab_redes:
        _render_redes()
    with tab_eval:
        _render_evaluar()
    with tab_tesis:
        _render_tesis()
    with tab_queries:
        _render_queries()
    with tab_corpus:
        _render_corpus()