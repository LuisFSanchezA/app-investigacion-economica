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


## Martes 20 de octubre de 2026
- Se creó `src/fuentes/world_bank.py` con la clase `BancoMundial` que implementa `FuenteBase`.
- Catálogo de indicadores (`INDICADORES`):
  - `NY.GDP.MKTP.CD` — PIB (USD corrientes)
  - `NY.GDP.PCAP.CD` — PIB per cápita
  - `SP.POP.TOTL` — Población total
  - `SL.UEM.TOTL.ZS` — Tasa de desempleo
- Catálogo de países (`PAISES`): MEX, USA, BRA, ARG, CHL, COL.
- El método `consultar()`:
  - Construye URL de la API pública del Banco Mundial.
  - Timeout de 60 segundos (la API puede tardar).
  - Maneja errores de conexión (Timeout, ConnectionError).
  - Maneja errores HTTP (status != 200).
  - Maneja respuestas mal formadas o vacías.
  - **Filtra el DataFrame por el rango de años pedido** (el Banco Mundial a veces ignora el parámetro `date`).
  - Si después del filtro no quedan datos, lanza `ValueError` claro.
  - Devuelve tupla `(DataFrame, Metadatos)`.
- Se actualizó `src/fuentes/__init__.py` para exponer `BancoMundial`, `INDICADORES`, `PAISES`, `Metadatos`, `FuenteBase`.
- Se probaron 5 casos:
  - ✅ Consulta exitosa: PIB México 2000–2024 (25 filas).
  - ✅ País inexistente ('XXX'): ValueError con mensaje claro.
  - ✅ Indicador inexistente: ValueError con mensaje claro.
  - ✅ Rango sin datos (1900–1905): ValueError con mensaje claro.
  - ✅ Rango parcial (1950–1970): devuelve 1960–1970 (11 filas).
- Aprendizaje: el Banco Mundial ignora rangos inválidos y devuelve todos los datos. Es necesario filtrar del lado del cliente.

## Pendientes para el miércoles 21
- Normalizar nombres de columnas y tipos de datos.
- Verificar que años y valores numéricos sean válidos.
- Detectar observaciones duplicadas y valores faltantes.
- Conservar la unidad original y documentar transformaciones.

## Miércoles 21 de octubre de 2026
- Se creó `src/fuentes/normalizacion.py` con 4 funciones:
  1. `normalizar_serie(df)`: renombra columnas al esquema estándar (anio, valor), convierte tipos, ordena por año y reinicia el índice.
  2. `detectar_duplicados(df)`: devuelve filas duplicadas por año.
  3. `detectar_faltantes(df)`: devuelve resumen de valores faltantes por columna.
  4. `resumen_calidad(df, metadatos)`: devuelve dict con fuente, indicador, unidad, observaciones, rango de años, duplicados y faltantes.
- Se actualizó `src/fuentes/__init__.py` para exponer las nuevas funciones.
- Se probó:
  - ✅ Normalización de serie del Banco Mundial: tipos correctos (Int64, float64).
  - ✅ Resumen de calidad: 25 obs, 2000–2024, 0 duplicados, 0 faltantes.
  - ✅ Detección de duplicados con datos sintéticos: encontró 2 filas duplicadas.
  - ✅ Detección de faltantes con datos sintéticos: encontró 1 faltante en 'valor'.
  - ✅ Normalización con nombres raros (date, value): renombró correctamente.
- Las transformaciones preservan la unidad original en los metadatos.

## Pendientes para el jueves 22
- Agregar sección "Fuentes de datos" a la app.
- Permitir elegir país e indicador.
- Mostrar tabla y fuente consultada.
- Mensaje de error comprensible si la consulta falla.

## Jueves 22 de octubre de 2026
- Se agregó la sección "Fuentes de datos" al menú lateral de la app.
- Controles de consulta:
  - Selector de país (6 opciones).
  - Selector de indicador (4 opciones).
  - Inputs de año inicial y final (min 1960, max 2024).
  - Botón "Consultar".
- Al consultar:
  - Se llama a `BancoMundial.consultar()`.
  - Se normaliza la serie con `normalizar_serie()`.
  - Se calcula el resumen de calidad con `resumen_calidad()`.
  - Se guarda todo en `st.session_state` para persistir entre interacciones.
- Visualización de resultados:
  - Mensaje de éxito con número de observaciones.
  - Metadatos en formato JSON.
  - Resumen de calidad con 3 métricas (observaciones, duplicados, faltantes).
  - Tabla completa del DataFrame.
- Manejo de errores:
  - Se capturan `ValueError` y `ConnectionError`.
  - Se muestra mensaje rojo con el error.
  - La app no se cae.
- Validación preventiva: los inputs de año tienen min=1960 y max=2024, lo que evita consultas fuera de rango.

## Pendientes para el viernes 23
- Crear gráfica temporal de la serie consultada.
- Mostrar el periodo y la unidad de medida.
- Permitir descargar los resultados en CSV.
- Comprobar que la descarga conserve nombres y valores.

## Viernes 23 de octubre de 2026
- Se agregó la gráfica temporal de la serie consultada con Plotly.
- Se agregó un bloque de "Contexto de la serie" con:
  - Periodo (año min – año max).
  - Unidad de medida.
  - Nombre del indicador.
- Se agregó botón de descarga CSV.
  - El nombre del archivo incluye: código del indicador, país, periodo.
  - Ejemplo: `NY.GDP.MKTP.CD_México_2000_2024.csv`.
- Se comprobó que la descarga conserva:
  - Nombres de columnas: anio, valor, pais_codigo, pais_nombre, indicador_codigo, indicador_nombre.
  - Valores correctos.
- Se probó con dos combinaciones:
  - México — PIB (USD corrientes) — 2000–2024.
  - Brasil — Población total — 2000–2024.

## Pendientes para el sábado 24
- Escribir pruebas automatizadas con pytest para el conector del Banco Mundial.
- Probar conversión de respuesta JSON válida.
- Probar respuesta vacía o con campos faltantes.
- Simular error de conexión o respuesta HTTP fallida.
- Comprobar que los metadatos se conserven.


## Sábado 24 de octubre de 2026
- Se creó `tests/test_world_bank.py` con 7 pruebas usando `unittest.mock`.
- Las pruebas simulan respuestas de la API sin hacer llamadas reales (rápidas y deterministas).
- Pruebas implementadas:
  1. `test_conversion_json_valido`: una respuesta JSON válida se convierte en DataFrame con las columnas correctas.
  2. `test_respuesta_vacia`: una respuesta sin observaciones lanza ValueError.
  3. `test_respuesta_mal_formada`: una respuesta con formato inesperado lanza ValueError.
  4. `test_error_http`: status code distinto de 200 lanza ConnectionError.
  5. `test_error_de_conexion`: ConnectionError de requests se propaga como ConnectionError.
  6. `test_timeout`: Timeout de requests se propaga como ConnectionError.
  7. `test_metadatos_se_conservan`: los metadatos devueltos tienen todos los campos esperados.
- Resultado: 7 pruebas aprobadas. Total acumulado: 13 pruebas (6 + 7).
- Se ejecutó `python -m pytest -v` desde la raíz: 13 passed.

## Pendientes para el domingo 25
- Ejecutar la aplicación desde cero.
- Ejecutar todas las pruebas con pytest.
- Actualizar README.md con la nueva fuente, indicador e instrucciones.
- Guardar cambios en Git y registrar pendientes.

## Domingo 25 de octubre de 2026
- Verificación desde cero: se activó el venv, se instalaron dependencias y la app corrió sin problemas.
- Se probaron las 5 secciones del menú: Pregunta, Literatura, Fuentes de datos, Datos, Tema.
- Se realizó una consulta de prueba en "Fuentes de datos":
  - País: México
  - Indicador: PIB (USD corrientes)
  - Años: 2000–2024
  - Resultado: metadatos, gráfica, tabla y descarga CSV funcionando correctamente.
- Se ejecutaron las 13 pruebas automatizadas: todas aprobadas.
- Se actualizó `README.md`:
  - Nueva sección "Fuentes de datos integradas" con tabla de indicadores y países.
  - Instrucciones de uso de la sección "Fuentes de datos".
  - Estructura actualizada del proyecto.
  - Próximos pasos para la semana 3.
- Se creó `docs/pendientes_semana_3.md` con el plan para la siguiente semana.
- Semana 2 completada. 15 commits en el historial.

## Pendientes para la semana 3
- Integrar Banco de México (Banxico) e INEGI.
- Integrar IA en la sección "Pregunta" (sugerencias de preguntas, objetivos y protocolo).
- Subir el repositorio a GitHub.
- Configurar GitHub Actions para pruebas automáticas.
- Diseñar las secciones "Literatura" y "Tema".