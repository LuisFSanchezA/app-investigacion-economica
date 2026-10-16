"""Esquema de metadatos para las fuentes de datos.

Toda consulta a una fuente externa debe devolver, además de los datos,
un conjunto de metadatos que permitan rastrear su origen, unidad de medida
y vigencia. Esto es indispensable para la reproducibilidad de una
investigación económica.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Metadatos:
    """Metadatos asociados a una consulta a una fuente de datos."""

    fuente: str
    indicador: str
    codigo_indicador: str
    unidad: str
    pais: str
    periodo_inicio: int
    periodo_fin: int
    fecha_consulta: datetime = field(default_factory=datetime.now)
    url_fuente: str = ""
    notas: str = ""

    def como_dict(self) -> dict:
        """Devuelve los metadatos como diccionario (útil para Streamlit)."""
        return {
            "fuente": self.fuente,
            "indicador": self.indicador,
            "codigo_indicador": self.codigo_indicador,
            "unidad": self.unidad,
            "pais": self.pais,
            "periodo_inicio": self.periodo_inicio,
            "periodo_fin": self.periodo_fin,
            "fecha_consulta": self.fecha_consulta.strftime("%Y-%m-%d %H:%M"),
            "url_fuente": self.url_fuente,
            "notas": self.notas,
        }