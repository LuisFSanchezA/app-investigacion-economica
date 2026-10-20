"""Conector para la API del Banco de México (SIE).

Documentación: https://www.banxico.org.mx/SieAPIRest/service/v1/doc/

La API requiere un token gratuito que se envía en el header `Bmx-Token`.
"""

import pandas as pd
import requests

from src.fuentes.base import FuenteBase
from src.fuentes.metadatos import Metadatos

URL_BASE = "https://www.banxico.org.mx/SieAPIRest/service/v1"

# Catálogo de series disponibles
SERIES = {
    "SF43718": {
        "nombre": "Tipo de cambio FIX",
        "unidad": "MXN por USD",
    },
    "SF283": {
        "nombre": "Reservas internacionales",
        "unidad": "millones de USD",
    },
    "SR14849": {
        "nombre": "Tasa de interés objetivo",
        "unidad": "%",
    },
    "SP68257": {
        "nombre": "Inflación anual",
        "unidad": "%",
    },
    "SL11295": {
        "nombre": "Tasa de desempleo",
        "unidad": "%",
    },
}


def _get_token() -> str:
    """Lee el token de Banxico desde st.secrets."""
    import streamlit as st
    try:
        return st.secrets["BANXICO_TOKEN"]
    except (KeyError, FileNotFoundError):
        raise ValueError(
            "No se encontró BANXICO_TOKEN en .streamlit/secrets.toml. "
            "Configura tu token de Banxico antes de usar esta fuente."
        )


class Banxico(FuenteBase):
    """Conector para la API del Banco de México."""

    @property
    def nombre(self) -> str:
        return "Banco de México"

    def consultar(
        self,
        indicador: str,
        pais: str,
        periodo_inicio: int,
        periodo_fin: int,
    ) -> tuple[pd.DataFrame, Metadatos]:
        """Consulta una serie de Banxico.

        Parámetros
        ----------
        indicador : str
            Código de la serie (ej: 'SF43718').
        pais : str
            Ignorado (Banxico es solo México). Se conserva por compatibilidad.
        periodo_inicio : int
            Año inicial.
        periodo_fin : int
            Año final.
        """
        token = _get_token()

        fecha_inicio = f"{periodo_inicio}-01-01"
        fecha_fin = f"{periodo_fin}-12-31"
        url = f"{URL_BASE}/series/{indicador}/datos/{fecha_inicio}/{fecha_fin}"

        try:
            respuesta = requests.get(
                url,
                headers={"Bmx-Token": token},
                timeout=60,
            )
        except requests.exceptions.Timeout:
            raise ConnectionError(
                "La consulta a Banxico excedió el tiempo de espera."
            )
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "No se pudo conectar con Banxico. Verifica tu conexión."
            )

        if respuesta.status_code == 401:
            raise ConnectionError(
                "El token de Banxico no es válido o expiró. "
                "Verifica tu token en .streamlit/secrets.toml"
            )
        if respuesta.status_code != 200:
            raise ConnectionError(
                f"Banxico respondió con código {respuesta.status_code}."
            )

        try:
            datos = respuesta.json()
        except ValueError:
            raise ValueError("La respuesta de Banxico no es JSON válido.")

        try:
            series = datos["bmx"]["series"]
        except (KeyError, TypeError):
            raise ValueError(
                "La respuesta de Banxico no tiene el formato esperado."
            )

        if not series or "datos" not in series[0]:
            raise ValueError(
                f"No hay datos para la serie {indicador} "
                f"entre {periodo_inicio} y {periodo_fin}."
            )

        serie_info = series[0]
        titulo_crudo = serie_info.get("titulo", indicador)
        titulo = " ".join(titulo_crudo.split())
        observaciones = serie_info["datos"]

        registros = []
        for obs in observaciones:
            valor_str = obs.get("dato", "")
            fecha_str = obs.get("fecha", "")
            if valor_str == "N/E" or not valor_str:
                valor = None
            else:
                try:
                    valor = float(valor_str.replace(",", ""))
                except ValueError:
                    valor = None
            registros.append({"fecha": fecha_str, "valor": valor})

        df = pd.DataFrame(registros)
        if df.empty:
            raise ValueError(
                f"No hay datos para la serie {indicador} "
                f"entre {periodo_inicio} y {periodo_fin}."
            )

        # Banxico usa formato DD/MM/YYYY
        df["fecha"] = pd.to_datetime(
            df["fecha"], format="%d/%m/%Y", errors="coerce"
        )
        df = df.dropna(subset=["fecha"]).sort_values("fecha").reset_index(drop=True)

        info_serie = SERIES.get(indicador, {})
        metadatos = Metadatos(
            fuente=self.nombre,
            indicador=titulo,
            codigo_indicador=indicador,
            unidad=info_serie.get("unidad", ""),
            pais="México",
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            url_fuente=url,
            notas="Datos descargados de la API SIE del Banco de México.",
        )

        return df, metadatos