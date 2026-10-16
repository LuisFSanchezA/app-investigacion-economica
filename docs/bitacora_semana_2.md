---

# Semana 2 — Integración de fuentes reales

## Lunes 19 de octubre de 2026
- Se creó el módulo `src/fuentes/` para separar la lógica de descarga de datos de la interfaz.
- Se creó `src/fuentes/__init__.py` (vacío, para que sea paquete importable).
- Se creó `src/fuentes/metadatos.py` con la clase `Metadatos` (dataclass).
  - Campos: fuente, indicador, codigo_indicador, unidad, pais, periodo_inicio, periodo_fin, fecha_consulta, url_fuente, notas.
  - Método `como_dict()` para exportar a Streamlit.
- Se creó `src/fuentes/base.py` con la clase abstracta `FuenteBase`.
  - Define la interfaz común para todas las fuentes: `nombre` y `consultar()`.
  - El método `consultar()` devuelve tupla `(DataFrame, Metadatos)`.
- Se verificó que la clase `Metadatos` funciona correctamente con un ejemplo del Banco Mundial.
- Commit registrado: "Lunes 19: módulo de fuentes con esquema de metadatos y clase base".

## Pendientes para el martes 20
- Construir el conector `src/fuentes/world_bank.py`.
- Consultar el PIB de México (indicador `NY.GDP.MKTP.CD`) mediante la API pública del Banco Mundial.
- Convertir la respuesta JSON en un DataFrame de pandas.
- Manejar errores HTTP, respuestas vacías y problemas de conexión.