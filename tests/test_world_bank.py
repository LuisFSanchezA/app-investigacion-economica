"""Pruebas automatizadas para el conector del Banco Mundial.

Usa mock para simular respuestas de la API y no depender de internet.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from src.fuentes.world_bank import BancoMundial


# Respuesta JSON válida simulada (2 años)
RESPUESTA_VALIDA = [
    {"page": 1, "pages": 1, "per_page": 1000, "total": 2},
    [
        {
            "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
            "country": {"id": "MX", "value": "Mexico"},
            "countryiso3code": "MEX",
            "date": "2020",
            "value": 1121064767168.8,
        },
        {
            "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
            "country": {"id": "MX", "value": "Mexico"},
            "countryiso3code": "MEX",
            "date": "2021",
            "value": 1316569466833.94,
        },
    ],
]


def _mock_response(json_data, status_code=200):
    """Crea un objeto respuesta simulado."""
    class MockResponse:
        def __init__(self, json_data, status_code):
            self._json = json_data
            self.status_code = status_code

        def json(self):
            return self._json

    return MockResponse(json_data, status_code)


# ----------------------------------------------------------------
# Test 1: Conversión de respuesta JSON válida
# ----------------------------------------------------------------
@patch("src.fuentes.world_bank.requests.get")
def test_conversion_json_valido(mock_get):
    """Una respuesta JSON válida se convierte en DataFrame correctamente."""
    mock_get.return_value = _mock_response(RESPUESTA_VALIDA, 200)

    bm = BancoMundial()
    df, meta = bm.consultar("NY.GDP.MKTP.CD", "MEX", 2020, 2021)

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 6)
    assert list(df["anio"]) == [2020, 2021]
    assert df["valor"].iloc[0] == pytest.approx(1121064767168.8)
    assert df["pais_codigo"].iloc[0] == "MEX"
    assert df["indicador_codigo"].iloc[0] == "NY.GDP.MKTP.CD"


# ----------------------------------------------------------------
# Test 2: Respuesta vacía
# ----------------------------------------------------------------
@patch("src.fuentes.world_bank.requests.get")
def test_respuesta_vacia(mock_get):
    """Una respuesta sin observaciones lanza ValueError."""
    mock_get.return_value = _mock_response(
        [{"page": 1, "pages": 1, "total": 0}, []], 200
    )

    bm = BancoMundial()
    with pytest.raises(ValueError, match="no tiene el formato esperado|No hay datos"):
        bm.consultar("NY.GDP.MKTP.CD", "MEX", 2020, 2024)


# ----------------------------------------------------------------
# Test 3: Respuesta con formato inesperado
# ----------------------------------------------------------------
@patch("src.fuentes.world_bank.requests.get")
def test_respuesta_mal_formada(mock_get):
    """Una respuesta que no es lista de 2 elementos lanza ValueError."""
    mock_get.return_value = _mock_response(
        {"message": [{"id": "120", "value": "Invalid value"}]}, 200
    )

    bm = BancoMundial()
    with pytest.raises(ValueError, match="no son válidos"):
        bm.consultar("NY.GDP.MKTP.CD", "XXX", 2020, 2024)


# ----------------------------------------------------------------
# Test 4: Error HTTP
# ----------------------------------------------------------------
@patch("src.fuentes.world_bank.requests.get")
def test_error_http(mock_get):
    """Un status code distinto de 200 lanza ConnectionError."""
    mock_get.return_value = _mock_response({}, 500)

    bm = BancoMundial()
    with pytest.raises(ConnectionError, match="código 500"):
        bm.consultar("NY.GDP.MKTP.CD", "MEX", 2020, 2024)


# ----------------------------------------------------------------
# Test 5: Error de conexión
# ----------------------------------------------------------------
@patch("src.fuentes.world_bank.requests.get")
def test_error_de_conexion(mock_get):
    """Un ConnectionError de requests se propaga como ConnectionError."""
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError()

    bm = BancoMundial()
    with pytest.raises(ConnectionError, match="No se pudo conectar"):
        bm.consultar("NY.GDP.MKTP.CD", "MEX", 2020, 2024)


# ----------------------------------------------------------------
# Test 6: Timeout
# ----------------------------------------------------------------
@patch("src.fuentes.world_bank.requests.get")
def test_timeout(mock_get):
    """Un Timeout de requests se propaga como ConnectionError."""
    import requests
    mock_get.side_effect = requests.exceptions.Timeout()

    bm = BancoMundial()
    with pytest.raises(ConnectionError, match="excedió el tiempo"):
        bm.consultar("NY.GDP.MKTP.CD", "MEX", 2020, 2024)


# ----------------------------------------------------------------
# Test 7: Metadatos correctos
# ----------------------------------------------------------------
@patch("src.fuentes.world_bank.requests.get")
def test_metadatos_se_conservan(mock_get):
    """Los metadatos devueltos tienen todos los campos esperados."""
    mock_get.return_value = _mock_response(RESPUESTA_VALIDA, 200)

    bm = BancoMundial()
    df, meta = bm.consultar("NY.GDP.MKTP.CD", "MEX", 2020, 2021)

    assert meta.fuente == "Banco Mundial"
    assert meta.codigo_indicador == "NY.GDP.MKTP.CD"
    assert meta.pais == "México"
    assert meta.periodo_inicio == 2020
    assert meta.periodo_fin == 2021
    assert "worldbank.org" in meta.url_fuente
    assert meta.fecha_consulta is not None