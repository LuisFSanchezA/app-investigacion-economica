"""Sección Literatura: búsqueda bibliográfica, queries y corpus.

Pestañas:
- Buscar: keywords IA + OpenAlex + añadir al corpus
- Queries: generador para WoS/Scopus/OpenAlex/Scholar
- Corpus: tabla del corpus acumulado + exportar CSV
"""

import json

import pandas as pd
import streamlit as st

from src.ai import sugerir_keywords_cached
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

    tab_buscar, tab_queries, tab_corpus = st.tabs(
        ["🔎 Buscar", "🔧 Queries", "📚 Corpus"]
    )
    with tab_buscar:
        _render_buscar()
    with tab_queries:
        _render_queries()
    with tab_corpus:
        _render_corpus()