"""Sección Tema: diagnóstico, delimitación, justificación, enunciado y resumen.

Consume los insumos de las otras secciones:
- Pregunta: st.session_state["pregunta_final"], ["objetivos_sugeridos"]
- Literatura: st.session_state["lit_corpus"]
- Fuentes de datos: st.session_state["df_fuente"], ["meta_fuente"]
"""

import pandas as pd
import streamlit as st

from src.ai import (
    generar_justificacion_cached,
    generar_resumen_ejecutivo_cached,
    sugerir_enunciado_cached,
)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _init_session_state():
    """Inicializa las claves necesarias en session_state."""
    claves = [
        "tema_fenomeno", "tema_poblacion", "tema_periodo",
        "tema_espacio", "tema_variables",
        "tema_enunciado", "tema_justificacion", "tema_resumen",
        "tema_error",
    ]
    for k in claves:
        if k not in st.session_state:
            st.session_state[k] = ""


def _insumos_disponibles() -> dict:
    """Devuelve un dict con el estado de los insumos."""
    pregunta = st.session_state.get("pregunta_final", "")
    objetivos = st.session_state.get("objetivos_sugeridos", "")
    corpus = st.session_state.get("lit_corpus", [])
    df_fuente = st.session_state.get("df_fuente")
    meta_fuente = st.session_state.get("meta_fuente")

    datos_str = ""
    if meta_fuente is not None:
        datos_str = f"{meta_fuente.fuente}: {meta_fuente.indicador}"

    return {
        "pregunta": pregunta,
        "objetivos": objetivos,
        "n_corpus": len(corpus),
        "datos": datos_str,
        "tiene_pregunta": bool(pregunta),
        "tiene_objetivos": bool(objetivos),
        "tiene_corpus": len(corpus) > 0,
        "tiene_datos": df_fuente is not None,
    }


# ---------------------------------------------------------------------------
# Diagnóstico
# ---------------------------------------------------------------------------

def _render_diagnostico(insumos: dict):
    """Muestra un checklist del estado de los insumos."""
    st.subheader("📋 Diagnóstico de insumos")
    st.caption(
        "Revisa qué tienes ya. Los insumos faltantes no bloquean el trabajo, "
        "pero mejoran la calidad de las sugerencias de IA."
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if insumos["tiene_pregunta"]:
            st.success("✅ Pregunta")
        else:
            st.warning("⚠️ Pregunta")
            st.caption("Ve a **Pregunta** para definirla.")

    with col2:
        if insumos["tiene_objetivos"]:
            st.success("✅ Objetivos")
        else:
            st.warning("⚠️ Objetivos")
            st.caption("Ve a **Pregunta** para generarlos.")

    with col3:
        if insumos["tiene_corpus"]:
            st.success(f"✅ Corpus ({insumos['n_corpus']})")
        else:
            st.warning("⚠️ Corpus")
            st.caption("Ve a **Literatura** para construirlo.")

    with col4:
        if insumos["tiene_datos"]:
            st.success("✅ Datos")
        else:
            st.warning("⚠️ Datos")
            st.caption("Ve a **Fuentes de datos** para consultarlos.")

    if not insumos["tiene_pregunta"]:
        st.info(
            "💡 **Sugerencia:** define tu pregunta de investigación antes de "
            "delimitar el tema. Es el insumo más importante."
        )


# ---------------------------------------------------------------------------
# Delimitación
# ---------------------------------------------------------------------------

def _render_delimitacion():
    """Formulario de delimitación del tema (5 campos)."""
    st.subheader("🎯 Delimitación del tema")
    st.caption(
        "Delimita tu tema en 5 dimensiones. Esto ayuda a que la IA genere "
        "un enunciado específico y una justificación sólida."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.session_state["tema_fenomeno"] = st.text_input(
            "Fenómeno de estudio:",
            value=st.session_state["tema_fenomeno"],
            placeholder="Ej: informalidad laboral",
            key="tema_fenomeno_input",
        )
        st.session_state["tema_poblacion"] = st.text_input(
            "Población:",
            value=st.session_state["tema_poblacion"],
            placeholder="Ej: jóvenes de 15-29 años",
            key="tema_poblacion_input",
        )
        st.session_state["tema_periodo"] = st.text_input(
            "Periodo:",
            value=st.session_state["tema_periodo"],
            placeholder="Ej: 2010-2024",
            key="tema_periodo_input",
        )

    with col2:
        st.session_state["tema_espacio"] = st.text_input(
            "Espacio geográfico:",
            value=st.session_state["tema_espacio"],
            placeholder="Ej: México (nacional)",
            key="tema_espacio_input",
        )
        st.session_state["tema_variables"] = st.text_input(
            "Variables principales:",
            value=st.session_state["tema_variables"],
            placeholder="Ej: salario, informalidad, edad",
            key="tema_variables_input",
        )

    # Ejemplos rápidos
    with st.expander("📖 ¿Qué es cada campo?"):
        st.markdown(
            """
            - **Fenómeno**: el problema o proceso que estudias (informalidad,
              desempleo, migración, etc.).
            - **Población**: a quién estudias (jóvenes, mujeres, trabajadores
              rurales, etc.).
            - **Periodo**: el rango temporal de tu análisis.
            - **Espacio**: el ámbito geográfico (país, estado, región).
            - **Variables**: las dimensiones que analizas.
            """
        )


# ---------------------------------------------------------------------------
# Enunciado
# ---------------------------------------------------------------------------

def _render_enunciado(insumos: dict):
    """Genera y edita el enunciado del tema."""
    st.subheader("📝 Enunciado del tema")
    st.caption(
        "El enunciado es 1-2 líneas que resumen tu tema delimitado. "
        "Es lo primero que un lector verá de tu proyecto."
    )

    if st.button("🤖 Sugerir enunciado con IA", key="btn_sugerir_enunciado"):
        if not insumos["tiene_pregunta"]:
            st.warning(
                "Necesitas una pregunta de investigación. Ve a **Pregunta**."
            )
        else:
            with st.spinner("Generando enunciado... puede tomar 30-60s."):
                try:
                    resultado = sugerir_enunciado_cached(
                        pregunta=insumos["pregunta"],
                        objetivos=insumos["objetivos"],
                        n_corpus=insumos["n_corpus"],
                        datos=insumos["datos"],
                        fenomeno=st.session_state["tema_fenomeno"],
                        poblacion=st.session_state["tema_poblacion"],
                        periodo=st.session_state["tema_periodo"],
                        espacio=st.session_state["tema_espacio"],
                        variables=st.session_state["tema_variables"],
                    )
                    st.session_state["tema_enunciado"] = resultado
                    st.session_state["tema_error"] = ""
                except (ValueError, ConnectionError) as e:
                    st.session_state["tema_error"] = str(e)

    if st.session_state.get("tema_error"):
        st.error(f"⚠️ {st.session_state['tema_error']}")

    if st.session_state["tema_enunciado"]:
        with st.expander("🤖 Sugerencia de IA (borrador — verificar)", expanded=True):
            st.markdown(st.session_state["tema_enunciado"])

    st.session_state["tema_enunciado"] = st.text_area(
        "Edita o escribe tu enunciado final:",
        value=st.session_state["tema_enunciado"],
        height=100,
        key="tema_enunciado_final",
    )


# ---------------------------------------------------------------------------
# Justificación
# ---------------------------------------------------------------------------

def _render_justificacion(insumos: dict):
    """Genera la justificación del tema."""
    st.subheader("💡 Justificación")
    st.caption(
        "La justificación explica por qué vale la pena investigar tu tema: "
        "pertinencia, viabilidad y originalidad."
    )

    if st.button("🤖 Generar justificación con IA", key="btn_generar_justificacion"):
        if not insumos["tiene_pregunta"]:
            st.warning(
                "Necesitas una pregunta de investigación. Ve a **Pregunta**."
            )
        else:
            with st.spinner("Generando justificación... puede tomar 30-60s."):
                try:
                    resultado = generar_justificacion_cached(
                        pregunta=insumos["pregunta"],
                        objetivos=insumos["objetivos"],
                        n_corpus=insumos["n_corpus"],
                        datos=insumos["datos"],
                        fenomeno=st.session_state["tema_fenomeno"],
                        poblacion=st.session_state["tema_poblacion"],
                        periodo=st.session_state["tema_periodo"],
                        espacio=st.session_state["tema_espacio"],
                        variables=st.session_state["tema_variables"],
                    )
                    st.session_state["tema_justificacion"] = resultado
                    st.session_state["tema_error"] = ""
                except (ValueError, ConnectionError) as e:
                    st.session_state["tema_error"] = str(e)

    if st.session_state["tema_justificacion"]:
        st.markdown(st.session_state["tema_justificacion"])


# ---------------------------------------------------------------------------
# Resumen ejecutivo
# ---------------------------------------------------------------------------

def _render_resumen(insumos: dict):
    """Genera el resumen ejecutivo."""
    st.subheader("📄 Resumen ejecutivo")
    st.caption(
        "Un resumen de 1 página que sintetiza todo tu proyecto. "
        "Ideal para presentaciones o para revisar la coherencia."
    )

    if st.button("🤖 Generar resumen ejecutivo con IA", key="btn_generar_resumen"):
        if not insumos["tiene_pregunta"]:
            st.warning("Necesitas una pregunta. Ve a **Pregunta**.")
        elif not st.session_state["tema_enunciado"]:
            st.warning("Necesitas un enunciado del tema. Genera uno primero.")
        else:
            with st.spinner("Generando resumen... puede tomar 30-60s."):
                try:
                    resultado = generar_resumen_ejecutivo_cached(
                        pregunta=insumos["pregunta"],
                        enunciado=st.session_state["tema_enunciado"],
                        objetivos=insumos["objetivos"],
                        n_corpus=insumos["n_corpus"],
                        datos=insumos["datos"],
                        fenomeno=st.session_state["tema_fenomeno"],
                        poblacion=st.session_state["tema_poblacion"],
                        periodo=st.session_state["tema_periodo"],
                        espacio=st.session_state["tema_espacio"],
                        variables=st.session_state["tema_variables"],
                    )
                    st.session_state["tema_resumen"] = resultado
                    st.session_state["tema_error"] = ""
                except (ValueError, ConnectionError) as e:
                    st.session_state["tema_error"] = str(e)

    if st.session_state["tema_resumen"]:
        st.markdown(st.session_state["tema_resumen"])

        # Descargar ficha completa
        st.download_button(
            "⬇️ Descargar ficha del tema (Markdown)",
            data=st.session_state["tema_resumen"],
            file_name="ficha_tema.md",
            mime="text/markdown",
            key="btn_descargar_ficha_tema",
        )


# ---------------------------------------------------------------------------
# Render principal
# ---------------------------------------------------------------------------

def render():
    """Renderiza la sección Tema completa."""
    _init_session_state()

    st.header("🎯 Tema")
    st.markdown(
        "Delimita tu tema, genera un enunciado con IA, justifica tu proyecto "
        "y obtén un resumen ejecutivo."
    )

    insumos = _insumos_disponibles()

    tab_diag, tab_delim, tab_enun, tab_just, tab_resumen = st.tabs(
        ["📋 Diagnóstico", "🎯 Delimitación", "📝 Enunciado", "💡 Justificación", "📄 Resumen"]
    )

    with tab_diag:
        _render_diagnostico(insumos)

    with tab_delim:
        _render_delimitacion()

    with tab_enun:
        _render_enunciado(insumos)

    with tab_just:
        _render_justificacion(insumos)

    with tab_resumen:
        _render_resumen(insumos) 