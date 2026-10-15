\# Bitácora Semana 1 — Plataforma de investigación económica



\## Lunes 12 de octubre de 2026

\- Python 3.12.1 verificado (usar `py` porque el alias del Store intercepta `python`).

\- VS Code 1.141.0 y Git 2.56.0.windows.2 funcionando.

\- Carpeta `C:\\Users\\chiqu\\investigacion-economica` creada.

\- Entorno virtual `.venv` creado y activado.

\- Nota: hay que ejecutar `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` en cada nueva sesión de PowerShell antes de activar el venv.

\- pip actualizado de 23.2.1 a 26.2.1.

\- Instalados: streamlit 1.65.0, pandas 3.0.6, plotly 7.1.0, pytest 9.1.1.

\- `requirements.txt` generado con `pip freeze` (1558 bytes).

\- `app.py` con app mínima de Streamlit funcionando en http://localhost:8501.

\- Aprendizaje: el here-string `@'...'@` de PowerShell falló al pegar; usar variables línea por línea con `Set-Content` es más confiable.

\- Windows Firewall pidió permiso para el puerto 8501 (Streamlit). No se permitió acceso en redes públicas.



\## Pendientes para el martes 13

\- Crear repositorio Git local (`git init`).

\- Configurar nombre y email de Git si no están.

\- Crear estructura: `app/`, `src/`, `tests/`, `data/raw/`, `data/processed/`, `docs/`.

\- Crear `.gitignore` (incluir `.venv/`, `\_\_pycache\_\_/`, `.pytest\_cache/`, etc.).

\- Crear `.gitattributes` (normalizar CRLF/LF).

\- Revisar y limpiar `requirements.txt`.

\- Primer commit.

## Martes 13 de octubre de 2026
- Se reescribió `app.py` con la primera interfaz real de la plataforma.
- Se agregó título, descripción y pie de página.
- Se agregó menú lateral con las cuatro entradas:
  - Pregunta de investigación
  - Literatura
  - Datos
  - Tema
- Cada sección muestra un encabezado, descripción y un mensaje de "se desarrollará en las próximas semanas".
- La app corre correctamente en http://localhost:8501.
- Se verificó el auto-reload de Streamlit: al guardar cambios en `app.py`, la app se actualiza sola con "Always rerun".

## Pendientes
- Crear `data/raw/pib_empleo_demo.csv` con datos ficticios.
- Crear `src/data_validation.py` con la función `validate_dataframe`.
- Leer el CSV con pandas y validar columnas, tipos y faltantes.
- Mostrar tabla y estadísticas descriptivas en la sección "Datos" de la app.