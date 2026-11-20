"""Pruebas del conector de INEGI."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.fuentes.inegi import INDICADORES_INEGI, INEGI


def _respuesta_inegi(observaciones: list[dict]) -> dict:
    return {
        "Series": [
            {
                "OBSERVACIONES": observaciones,
            }
        ]
    }


@pytest.fixture
def obs_ejemplo():
    return [
        {"TIME_PERIOD": "2020/01", "OBS_VALUE": "1000.5"},
        {"TIME_PERIOD": "2021/01", "OBS_VALUE": "1100.0"},
        {"TIME_PERIOD": "2022/01", "OBS_VALUE": "1200.3"},
    ]


class TestToken:
    @patch("src.fuentes.inegi.os.environ.get")
    @patch("src.fuentes.inegi._get_token")
    def test_sin_token_falla(self, mock_get_token, mock_env):
        mock_get_token.side_effect = ValueError("No se encontró INEGI_TOKEN")
        conector = INEGI()
        with pytest.raises(ValueError, match="INEGI_TOKEN"):
            conector.consultar(indicador="1002000001")


class TestConsultar:
    @patch("src.fuentes.inegi._get_token", return_value="fake_token")
    @patch("src.fuentes.inegi.requests.get")
    def test_exitoso(self, mock_get, mock_token, obs_ejemplo):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _respuesta_inegi(obs_ejemplo)
        mock_get.return_value = mock_resp

        conector = INEGI()
        df, meta = conector.consultar(indicador="1002000001")

        assert len(df) == 3
        assert list(df["anio"]) == [2020, 2021, 2022]
        assert list(df["valor"]) == [1000.5, 1100.0, 1200.3]
        assert meta.fuente == "INEGI"

    @patch("src.fuentes.inegi._get_token", return_value="fake_token")
    @patch("src.fuentes.inegi.requests.get")
    def test_filtra_por_anio(self, mock_get, mock_token, obs_ejemplo):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _respuesta_inegi(obs_ejemplo)
        mock_get.return_value = mock_resp

        conector = INEGI()
        df, _ = conector.consultar(
            indicador="1002000001",
            periodo_inicio=2021,
            periodo_fin=2022,
        )
        assert len(df) == 2
        assert list(df["anio"]) == [2021, 2022]

    @patch("src.fuentes.inegi._get_token", return_value="fake_token")
    @patch("src.fuentes.inegi.requests.get")
    def test_valores_no_disponibles(self, mock_get, mock_token):
        obs = [
            {"TIME_PERIOD": "2020/01", "OBS_VALUE": "N/E"},
            {"TIME_PERIOD": "2021/01", "OBS_VALUE": "100.0"},
        ]
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _respuesta_inegi(obs)
        mock_get.return_value = mock_resp

        conector = INEGI()
        df, _ = conector.consultar(indicador="1002000001")
        # pandas convierte None a NaN en columnas numéricas
        assert pd.isna(df.iloc[0]["valor"])
        assert df.iloc[1]["valor"] == 100.0

    @patch("src.fuentes.inegi._get_token", return_value="fake_token")
    @patch("src.fuentes.inegi.requests.get")
    def test_token_invalido(self, mock_get, mock_token):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        conector = INEGI()
        with pytest.raises(ConnectionError, match="token"):
            conector.consultar(indicador="1002000001")

    @patch("src.fuentes.inegi._get_token", return_value="fake_token")
    @patch("src.fuentes.inegi.requests.get")
    def test_error_http(self, mock_get, mock_token):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        conector = INEGI()
        with pytest.raises(ConnectionError):
            conector.consultar(indicador="1002000001")

    @patch("src.fuentes.inegi._get_token", return_value="fake_token")
    @patch("src.fuentes.inegi.requests.get")
    def test_respuesta_mal_formada(self, mock_get, mock_token):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"otra_cosa": []}
        mock_get.return_value = mock_resp

        conector = INEGI()
        with pytest.raises(ValueError, match="formato"):
            conector.consultar(indicador="1002000001")

    @patch("src.fuentes.inegi._get_token", return_value="fake_token")
    @patch("src.fuentes.inegi.requests.get")
    def test_sin_observaciones(self, mock_get, mock_token):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = _respuesta_inegi([])
        mock_get.return_value = mock_resp

        conector = INEGI()
        with pytest.raises(ValueError):
            conector.consultar(indicador="1002000001")

    def test_indicador_inexistente(self):
        conector = INEGI()
        with pytest.raises(ValueError, match="catálogo"):
            conector.consultar(indicador="9999999999")


class TestCatalogo:
    def test_catalogo_definido(self):
        assert "1002000001" in INDICADORES_INEGI
        assert len(INDICADORES_INEGI) >= 3

    def test_campos_requeridos(self):
        for codigo, info in INDICADORES_INEGI.items():
            assert "nombre" in info
            assert "unidad" in info
            assert "area" in info