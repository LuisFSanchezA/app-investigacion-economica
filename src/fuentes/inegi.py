"""Conector para la API de Indicadores del INEGI.

Documentación:
https://www.inegi.org.mx/servicios/api_indicadores.html
"""

from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests

from src.fuentes.base import FuenteBase
from src.fuentes.metadatos import Metadatos


URL_BASE = (
    "https://www.inegi.org.mx/app/api/indicadores/"
    "desarrolladores/jsonxml/INDICATOR"
)

# Catálogo mínimo de indicadores de INEGI.
INDICADORES_INEGI = {
    "756261": {
        "nombre": "PIB nacional (millones de pesos)",
        "unidad": "millones de pesos",
        "area": "0",
        "tipo": "BIE-BISE",
    },
    "1002000001": {
        "nombre": "PIB nacional (millones de pesos) [alt]",
        "unidad": "millones de pesos",
        "area": "0",
        "tipo": "BIE-BISE",
    },
    "6207020038": {
        "nombre": "Población total (personas)",
        "unidad": "personas",
        "area": "0",
        "tipo": "BIE-BISE",
    },
    "6200240357": {
        "nombre": "Tasa de desocupación (% de la PEA)",
        "unidad": "%",
        "area": "0",
        "tipo": "BIE-BISE",
    },
    "1002000003": {
        "nombre": "Inflación anual (%)",
        "unidad": "%",
        "area": "0",
        "tipo": "BIE-BISE",
    },
}

ENTIDADES = {
    "0": "Nacional",
    "01": "Aguascalientes",
    "02": "Baja California",
    "03": "Baja California Sur",
    "04": "Campeche",
    "05": "Coahuila",
    "06": "Colima",
    "07": "Chiapas",
    "08": "Chihuahua",
    "09": "Ciudad de México",
    "10": "Durango",
    "11": "Guanajuato",
    "12": "Guerrero",
    "13": "Hidalgo",
    "14": "Jalisco",
    "15": "Estado de México",
    "16": "Michoacán",
    "17": "Morelos",
    "18": "Nayarit",
    "19": "Nuevo León",
    "20": "Oaxaca",
    "21": "Puebla",
    "22": "Querétaro",
    "23": "Quintana Roo",
    "24": "San Luis Potosí",
    "25": "Sinaloa",
    "26": "Sonora",
    "27": "Tabasco",
    "28": "Tamaulipas",
    "29": "Tlaxcala",
    "30": "Veracruz",
    "31": "Yucatán",
    "32": "Zacatecas",
}


def _get_token() -> str:
    """Obtiene el token de INEGI desde Streamlit secrets o el entorno."""
    try:
        import streamlit as st

        token = st.secrets.get("INEGI_TOKEN")
        if token:
            return str(token)
    except Exception:
        # La aplicación también puede ejecutarse fuera de Streamlit.
        pass

    token = os.environ.get("INEGI_TOKEN")
    if token:
        return token

    raise ValueError(
        "No se encontró INEGI_TOKEN. Configúralo en "
        ".streamlit/secrets.toml o como variable de entorno. "
        "Obtén tu token en "
        "https://www.inegi.org.mx/servicios/api_indicadores.html"
    )


def _obtener_observaciones(datos: Any, indicador: str) -> list[dict]:
    """Valida la respuesta y admite ambas variantes del nombre del campo.

    La documentación de la API utiliza OBSERVATIONS; algunos consumidores,
    mocks o respuestas transformadas utilizan OBSERVACIONES.
    """
    if not isinstance(datos, dict) or "Series" not in datos:
        raise ValueError(
            "La respuesta de INEGI no tiene el formato esperado."
        )

    series = datos["Series"]
    if not isinstance(series, list) or not series:
        raise ValueError(f"No hay datos para el indicador {indicador}.")

    primera_serie = series[0]
    if not isinstance(primera_serie, dict):
        raise ValueError(
            "La respuesta de INEGI no tiene el formato esperado."
        )

    if "OBSERVATIONS" in primera_serie:
        observaciones = primera_serie["OBSERVATIONS"]
    elif "OBSERVACIONES" in primera_serie:
        observaciones = primera_serie["OBSERVACIONES"]
    else:
        raise ValueError(
            "La respuesta de INEGI no tiene el formato esperado: "
            "no se encontró OBSERVATIONS ni OBSERVACIONES."
        )

    if not isinstance(observaciones, list):
        raise ValueError(
            "La respuesta de INEGI no tiene el formato esperado: "
            "las observaciones no son una lista."
        )

    if not observaciones:
        raise ValueError(
            f"No hay observaciones para el indicador {indicador}."
        )

    return observaciones


class INEGI(FuenteBase):
    """Conector para la API de Indicadores del INEGI."""

    @property
    def nombre(self) -> str:
        return "INEGI"

    def consultar(
        self,
        indicador: str,
        pais: str = "México",
        periodo_inicio: int | None = None,
        periodo_fin: int | None = None,
        entidad: str = "0",
    ) -> tuple[pd.DataFrame, Metadatos]:
        """Consulta un indicador de INEGI.

        Args:
            indicador: Código del indicador incluido en el catálogo.
            pais: Se conserva por compatibilidad; INEGI corresponde a México.
            periodo_inicio: Año inicial inclusivo.
            periodo_fin: Año final inclusivo.
            entidad: Código de cobertura geográfica; "0" representa el total
                nacional y "01" a "32" las entidades federativas.

        Returns:
            Una tupla con el DataFrame de observaciones y sus metadatos.
        """
        if indicador not in INDICADORES_INEGI:
            raise ValueError(
                f"Indicador '{indicador}' no está en el catálogo. "
                f"Disponibles: {list(INDICADORES_INEGI.keys())}"
            )

        info = INDICADORES_INEGI[indicador]
        area = info.get("area", "0")
        tipo = info.get("tipo", "BIE-BISE")
        token = _get_token()

        url = (
            f"{URL_BASE}/{indicador}/es/{area}/true/{tipo}/2.0/{token}"
            "?type=json"
        )

        try:
            respuesta = requests.get(url, timeout=45)
        except requests.exceptions.Timeout as exc:
            raise ConnectionError(
                "La consulta a INEGI excedió el tiempo de espera."
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionError(
                "No se pudo conectar con INEGI. Verifica tu conexión."
            ) from exc

        if respuesta.status_code == 401:
            raise ConnectionError(
                "El token de INEGI no es válido o expiró. "
                "Verifica tu token en .streamlit/secrets.toml."
            )

        if respuesta.status_code != 200:
            raise ConnectionError(
                f"INEGI respondió con código {respuesta.status_code}."
            )

        try:
            datos = respuesta.json()
        except ValueError as exc:
            raise ValueError(
                "La respuesta de INEGI no es JSON válido."
            ) from exc

        observaciones = _obtener_observaciones(datos, indicador)

        registros = []
        for obs in observaciones:
            if not isinstance(obs, dict):
                continue

            # Normalizar el código de entidad de la observación
            cober = str(obs.get("COBER_GEO", "0")).zfill(2)
            if cober == "00":
                cober = "0"

            # Normalizar la entidad solicitada
            entidad_consulta = str(entidad).zfill(2)
            if entidad_consulta == "00":
                entidad_consulta = "0"

            # Filtrar SIEMPRE (incluido "0" = Nacional)
            if cober != entidad_consulta:
                continue

            periodo = str(obs.get("TIME_PERIOD", "")).strip()
            anio = periodo.split("/")[0] if "/" in periodo else periodo

            try:
                anio_int = int(anio)
            except (TypeError, ValueError):
                continue

            valor_str = obs.get("OBS_VALUE")
            if valor_str is None or str(valor_str).strip().upper() in {
                "",
                "N/E",
                "NA",
            }:
                valor = None
            else:
                try:
                    valor = float(str(valor_str).replace(",", "").strip())
                except (TypeError, ValueError):
                    valor = None

            registros.append(
                {
                    "anio": anio_int,
                    "valor": valor,
                    "entidad": ENTIDADES.get(cober, f"Entidad {cober}"),
                }
            )

        df = pd.DataFrame(
            registros,
            columns=["anio", "valor", "entidad"],
        )

        if df.empty:
            raise ValueError(
                f"No se pudieron parsear observaciones para {indicador}."
            )

        if periodo_inicio is not None:
            df = df[df["anio"] >= periodo_inicio]

        if periodo_fin is not None:
            df = df[df["anio"] <= periodo_fin]

        df = df.sort_values("anio").reset_index(drop=True)

        if df.empty:
            raise ValueError(
                f"No hay datos para {indicador} en el rango "
                f"{periodo_inicio}-{periodo_fin}."
            )

        metadatos = Metadatos(
            fuente=self.nombre,
            indicador=info["nombre"],
            codigo_indicador=indicador,
            unidad=info["unidad"],
            pais="México",
            periodo_inicio=(
                periodo_inicio
                if periodo_inicio is not None
                else int(df["anio"].min())
            ),
            periodo_fin=(
                periodo_fin
                if periodo_fin is not None
                else int(df["anio"].max())
            ),
            url_fuente=url.replace(str(token), "***") if token else url,
            notas=(
                "Datos descargados de la API de Indicadores del INEGI. "
                f"Entidad: {ENTIDADES.get(str(entidad), entidad)}."
            ),
        )

        return df, metadatos