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