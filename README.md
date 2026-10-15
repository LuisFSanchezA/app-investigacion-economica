# Plataforma de investigación económica

Herramienta para organizar y explorar el proceso de investigación económica:
desde la pregunta inicial hasta el análisis de datos y la construcción del tema.

## Estado del proyecto

Versión 0.1 — Semana 1 completada.

Módulos actuales:
- **Pregunta**: definición y refinamiento de la pregunta de investigación (placeholder).
- **Literatura**: organización de fuentes académicas (placeholder).
- **Datos**: carga, validación y visualización de datos económicos (funcional).
- **Tema**: construcción y delimitación del tema (placeholder).

## Requisitos

- Python 3.12 o superior
- Git (opcional, para control de versiones)
- VS Code (recomendado)

## Instalación

1. Clona o descarga este repositorio:

   ```bash
   git clone <url-del-repositorio>
   cd investigacion-economica
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   streamlit run app.py
   python -m pytest -v
    ```

## Estructura del proyecto

investigacion-economica/
├── app.py                          # Aplicación principal de Streamlit
├── requirements.txt                # Dependencias del proyecto
├── README.md                       # Este archivo
├── .gitignore                      # Archivos excluidos de Git
├── .gitattributes                  # Normalización de finales de línea
├── app/                            # Módulos de la aplicación (futuro)
├── src/
│   ├── __init__.py
│   └── data_validation.py          # Funciones de validación de datos
├── tests/
│   └── test_data_validation.py     # Pruebas con pytest
├── data/
│   ├── raw/                        # Datos originales
│   │   └── pib_empleo_demo.csv     # CSV de prueba (datos ficticios)
│   └── processed/                  # Datos procesados (futuro)
└── docs/
    └── bitacora_semana_1.md        # Bitácora de desarrollo