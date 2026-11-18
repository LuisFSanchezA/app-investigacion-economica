"""Conector para la API pública de OpenAlex.

Documentación: https://docs.openalex.org/

OpenAlex no requiere autenticación, pero se recomienda:
- Enviar un email en `mailto` para el "polite pool".
- Usar `OPENALEX_API_KEY` (gratis en https://openalex.org/rest-api)
  para evitar la pausa de búsquedas anónimas.

La API devuelve JSON con:
- `meta`: información de paginación (count, page, per_page, next_cursor)
- `results`: lista de trabajos

Estrategia de paginación:
- OpenAlex permite hasta `per_page=200`.
- Usamos cursor-based pagination (cursor=*) para evitar el límite
  de 10,000 resultados del page-based.
"""

from __future__ import annotations

import os
import time
from typing import Any, Iterable

import pandas as pd
import requests

from src.fuentes.base import FuenteBase
from src.fuentes.metadatos import Metadatos

URL_BASE = "https://api.openalex.org/works"

# Email de cortesía para el "polite pool" de OpenAlex.
EMAIL_CORTESIA = "investigacioneconomica0@gmail.com"

# Máximo de resultados por página permitido por OpenAlex
PER_PAGE = 200

# Límite de seguridad para no descargar corpus gigantes por accidente
MAX_RESULTADOS = 2000


# ---------------------------------------------------------------------------
# Lectura de credenciales (secrets > env > fallback)
# ---------------------------------------------------------------------------

def _get_api_key() -> str | None:
    """Lee OPENALEX_API_KEY de secrets o env, si existe."""
    try:
        import streamlit as st
        key = st.secrets.get("OPENALEX_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("OPENALEX_API_KEY")


def _get_email() -> str:
    """Lee OPENALEX_EMAIL de secrets o usa fallback."""
    try:
        import streamlit as st
        email = st.secrets.get("OPENALEX_EMAIL")
        if email:
            return email
    except Exception:
        pass
    return os.environ.get("OPENALEX_EMAIL", EMAIL_CORTESIA)


# ---------------------------------------------------------------------------
# Conector
# ---------------------------------------------------------------------------

class OpenAlex(FuenteBase):
    """Conector para la API pública de OpenAlex."""

    @property
    def nombre(self) -> str:
        return "OpenAlex"

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def buscar(
        self,
        keywords: Iterable[str],
        desde: int | None = None,
        hasta: int | None = None,
        tipos: list[str] | None = None,
        idiomas: list[str] | None = None,
        open_access: bool | None = None,
        limite: int = 200,
    ) -> tuple[pd.DataFrame, Metadatos]:
        """Busca trabajos en OpenAlex.

        Parámetros
        ----------
        keywords : iterable de str
            Palabras clave o frases. Se envían en el parámetro `search`.
        desde, hasta : int, opcional
            Rango de años de publicación.
        tipos : list[str], opcional
            Tipos OpenAlex: 'article', 'review', 'book', 'book-chapter',
            'dissertation', 'report', etc.
        idiomas : list[str], opcional
            Códigos ISO 639-1: 'es', 'en', 'pt'.
        open_access : bool, opcional
            Si True, solo trabajos de acceso abierto.
        limite : int
            Número máximo de resultados a descargar (default 200).

        Devuelve
        -------
        tuple[pd.DataFrame, Metadatos]

        Levanta
        ------
        ConnectionError
            Si no se puede conectar o la API responde con error HTTP.
        ValueError
            Si no hay keywords o la respuesta está mal formada.
        """
        kws = [k.strip() for k in keywords if k and k.strip()]
        if not kws:
            raise ValueError("Debes proporcionar al menos una palabra clave.")

        if desde is not None and hasta is not None and desde > hasta:
            raise ValueError(
                f"El año inicial ({desde}) no puede ser mayor que el final ({hasta})."
            )

        limite = max(1, min(int(limite), MAX_RESULTADOS))

        search = " ".join(kws)
        filtros: list[str] = []

        if desde is not None:
            filtros.append(f"from_publication_date:{desde}-01-01")
        if hasta is not None:
            filtros.append(f"to_publication_date:{hasta}-12-31")
        if tipos:
            tipos_limpios = [t.strip() for t in tipos if t.strip()]
            if tipos_limpios:
                filtros.append(f"type:{'|'.join(tipos_limpios)}")
        if idiomas:
            idiomas_limpios = [i.strip() for i in idiomas if i.strip()]
            if idiomas_limpios:
                filtros.append(f"language:{'|'.join(idiomas_limpios)}")
        if open_access is True:
            filtros.append("is_oa:true")

        filtro_str = ",".join(filtros) if filtros else None

        resultados, url_consulta = self._descargar_paginado(
            search=search,
            filtro=filtro_str,
            limite=limite,
        )

        if not resultados:
            raise ValueError(
                f"No se encontraron trabajos para '{search}' "
                f"con los filtros aplicados."
            )

        df = self._normalizar(resultados)
        df = self._deduplicar(df)

        metadatos = Metadatos(
            fuente=self.nombre,
            indicador=f"Búsqueda: {search}",
            codigo_indicador="openalex_search",
            unidad="trabajos",
            pais="Internacional",
            periodo_inicio=desde if desde is not None else 0,
            periodo_fin=hasta if hasta is not None else 0,
            url_fuente=url_consulta,
            notas=(
                f"Búsqueda en OpenAlex con {len(df)} trabajos únicos. "
                f"Filtros: {filtro_str or 'ninguno'}."
            ),
        )

        return df, metadatos

    def consultar(
        self,
        indicador: str,
        pais: str = "Internacional",
        periodo_inicio: int | None = None,
        periodo_fin: int | None = None,
    ) -> tuple[pd.DataFrame, Metadatos]:
        """Compatibilidad con `FuenteBase`.

        OpenAlex no maneja indicadores ni países como World Bank/Banxico.
        Interpretamos `indicador` como la consulta de búsqueda textual
        y delegamos en `buscar()`.
        """
        return self.buscar(
            keywords=[indicador],
            desde=periodo_inicio,
            hasta=periodo_fin,
        )

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _descargar_paginado(
        self,
        search: str,
        filtro: str | None,
        limite: int,
    ) -> tuple[list[dict[str, Any]], str]:
        """Descarga resultados usando cursor-based pagination."""
        resultados: list[dict[str, Any]] = []
        cursor = "*"
        url_primera = ""

        while len(resultados) < limite:
            params: dict[str, Any] = {
                "search": search,
                "per-page": min(PER_PAGE, limite - len(resultados)),
                "cursor": cursor,
                "mailto": _get_email(),
            }
            api_key = _get_api_key()
            if api_key:
                params["api_key"] = api_key
            if filtro:
                params["filter"] = filtro

            url = URL_BASE
            if not url_primera:
                from urllib.parse import urlencode
                url_primera = f"{URL_BASE}?{urlencode(params)}"

            try:
                respuesta = requests.get(url, params=params, timeout=45)
            except requests.exceptions.Timeout:
                raise ConnectionError(
                    "La consulta a OpenAlex excedió el tiempo de espera."
                )
            except requests.exceptions.ConnectionError:
                raise ConnectionError(
                    "No se pudo conectar con OpenAlex. "
                    "Verifica tu conexión a internet."
                )

            if respuesta.status_code == 503:
                raise ConnectionError(
                    "OpenAlex está temporalmente saturado (503). "
                    "Si esto es frecuente, configura OPENALEX_API_KEY "
                    "en .streamlit/secrets.toml (gratis en "
                    "https://openalex.org/rest-api)."
                )
            if respuesta.status_code != 200:
                raise ConnectionError(
                    f"OpenAlex respondió con código {respuesta.status_code}."
                )

            try:
                datos = respuesta.json()
            except ValueError:
                raise ValueError("La respuesta de OpenAlex no es JSON válido.")

            if not isinstance(datos, dict) or "results" not in datos:
                raise ValueError(
                    "La respuesta de OpenAlex no tiene el formato esperado."
                )

            lote = datos.get("results") or []
            if not lote:
                break

            resultados.extend(lote)

            meta = datos.get("meta", {})
            siguiente = meta.get("next_cursor")
            if not siguiente:
                break
            cursor = siguiente

            time.sleep(0.2)

        return resultados, url_primera

    def _normalizar(self, resultados: list[dict[str, Any]]) -> pd.DataFrame:
        """Convierte la lista cruda de OpenAlex en un DataFrame tabular."""
        registros: list[dict[str, Any]] = []

        for r in resultados:
            autores = [
                a.get("author", {}).get("display_name", "")
                for a in (r.get("authorships") or [])
                if a.get("author")
            ]
            autores = [a for a in autores if a]

            instituciones: list[str] = []
            paises: list[str] = []
            for a in r.get("authorships") or []:
                for inst in a.get("institutions") or []:
                    nombre = inst.get("display_name")
                    if nombre and nombre not in instituciones:
                        instituciones.append(nombre)
                    pais = inst.get("country_code")
                    if pais and pais not in paises:
                        paises.append(pais)

            primary = r.get("primary_location") or {}
            source = primary.get("source") or {}
            fuente_nombre = source.get("display_name") or ""

            conceptos_raw = r.get("concepts") or []
            conceptos_ordenados = sorted(
                conceptos_raw,
                key=lambda c: c.get("score", 0),
                reverse=True,
            )[:10]
            conceptos = [
                c.get("display_name", "")
                for c in conceptos_ordenados
                if c.get("display_name")
            ]

            oa = r.get("open_access") or {}
            es_oa = bool(oa.get("is_oa"))

            idioma = r.get("language") or ""
            referencias = r.get("referenced_works") or []

            registros.append(
                {
                    "id": r.get("id", ""),
                    "doi": r.get("doi") or "",
                    "titulo": r.get("title") or r.get("display_name") or "",
                    "autores": "; ".join(autores),
                    "instituciones": "; ".join(instituciones),
                    "paises": "; ".join(paises),
                    "anio": r.get("publication_year"),
                    "tipo": r.get("type") or "",
                    "fuente": fuente_nombre,
                    "idioma": idioma,
                    "citas": r.get("cited_by_count", 0),
                    "open_access": es_oa,
                    "conceptos": "; ".join(conceptos),
                    "n_referencias": len(referencias),
                    "referencias": referencias,
                    "resumen": self._reconstruir_resumen(r),
                }
            )

        return pd.DataFrame(registros)

    @staticmethod
    def _reconstruir_resumen(r: dict[str, Any]) -> str:
        """Reconstruye el resumen desde el índice invertido de OpenAlex."""
        inv = r.get("abstract_inverted_index")
        if not inv:
            return ""
        pares: list[tuple[int, str]] = []
        for palabra, posiciones in inv.items():
            for pos in posiciones:
                pares.append((pos, palabra))
        pares.sort()
        return " ".join(p for _, p in pares)

    @staticmethod
    def _deduplicar(df: pd.DataFrame) -> pd.DataFrame:
        """Deduplica por DOI (si existe) o por título normalizado."""
        if df.empty:
            return df

        df = df.copy()

        doi_norm = df["doi"].fillna("").str.lower().str.strip()
        titulo_norm = (
            df["titulo"]
            .fillna("")
            .str.lower()
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        clave = doi_norm.where(doi_norm != "", titulo_norm)
        df["_clave_dedup"] = clave

        df = df[df["_clave_dedup"] != ""]
        df = df.drop_duplicates(subset="_clave_dedup", keep="first")
        df = df.drop(columns="_clave_dedup").reset_index(drop=True)

        return df