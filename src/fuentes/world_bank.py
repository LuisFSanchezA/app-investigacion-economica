"""Conector para la API pública del Banco Mundial.

Documentación: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392

La API no requiere autenticación. Devuelve JSON con dos elementos:
- [0]: metadatos de la consulta (paginación, última actualización)
- [1]: lista de observaciones (una por año)
"""

import pandas as pd
import requests

from src.fuentes.base import FuenteBase
from src.fuentes.metadatos import Metadatos

URL_BASE = "https://api.worldbank.org/v2"

# Catálogo mínimo de indicadores disponibles
INDICADORES = {
    "NY.GDP.MKTP.CD": {
        "nombre": "PIB (USD corrientes)",
        "unidad": "USD corrientes",
    },
    "NY.GDP.PCAP.CD": {
        "nombre": "PIB per cápita (USD corrientes)",
        "unidad": "USD corrientes",
    },
    "SP.POP.TOTL": {
        "nombre": "Población total",
        "unidad": "personas",
    },
    "SL.UEM.TOTL.ZS": {
        "nombre": "Tasa de desempleo (% de la población activa)",
        "unidad": "%",
    },
}

# Catálogo mínimo de países
PAISES = {
    "MEX": "México",
    "USA": "Estados Unidos",
    "BRA": "Brasil",
    "ARG": "Argentina",
    "CHL": "Chile",
    "COL": "Colombia",
}


class BancoMundial(FuenteBase):
    """Conector para la API pública del Banco Mundial."""

    @property
    def nombre(self) -> str:
        return "Banco Mundial"

    def consultar(
        self,
        indicador: str,
        pais: str,
        periodo_inicio: int,
        periodo_fin: int,
    ) -> tuple[pd.DataFrame, Metadatos]:
        """Consulta una serie del Banco Mundial.

        Parámetros
        ----------
        indicador : str
            Código del indicador (ej: 'NY.GDP.MKTP.CD').
        pais : str
            Código ISO3 del país (ej: 'MEX').
        periodo_inicio : int
            Año inicial.
        periodo_fin : int
            Año final.

        Devuelve
        -------
        tuple[pd.DataFrame, Metadatos]

        Levanta
        ------
        ConnectionError
            Si no se puede conectar con la API.
        ValueError
            Si la respuesta está vacía o mal formada.
        """
        url = (
            f"{URL_BASE}/country/{pais}/indicator/{indicador}"
            f"?format=json&per_page=1000&date={periodo_inicio}:{periodo_fin}"
        )

        # --- Manejo de errores de conexión ---
        try:
            respuesta = requests.get(url, timeout=45)
        except requests.exceptions.Timeout:
            raise ConnectionError(
                "La consulta al Banco Mundial excedió el tiempo de espera."
            )
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "No se pudo conectar con el Banco Mundial. "
                "Verifica tu conexión a internet."
            )

        # --- Manejo de errores HTTP ---
        if respuesta.status_code != 200:
            raise ConnectionError(
                f"El Banco Mundial respondió con código {respuesta.status_code}."
            )

        # --- Manejo de respuesta vacía o mal formada ---
        try:
            datos = respuesta.json()
        except ValueError:
            raise ValueError("La respuesta del Banco Mundial no es JSON válido.")

        if not isinstance(datos, list) or len(datos) < 2:
            raise ValueError(
                f"El país '{pais}' o el indicador '{indicador}' no son válidos "
                f"en el Banco Mundial. Verifica los códigos."
            )

        if datos[1] is None or len(datos[1]) == 0:
            raise ValueError(
                f"No hay datos disponibles para el indicador {indicador} "
                f"en {pais} entre {periodo_inicio} y {periodo_fin}."
            )

        # --- Conversión a DataFrame ---
        observaciones = datos[1]
        registros = []
        for obs in observaciones:
            registros.append(
                {
                    "anio": int(obs["date"]),
                    "valor": obs["value"],  # puede ser None
                    "pais_codigo": obs["countryiso3code"],
                    "pais_nombre": obs["country"]["value"],
                    "indicador_codigo": obs["indicator"]["id"],
                    "indicador_nombre": obs["indicator"]["value"],
                }
            )

        df = pd.DataFrame(registros)
        df = df.sort_values("anio").reset_index(drop=True)

        # El Banco Mundial a veces ignora el rango de fechas y devuelve
        # todos los datos disponibles. Filtramos para respetar el rango pedido.
        df = df[(df["anio"] >= periodo_inicio) & (df["anio"] <= periodo_fin)]
        df = df.reset_index(drop=True)

        if df.empty:
            raise ValueError(
                f"No hay datos disponibles para el indicador {indicador} "
                f"en {pais} entre {periodo_inicio} y {periodo_fin}."
            )

        # --- Metadatos ---
        info_indicador = INDICADORES.get(indicador, {})
        metadatos = Metadatos(
            fuente=self.nombre,
            indicador=info_indicador.get("nombre", indicador),
            codigo_indicador=indicador,
            unidad=info_indicador.get("unidad", ""),
            pais=PAISES.get(pais, pais),
            periodo_inicio=periodo_inicio,
            periodo_fin=periodo_fin,
            url_fuente=url,
            notas="Datos descargados de la API pública del Banco Mundial.",
        )

        return df, metadatos