"""Test E2E mínimo: flujo Pregunta → Literatura → Datos → Tema (sin UI).

No ejercita Streamlit; verifica que las funciones clave del flujo existen
y son invocables con insumos mínimos. Sirve como smoke test para el deploy.
"""

import inspect

import pytest

from src.fuentes.base import FuenteBase


def test_flujo_completo_importable():
    """Los módulos clave del flujo se importan sin error."""
    from src.fuentes import world_bank, inegi, openalex  # noqa: F401
    from src.ai import (  # noqa: F401
        generar_justificacion_cached,
        generar_resumen_ejecutivo_cached,
        sugerir_enunciado_cached,
    )
    from app import seccion_tema  # noqa: F401


def test_seccion_tema_render_callable():
    """La sección Tema expone un callable render()."""
    from app.seccion_tema import render

    assert callable(render)


@pytest.mark.parametrize(
    "modulo,clase",
    [
        ("world_bank", "BancoMundial"),
        ("inegi", "INEGI"),
        ("openalex", "OpenAlex"),
    ],
)
def test_conector_es_subclase_de_fuentebase(modulo, clase):
    """Cada conector expone una clase que hereda de FuenteBase."""
    import importlib

    m = importlib.import_module(f"src.fuentes.{modulo}")
    assert hasattr(m, clase), f"{modulo} no expone la clase {clase}"

    cls = getattr(m, clase)
    assert inspect.isclass(cls), f"{modulo}.{clase} no es una clase"
    assert issubclass(cls, FuenteBase), (
        f"{modulo}.{clase} no hereda de FuenteBase"
    )