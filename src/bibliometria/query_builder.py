"""Generador de queries de búsqueda para distintas bases bibliográficas.

No consulta WoS ni Scopus (APIs de pago); solo produce la cadena de búsqueda
lista para que el estudiante la pegue en la interfaz web de cada base.

Referencias de sintaxis:
- WoS:  https://webofscience.help.clarivate.com/
- Scopus: https://service.elsevier.com/app/answers/detail/a_id/11365/
- OpenAlex: https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/search-entities
- Google Scholar: https://scholar.google.com/intl/es/scholar/help.html
"""

from __future__ import annotations

from typing import Iterable, Sequence


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------

def formatear_keywords(keywords: Iterable[str]) -> list[str]:
    """Normaliza una lista de palabras clave.

    - Quita espacios sobrantes.
    - Descarta vacías.
    - Deduplica preservando orden (case-insensitive).
    - Envuelve en comillas dobles las que tienen espacios (frases).
    """
    vistas: set[str] = set()
    limpias: list[str] = []
    for kw in keywords:
        kw = " ".join(kw.split()).strip()
        if not kw:
            continue
        clave = kw.lower()
        if clave in vistas:
            continue
        vistas.add(clave)
        if " " in kw:
            limpias.append(f'"{kw}"')
        else:
            limpias.append(kw)
    return limpias


def _unir_con_or(items: Sequence[str]) -> str:
    """Une una lista con ' OR '."""
    return " OR ".join(items)


def _validar_rango(desde: int | None, hasta: int | None) -> tuple[int, int]:
    """Valida y normaliza un rango de años.

    Si ambos son None, devuelve (1900, año actual aproximado 2100).
    Si solo uno se da, se completa con un valor razonable.
    """
    if desde is None and hasta is None:
        return (1900, 2100)
    if desde is None:
        desde = 1900
    if hasta is None:
        hasta = 2100
    if desde > hasta:
        raise ValueError(
            f"El año inicial ({desde}) no puede ser mayor que el final ({hasta})."
        )
    return (desde, hasta)


# ---------------------------------------------------------------------------
# Constructores de query
# ---------------------------------------------------------------------------

def construir_query_wos(
    keywords: Iterable[str],
    desde: int | None = None,
    hasta: int | None = None,
    tipos: Sequence[str] | None = None,
    idiomas: Sequence[str] | None = None,
) -> str:
    """Construye una query para Web of Science (sintaxis avanzada).

    Parámetros
    ----------
    keywords : iterable de str
        Palabras clave o frases. Se combinan con OR dentro de TS=.
    desde, hasta : int, opcional
        Rango de años (campo PY).
    tipos : secuencia de str, opcional
        Tipos de documento WoS: 'Article', 'Review', 'Book', 'Book Chapter',
        'Thesis', 'Report'. Se combinan con OR dentro de DT=.
    idiomas : secuencia de str, opcional
        Códigos de idioma WoS: 'Spanish', 'English', 'Portuguese', etc.

    Devuelve
    -------
    str
        Query lista para pegar en la búsqueda avanzada de WoS.
    """
    kws = formatear_keywords(keywords)
    if not kws:
        raise ValueError("Debes proporcionar al menos una palabra clave.")

    partes: list[str] = [f"TS=({_unir_con_or(kws)})"]

    desde_v, hasta_v = _validar_rango(desde, hasta)
    partes.append(f"PY=({desde_v}-{hasta_v})")

    if tipos:
        tipos_limpios = [t.strip() for t in tipos if t.strip()]
        if tipos_limpios:
            partes.append(f"DT=({_unir_con_or(tipos_limpios)})")

    if idiomas:
        idiomas_limpios = [i.strip() for i in idiomas if i.strip()]
        if idiomas_limpios:
            partes.append(f"LA=({_unir_con_or(idiomas_limpios)})")

    return "\nAND ".join(partes)


def construir_query_scopus(
    keywords: Iterable[str],
    desde: int | None = None,
    hasta: int | None = None,
    tipos: Sequence[str] | None = None,
    idiomas: Sequence[str] | None = None,
) -> str:
    """Construye una query para Scopus (Advanced Search).

    Notas de sintaxis:
    - TITLE-ABS-KEY busca en título, resumen y palabras clave.
    - PUBYEAR usa > y < (no rangos con guion).
    - DOCTYPE usa códigos: 'ar' (article), 're' (review), 'bk' (book),
      'ch' (chapter), 'cp' (conference paper).
    - LANGUAGE usa códigos de 2 letras: 'spa', 'eng', 'por'.
    """
    kws = formatear_keywords(keywords)
    if not kws:
        raise ValueError("Debes proporcionar al menos una palabra clave.")

    partes: list[str] = [f"TITLE-ABS-KEY({_unir_con_or(kws)})"]

    desde_v, hasta_v = _validar_rango(desde, hasta)
    # Scopus requiere dos condiciones separadas
    partes.append(f"PUBYEAR > {desde_v - 1}")
    partes.append(f"PUBYEAR < {hasta_v + 1}")

    if tipos:
        tipos_limpios = [t.strip() for t in tipos if t.strip()]
        if tipos_limpios:
            partes.append(f"DOCTYPE({_unir_con_or(tipos_limpios)})")

    if idiomas:
        idiomas_limpios = [i.strip() for i in idiomas if i.strip()]
        if idiomas_limpios:
            partes.append(f"LANGUAGE({_unir_con_or(idiomas_limpios)})")

    return "\nAND ".join(partes)


def construir_query_openalex(
    keywords: Iterable[str],
    desde: int | None = None,
    hasta: int | None = None,
    tipos: Sequence[str] | None = None,
    idiomas: Sequence[str] | None = None,
) -> str:
    """Construye una query para OpenAlex (parámetro `search` o `filter`).

    Devuelve una cadena pensada para el parámetro `filter` de OpenAlex,
    que es el que permite combinar búsqueda + año + tipo + idioma.

    Ejemplo de salida:
        "informalidad laboral,informal employment,from_publication_date:2015-01-01,to_publication_date:2025-12-31,type:article|review,language:es|en"
    """
    kws = formatear_keywords(keywords)
    if not kws:
        raise ValueError("Debes proporcionar al menos una palabra clave.")

    # OpenAlex no usa comillas; limpiamos las que añadió formatear_keywords
    kws_planas = [k.strip('"') for k in kws]

    desde_v, hasta_v = _validar_rango(desde, hasta)

    filtros: list[str] = [
        ",".join(kws_planas),  # búsqueda textual (search)
        f"from_publication_date:{desde_v}-01-01",
        f"to_publication_date:{hasta_v}-12-31",
    ]

    if tipos:
        tipos_limpios = [t.strip() for t in tipos if t.strip()]
        if tipos_limpios:
            filtros.append(f"type:{'|'.join(tipos_limpios)}")

    if idiomas:
        idiomas_limpios = [i.strip() for i in idiomas if i.strip()]
        if idiomas_limpios:
            filtros.append(f"language:{'|'.join(idiomas_limpios)}")

    return ",".join(filtros)


def construir_query_google_scholar(
    keywords: Iterable[str],
    desde: int | None = None,
    hasta: int | None = None,
) -> str:
    """Construye una query para Google Scholar (solo texto, sin API).

    Google Scholar no tiene API oficial; esto solo produce una cadena que
    el estudiante puede pegar en la búsqueda avanzada o en la barra.
    """
    kws = formatear_keywords(keywords)
    if not kws:
        raise ValueError("Debes proporcionar al menos una palabra clave.")

    base = _unir_con_or(kws)
    desde_v, hasta_v = _validar_rango(desde, hasta)

    # Google Scholar no soporta rangos de años en la barra; se sugiere
    # usar la búsqueda avanzada. Añadimos pista textual.
    return f"{base}  (rango sugerido: {desde_v}-{hasta_v})"


# ---------------------------------------------------------------------------
# Catálogos de códigos por base (para la UI)
# ---------------------------------------------------------------------------

TIPOS_WOS = {
    "Article": "Article",
    "Review": "Review",
    "Book": "Book",
    "Book Chapter": "Book Chapter",
    "Thesis": "Thesis",
    "Report": "Report",
}

TIPOS_SCOPUS = {
    "ar": "Article",
    "re": "Review",
    "bk": "Book",
    "ch": "Book Chapter",
    "cp": "Conference Paper",
}

TIPOS_OPENALEX = {
    "article": "Article",
    "review": "Review",
    "book": "Book",
    "book-chapter": "Book Chapter",
    "dissertation": "Dissertation / Thesis",
    "report": "Report",
}

IDIOMAS_WOS = {
    "Spanish": "Spanish",
    "English": "English",
    "Portuguese": "Portuguese",
}

IDIOMAS_SCOPUS = {
    "spa": "Spanish",
    "eng": "English",
    "por": "Portuguese",
}

IDIOMAS_OPENALEX = {
    "es": "Spanish",
    "en": "English",
    "pt": "Portuguese",
}