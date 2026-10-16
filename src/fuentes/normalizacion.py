"""Funciones de normalización para datos descargados de fuentes externas.

El objetivo es estandarizar nombres de columnas, tipos de datos y
detectar problemas de calidad antes de que los datos lleguen a la
interfaz o al análisis.
"""

import pandas as pd

from src.fuentes.metadatos import Metadatos


COLUMNAS_ESTANDAR = ["anio", "valor"]


def normalizar_serie(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza un DataFrame de serie temporal.

    - Renombra columnas al esquema estándar.
    - Convierte `anio` a entero y `valor` a float.
    - Ordena por año.
    - Reinicia el índice.
    """
    if df.empty:
        raise ValueError("El DataFrame está vacío; no se puede normalizar.")

    df = df.copy()

    renombres = {
        "date": "anio",
        "year": "anio",
        "value": "valor",
        "gdp": "valor",
    }
    df = df.rename(columns=renombres)

    if "anio" not in df.columns or "valor" not in df.columns:
        raise ValueError(
            f"El DataFrame no tiene las columnas mínimas esperadas "
            f"({COLUMNAS_ESTANDAR}). Columnas actuales: {list(df.columns)}"
        )

    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")

    if df["anio"].isna().any():
        raise ValueError("Hay valores no numéricos en la columna 'anio'.")

    df = df.sort_values("anio").reset_index(drop=True)

    return df


def detectar_duplicados(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve las filas duplicadas por año, si las hay."""
    if "anio" not in df.columns:
        raise ValueError("El DataFrame no tiene la columna 'anio'.")
    return df[df.duplicated(subset=["anio"], keep=False)]


def detectar_faltantes(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve un resumen de valores faltantes por columna."""
    return df.isna().sum().to_frame(name="faltantes")


def resumen_calidad(df: pd.DataFrame, metadatos: Metadatos) -> dict:
    """Genera un resumen de calidad del DataFrame normalizado."""
    duplicados = detectar_duplicados(df)
    faltantes = detectar_faltantes(df)

    return {
        "fuente": metadatos.fuente,
        "indicador": metadatos.indicador,
        "unidad": metadatos.unidad,
        "observaciones": len(df),
        "anio_min": int(df["anio"].min()) if not df.empty else None,
        "anio_max": int(df["anio"].max()) if not df.empty else None,
        "duplicados": len(duplicados),
        "faltantes": faltantes.to_dict()["faltantes"],
    }