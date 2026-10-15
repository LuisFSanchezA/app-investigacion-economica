"""Funciones de validación para conjuntos de datos económicos."""

import pandas as pd


def validate_dataframe(df, required_columns):
    """Valida la estructura básica de un conjunto de datos.

    Parámetros
    ----------
    df : pd.DataFrame
        El DataFrame a validar.
    required_columns : list[str]
        Lista de columnas que deben estar presentes.

    Devuelve
    -------
    bool
        True si la validación pasa.

    Levanta
    -------
    ValueError
        Si el DataFrame está vacío o si faltan columnas obligatorias.
    """
    if df.empty:
        raise ValueError("El conjunto de datos está vacío.")

    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(f"Faltan columnas obligatorias: {missing}")

    return True