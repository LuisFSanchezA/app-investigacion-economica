"""Conector para la API de Indicadores del INEGI.

Documentación: https://www.inegi.org.mx/servicios/api_indicadores.html

Estructura de la URL (según el portal de INEGI):
https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/{ids}/{lang}/{area}/{recent}/{type}/false/BISE/2.0/{token}?type=json

Parámetros:
- ids: IDs de indicadores separados por coma (ej. "756261").
- lang: "es" o "en".
- area: "0" para nacional, "07000001" para Aguascalientes, etc.
- recent: "true" (último) o "false" (todos).
- type: "BIE-BISE" (Banco de Indicadores) o "BISE" (Banco de Indicadores Sectoriales).

Respuesta:
{
  "Header": {...},
  "Series": [
    {
      "INDICADOR": "756261",
      "OBSERVATIONS": [
        {"TIME_PERIOD": "2024", "OBS_VALUE": "...", "COBER_GEO": "0"},
        ...
      ]
    }
  ]
}
"""

from __future__ import annotations

import os
from typing import Any

import pandas as pd
import requests

from src.fuentes.base import FuenteBase
from src.fuentes.metadatos import Metadatos

URL_BASE = "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR"

# Catálogo mínimo de indicadores de INEGI
# NOTA: los códigos son los que INEGI usa en su API. Verifica cada uno en
# https://www.inegi.org.mx/servicios/api_indicadores.html
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

# Códigos de entidad federativa (COBER_GEO) para filtrar
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
    """Lee el token de INEGI de secrets o env."""
    try:
        import streamlit as st
        token = st.secrets.get("INEGI_TOKEN")
        if token:
            return token
    except Exception:
        pass
    token = os.environ.get("INEGI_TOKEN")
    if token:
        return token
    raise ValueError(
        "No se encontró INEGI_TOKEN. Configúralo en .streamlit/secrets.toml "
        "o como variable de entorno. Obtén tu token gratis en "
        "https://www.inegi.org.mx/servicios/api_indicadores.html"
    )


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

        Parámetros
        ----------
        indicador : str
            Código del indicador (ej. '756261' para PIB).
        pais : str
            Ignorado (INEGI es solo México). Se conserva por compatibilidad.
        periodo_inicio, periodo_fin : int, opcional
            Rango de años (se filtra en el DataFrame resultante).
        entidad : str
            Código de entidad federativa (COBER_GEO): '0' = nacional,
            '01' = Aguascalientes, ..., '32' = Zacatecas.

        Devuelve
        -------
        tuple[pd.DataFrame, Metadatos]
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
            f"?type=json"
        )

        try:
            respuesta = requests.get(url, timeout=45)
        except requests.exceptions.Timeout:
            raise ConnectionError(
                "La consulta a INEGI excedió el tiempo de espera."
            )
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "No se pudo conectar con INEGI. Verifica tu conexión."
            )

        if respuesta.status_code == 401:
            raise ConnectionError(
                "El token de INEGI no es válido o expiró. "
                "Verifica tu token en .streamlit/secrets.toml"
            )
        if respuesta.status_code != 200:
            raise ConnectionError(
                f"INEGI respondió con código {respuesta.status_code}."
            )

        try:
            datos = respuesta.json()
        except ValueError:
            raise ValueError("La respuesta de INEGI no es JSON válido.")

        try:
            series = datos["Series"]
            if not series or "OBSERVATIONS" not in series[0]:
                raise ValueError(
                    f"No hay datos para el indicador {indicador}."
                )
            observaciones = series[0]["OBSERVATIONS"]
        except (KeyError, TypeError):
            raise ValueError(
                "La respuesta de INEGI no tiene el formato esperado."
            )

        if not observaciones:
            raise ValueError(
                f"No hay observaciones para el indicador {indicador}."
            )

        registros = []
        for obs in observaciones:
            # Filtrar por entidad
            cober = str(obs.get("COBER_GEO", "0"))
            if entidad != "0" and cober != entidad:
                continue

            periodo = str(obs.get("TIME_PERIOD", ""))
            anio = periodo.split("/")[0] if "/" in periodo else periodo
            try:
                anio_int = int(anio)
            except ValueError:
                continue

            valor_str = obs.get("OBS_VALUE", "")
            if valor_str in ("", "N/E", "NA", None):
                valor = None
            else:
                try:
                    valor = float(str(valor_str).replace(",", ""))
                except ValueError:
                    valor = None

            registros.append({
                "anio": anio_int,
                "valor": valor,
                "entidad": ENTIDADES.get(cober, cober),
            })

        df = pd.DataFrame(registros)
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
            periodo_inicio=periodo_inicio or int(df["anio"].min()),
            periodo_fin=periodo_fin or int(df["anio"].max()),
            url_fuente=url.replace(token, "***"),
            notas=(
                f"Datos descargados de la API de Indicadores del INEGI. "
                f"Entidad: {ENTIDADES.get(entidad, entidad)}."
            ),
        )

        return df, metadatos