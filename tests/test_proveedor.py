"""Pruebas de la capa de proveedor (factory + fallback)."""

from unittest.mock import MagicMock, patch

import pytest

from src.ai.proveedor import construir_cadena, generar_con_fallback
from src.ai.proveedores.base import (
    ErrorCredenciales,
    ErrorCuota,
    ErrorProveedorIA,
    ErrorSaturado,
    ProveedorIA,
)


class _ProveedorFake(ProveedorIA):
    """Proveedor falso para pruebas: responde o falla según config."""

    nombre = "fake"

    def __init__(self, respuestas: list):
        # respuestas: lista de textos o excepciones, se consumen en orden.
        self.respuestas = list(respuestas)
        self.llamadas = 0

    def disponible(self) -> bool:
        return True

    def generar(self, prompt: str, max_tokens: int = 1024) -> str:
        self.llamadas += 1
        if not self.respuestas:
            raise ErrorProveedorIA("sin respuestas configuradas")
        r = self.respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


# ---------------------------------------------------------------------------
# construir_cadena
# ---------------------------------------------------------------------------

class TestConstruirCadena:
    @patch("src.ai.proveedor._leer_orden", return_value=["groq", "gemini"])
    @patch("src.ai.proveedor._REGISTRO")
    def test_solo_disponibles(self, mock_registro, mock_orden):
        p_groq = MagicMock(spec=ProveedorIA)
        p_groq.disponible.return_value = True
        p_gemini = MagicMock(spec=ProveedorIA)
        p_gemini.disponible.return_value = False

        mock_registro.get.side_effect = lambda n: {
            "groq": lambda: p_groq,
            "gemini": lambda: p_gemini,
        }.get(n)

        cadena = construir_cadena()
        assert len(cadena) == 1
        assert cadena[0] is p_groq

    @patch("src.ai.proveedor._leer_orden", return_value=["desconocido"])
    def test_nombre_desconocido_ignorado(self, mock_orden):
        assert construir_cadena() == []


# ---------------------------------------------------------------------------
# generar_con_fallback
# ---------------------------------------------------------------------------

class TestGenerarConFallback:
    @patch("src.ai.proveedor.construir_cadena")
    def test_primero_responde(self, mock_construir):
        p = _ProveedorFake(["hola"])
        mock_construir.return_value = [p]
        assert generar_con_fallback("prompt") == "hola"
        assert p.llamadas == 1

    @patch("src.ai.proveedor.construir_cadena")
    def test_fallback_por_saturacion(self, mock_construir):
        p1 = _ProveedorFake([ErrorSaturado("503"), ErrorSaturado("503")])
        p2 = _ProveedorFake(["respuesta de p2"])
        mock_construir.return_value = [p1, p2]

        with patch("time.sleep"):  # no esperar de verdad
            resultado = generar_con_fallback(
                "prompt", max_reintentos_por_proveedor=2
            )
        assert resultado == "respuesta de p2"
        assert p1.llamadas == 2  # agotó reintentos
        assert p2.llamadas == 1

    @patch("src.ai.proveedor.construir_cadena")
    def test_fallback_por_cuota(self, mock_construir):
        p1 = _ProveedorFake([ErrorCuota("429")])
        p2 = _ProveedorFake(["respuesta de p2"])
        mock_construir.return_value = [p1, p2]

        resultado = generar_con_fallback("prompt")
        assert resultado == "respuesta de p2"
        assert p1.llamadas == 1  # no reintenta cuota

    @patch("src.ai.proveedor.construir_cadena")
    def test_fallback_por_credenciales(self, mock_construir):
        p1 = _ProveedorFake([ErrorCredenciales("401")])
        p2 = _ProveedorFake(["respuesta de p2"])
        mock_construir.return_value = [p1, p2]

        resultado = generar_con_fallback("prompt")
        assert resultado == "respuesta de p2"

    @patch("src.ai.proveedor.construir_cadena")
    def test_todos_fallan(self, mock_construir):
        p1 = _ProveedorFake([ErrorCredenciales("401")])
        p2 = _ProveedorFake([ErrorCredenciales("401")])
        mock_construir.return_value = [p1, p2]

        with pytest.raises(ErrorProveedorIA, match="Todos los proveedores"):
            generar_con_fallback("prompt")

    @patch("src.ai.proveedor.construir_cadena")
    def test_sin_proveedores(self, mock_construir):
        mock_construir.return_value = []
        with pytest.raises(ErrorProveedorIA, match="No hay proveedor"):
            generar_con_fallback("prompt")

    @patch("src.ai.proveedor.construir_cadena")
    def test_reintenta_saturacion_y_luego_exito(self, mock_construir):
        p = _ProveedorFake([ErrorSaturado("503"), "ok al segundo intento"])
        mock_construir.return_value = [p]

        with patch("time.sleep"):
            resultado = generar_con_fallback(
                "prompt", max_reintentos_por_proveedor=2
            )
        assert resultado == "ok al segundo intento"
        assert p.llamadas == 2 