"""Conector para la API pública de OpenAlex.

Documentación: https://docs.openalex.org/

OpenAlex no requiere autenticación. Se recomienda enviar un email en el
parámetro `mailto` para entrar al "polite pool" (mejor rate limit).

La API devuelve JSON con:
- `meta`: información de paginación (count, page, per_page, next_cursor)
- `results`: lista de trabajos

Estrategia de paginación:
- OpenAlex permite hasta `per_page=200`.
- Para corpus grandes se usa `cursor=*` (cursor-based pagination).
- Aquí usamos cursor-based para evitar el límite de 10,000 resultados
  del page-based.
"""

from __future__ import annotations

import time
from typing import Any, Iterable

import pandas as pd
import requests

from src.fuentes.base import FuenteBase
from src.fuentes.metadatos import Metadatos

URL_BASE = "https://api.openalex.org/works"

# Email de cortesía para el "polite pool" de OpenAlex.
# Cámbialo por tu correo real si quieres mejores límites.
EMAIL_CORTESIA = "investigacion-economica@example.com"

# Máximo de resultados por página permitido por OpenAlex
PER_PAGE = 200

# Límite de seguridad para no descargar corpus gigantes por accidente
MAX_RESULTADOS = 2000


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

        # Validar rango de años
        if desde is not None and hasta is not None and desde > hasta:
            raise ValueError(
                f"El año inicial ({desde}) no puede ser mayor que el final ({hasta})."
            )

        limite = max(1, min(int(limite), MAX_RESULTADOS))

        # Construir parámetros base
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

        # Descargar con paginación por cursor
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
        Aquí interpretamos `indicador` como la consulta de búsqueda textual
        y delegamos en `buscar()`. `pais` se ignora (OpenAlex es
        internacional).

        Este método existe solo para satisfacer la interfaz abstracta de
        `FuenteBase`; la UI de Literatura usará `buscar()` directamente.
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
        """Descarga resultados usando cursor-based pagination.

        Devuelve (lista_de_resultados, url_de_la_primera_consulta).
        """
        resultados: list[dict[str, Any]] = []
        cursor = "*"
        url_primera = ""

        while len(resultados) < limite:
            params: dict[str, Any] = {
                "search": search,
                "per-page": min(PER_PAGE, limite - len(resultados)),
                "cursor": cursor,
                "mailto": EMAIL_CORTESIA,
            }
            if filtro:
                params["filter"] = filtro

            url = URL_BASE
            if not url_primera:
                # Guardamos la URL "reproducible" (sin cursor) para metadatos
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

            # Siguiente cursor
            meta = datos.get("meta", {})
            siguiente = meta.get("next_cursor")
            if not siguiente:
                break
            cursor = siguiente

            # Cortesía con la API: pequeña pausa entre páginas
            time.sleep(0.2)

        return resultados, url_primera

    def _normalizar(self, resultados: list[dict[str, Any]]) -> pd.DataFrame:
        """Convierte la lista cruda de OpenAlex en un DataFrame tabular."""
        registros: list[dict[str, Any]] = []

        for r in resultados:
            # Autores
            autores = [
                a.get("author", {}).get("display_name", "")
                for a in (r.get("authorships") or [])
                if a.get("author")
            ]
            autores = [a for a in autores if a]

            # Instituciones (únicas, sin vacías)
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

            # Fuente (revista, libro, etc.)
            primary = r.get("primary_location") or {}
            source = primary.get("source") or {}
            fuente_nombre = source.get("display_name") or ""

            # Conceptos (top 10 por score)
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

            # Open access
            oa = r.get("open_access") or {}
            es_oa = bool(oa.get("is_oa"))

            # Idioma
            idioma = r.get("language") or ""

            # Referencias
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
        """Reconstruye el resumen desde el índice invertido de OpenAlex.

        OpenAlex devuelve `abstract_inverted_index` como un dict
        {palabra: [posiciones]}. Lo convertimos a texto plano.
        """
        inv = r.get("abstract_inverted_index")
        if not inv:
            return ""
        # Construir lista (posición, palabra)
        pares: list[tuple[int, str]] = []
        for palabra, posiciones in inv.items():
            for pos in posiciones:
                pares.append((pos, palabra))
        pares.sort()
        return " ".join(p for _, p in pares)

    @staticmethod
    def _deduplicar(df: pd.DataFrame) -> pd.DataFrame:
        """Deduplica por DOI (si existe) o por título normalizado.

        Reglas:
        - Si hay DOI, se usa como clave.
        - Si no hay DOI, se usa título en minúsculas sin espacios extra.
        - Se conserva la primera ocurrencia.
        """
        if df.empty:
            return df

        df = df.copy()

        # Clave de deduplicación
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

        # Conservar primera ocurrencia (y descartar claves vacías)
        df = df[df["_clave_dedup"] != ""]
        df = df.drop_duplicates(subset="_clave_dedup", keep="first")
        df = df.drop(columns="_clave_dedup").reset_index(drop=True)

        return df