"""Pruebas automatizadas para el conector de Banxico.

Usa mock para simular respuestas de la API y no depender del token real.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.fuentes import banxico


# Respuesta JSON válida simulada (3 días)
RESPUESTA_VALIDA = {
    "bmx": {
        "series": [
            {
                "idSerie": "SF43718",
                "titulo": "Tipo de cambio FIX",
                "datos": [
                    {"fecha": "02/01/2024", "dato": "17.0297"},
                    {"fecha": "03/01/2024", "dato": "17.0492"},
                    {"fecha": "04/01/2024", "dato": "17.0458"},
                ],
            }
        ]
    }
}


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
# Fixture: mock de st.secrets
# ----------------------------------------------------------------
@pytest.fixture(autouse=True)
def mock_secrets(monkeypatch):
    """Simula st.secrets con un token falso."""
    import streamlit as st
    monkeypatch.setattr(st, "secrets", {"BANXICO_TOKEN": "fake-token"}, raising=False)


# ----------------------------------------------------------------
# Test 1: Conversión de respuesta JSON válida
# ----------------------------------------------------------------
@patch("src.fuentes.banxico.requests.get")
def test_conversion_json_valido(mock_get):
    """Una respuesta válida se convierte en DataFrame con fechas y valores."""
    mock_get.return_value = _mock_response(RESPUESTA_VALIDA, 200)

    b = banxico.Banxico()
    df, meta = b.consultar("SF43718", "MEX", 2024, 2024)

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (3, 2)
    assert list(df.columns) == ["fecha", "valor"]
    assert df["fecha"].iloc[0] == pd.Timestamp("2024-01-02")
    assert df["valor"].iloc[0] == pytest.approx(17.0297)


# ----------------------------------------------------------------
# Test 2: Respuesta con valores N/E
# ----------------------------------------------------------------
@patch("src.fuentes.banxico.requests.get")
def test_valores_no_disponibles(mock_get):
    """Los valores 'N/E' se convierten en None."""
    respuesta = {
        "bmx": {
            "series": [
                {
                    "idSerie": "SF43718",
                    "titulo": "Test",
                    "datos": [
                        {"fecha": "02/01/2024", "dato": "17.0297"},
                        {"fecha": "03/01/2024", "dato": "N/E"},
                    ],
                }
            ]
        }
    }
    mock_get.return_value = _mock_response(respuesta, 200)

    b = banxico.Banxico()
    df, meta = b.consultar("SF43718", "MEX", 2024, 2024)

    assert df["valor"].iloc[0] == pytest.approx(17.0297)
    assert pd.isna(df["valor"].iloc[1])


# ----------------------------------------------------------------
# Test 3: Token inválido (401)
# ----------------------------------------------------------------
@patch("src.fuentes.banxico.requests.get")
def test_token_invalido(mock_get):
    """Un 401 lanza ConnectionError con mensaje sobre el token."""
    mock_get.return_value = _mock_response({}, 401)

    b = banxico.Banxico()
    with pytest.raises(ConnectionError, match="token"):
        b.consultar("SF43718", "MEX", 2024, 2024)


# ----------------------------------------------------------------
# Test 4: Error HTTP general
# ----------------------------------------------------------------
@patch("src.fuentes.banxico.requests.get")
def test_error_http(mock_get):
    """Un status distinto de 200 lanza ConnectionError."""
    mock_get.return_value = _mock_response({}, 500)

    b = banxico.Banxico()
    with pytest.raises(ConnectionError, match="código 500"):
        b.consultar("SF43718", "MEX", 2024, 2024)


# ----------------------------------------------------------------
# Test 5: Error de conexión
# ----------------------------------------------------------------
@patch("src.fuentes.banxico.requests.get")
def test_error_de_conexion(mock_get):
    """Un ConnectionError de requests se propaga."""
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError()

    b = banxico.Banxico()
    with pytest.raises(ConnectionError, match="No se pudo conectar"):
        b.consultar("SF43718", "MEX", 2024, 2024)


# ----------------------------------------------------------------
# Test 6: Timeout
# ----------------------------------------------------------------
@patch("src.fuentes.banxico.requests.get")
def test_timeout(mock_get):
    """Un Timeout se propaga como ConnectionError."""
    import requests
    mock_get.side_effect = requests.exceptions.Timeout()

    b = banxico.Banxico()
    with pytest.raises(ConnectionError, match="tiempo de espera"):
        b.consultar("SF43718", "MEX", 2024, 2024)


# ----------------------------------------------------------------
# Test 7: Respuesta con formato inesperado
# ----------------------------------------------------------------
@patch("src.fuentes.banxico.requests.get")
def test_respuesta_mal_formada(mock_get):
    """Una respuesta sin 'bmx' lanza ValueError."""
    mock_get.return_value = _mock_response({"mensaje": "algo"}, 200)

    b = banxico.Banxico()
    with pytest.raises(ValueError, match="formato esperado"):
        b.consultar("SF43718", "MEX", 2024, 2024)


# ----------------------------------------------------------------
# Test 8: Respuesta vacía
# ----------------------------------------------------------------
@patch("src.fuentes.banxico.requests.get")
def test_respuesta_vacia(mock_get):
    """Una respuesta sin datos lanza ValueError."""
    respuesta = {
        "bmx": {"series": [{"idSerie": "SF43718", "titulo": "Test", "datos": []}]}
    }
    mock_get.return_value = _mock_response(respuesta, 200)

    b = banxico.Banxico()
    with pytest.raises(ValueError, match="No hay datos"):
        b.consultar("SF43718", "MEX", 2024, 2024)


# ----------------------------------------------------------------
# Test 9: Metadatos correctos
# ----------------------------------------------------------------
@patch("src.fuentes.banxico.requests.get")
def test_metadatos_se_conservan(mock_get):
    """Los metadatos tienen todos los campos esperados."""
    mock_get.return_value = _mock_response(RESPUESTA_VALIDA, 200)

    b = banxico.Banxico()
    df, meta = b.consultar("SF43718", "MEX", 2024, 2024)

    assert meta.fuente == "Banco de México"
    assert meta.codigo_indicador == "SF43718"
    assert meta.unidad == "MXN por USD"
    assert meta.pais == "México"
    assert meta.periodo_inicio == 2024
    assert meta.periodo_fin == 2024
    assert "banxico.org.mx" in meta.url_fuente


# ----------------------------------------------------------------
# Test 10: Sin token configurado
# ----------------------------------------------------------------
def test_sin_token(monkeypatch):
    """Si no hay BANXICO_TOKEN, lanza ValueError."""
    import streamlit as st
    monkeypatch.setattr(st, "secrets", {}, raising=False)

    b = banxico.Banxico()
    with pytest.raises(ValueError, match="BANXICO_TOKEN"):
        b.consultar("SF43718", "MEX", 2024, 2024)