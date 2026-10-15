"""Pruebas automatizadas para la validación de datos económicos."""

import pandas as pd
import pytest

from src.data_validation import validate_dataframe


# ----------------------------------------------------------------
# Test 1: Lectura correcta del archivo
# ----------------------------------------------------------------
def test_lectura_correcta_del_csv():
    """Un CSV válido se lee y devuelve un DataFrame con las filas y columnas esperadas."""
    df = pd.read_csv("data/raw/pib_empleo_demo.csv")

    assert df.shape[0] == 5
    assert df.shape[1] == 4
    assert list(df.columns) == [
        "entidad",
        "anio",
        "pib_millones",
        "empleo_miles",
    ]


# ----------------------------------------------------------------
# Test 2: Detección de columnas faltantes
# ----------------------------------------------------------------
def test_faltan_columnas_obligatorias():
    """Si falta una columna obligatoria, se informa cuál falta."""
    df = pd.DataFrame(
        {
            "entidad": ["México"],
            "pib_millones": [100],
            "empleo_miles": [50],
        }
    )

    with pytest.raises(ValueError, match="Faltan columnas"):
        validate_dataframe(
            df, ["entidad", "anio", "pib_millones", "empleo_miles"]
        )


# ----------------------------------------------------------------
# Test 3: Detección de valores faltantes
# ----------------------------------------------------------------
def test_deteccion_de_valores_faltantes():
    """Un DataFrame con valores faltantes se detecta sin eliminarlos ni imputarlos."""
    df = pd.DataFrame(
        {
            "entidad": ["México", "México"],
            "anio": [2020, 2021],
            "pib_millones": [100, None],  # valor faltante
            "empleo_miles": [50, 55],
        }
    )

    # La validación estructural pasa...
    assert validate_dataframe(
        df, ["entidad", "anio", "pib_millones", "empleo_miles"]
    ) is True

    # ...pero los valores faltantes siguen ahí, no se eliminan ni imputan.
    assert df["pib_millones"].isna().sum() == 1
    assert df.shape[0] == 2


# ----------------------------------------------------------------
# Test 4: Validación de tipos de datos
# ----------------------------------------------------------------
def test_validacion_de_tipos_de_datos():
    """Un año con formato incorrecto (texto) se detecta como tipo no válido."""
    df = pd.DataFrame(
        {
            "entidad": ["México", "México"],
            "anio": ["dos mil veinte", "2021"],  # tipo incorrecto
            "pib_millones": [100, 110],
            "empleo_miles": [50, 55],
        }
    )

    # La validación estructural pasa (las columnas existen)...
    assert validate_dataframe(
        df, ["entidad", "anio", "pib_millones", "empleo_miles"]
    ) is True

    # ...pero el tipo de dato es incorrecto (debería ser numérico).
    assert not pd.api.types.is_numeric_dtype(df["anio"])


# ----------------------------------------------------------------
# Test 5: Archivo vacío o inexistente
# ----------------------------------------------------------------
def test_dataframe_vacio():
    """Un DataFrame vacío levanta un ValueError con mensaje claro."""
    df = pd.DataFrame(columns=["entidad", "anio", "pib_millones", "empleo_miles"])

    with pytest.raises(ValueError, match="vacío"):
        validate_dataframe(
            df, ["entidad", "anio", "pib_millones", "empleo_miles"]
        )


def test_archivo_inexistente():
    """Leer un archivo que no existe levanta FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        pd.read_csv("data/raw/archivo_que_no_existe.csv")