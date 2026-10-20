# Plataforma de investigación económica

[![Tests](https://github.com/LuisFSanchezA/app-investigacion-economica/actions/workflows/tests.yml/badge.svg)](https://github.com/LuisFSanchezA/app-investigacion-economica/actions/workflows/tests.yml)

Herramienta para organizar y explorar el proceso de investigación económica:
desde la pregunta inicial hasta el análisis de datos y la construcción del tema.


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

## Fuentes de datos integradas

### Banco Mundial

Se integró la API pública del Banco Mundial para consultar series económicas reales.

**Indicadores disponibles:**

| Código | Nombre | Unidad |
|---|---|---|
| `NY.GDP.MKTP.CD` | PIB | USD corrientes |
| `NY.GDP.PCAP.CD` | PIB per cápita | USD corrientes |
| `SP.POP.TOTL` | Población total | personas |
| `SL.UEM.TOTL.ZS` | Tasa de desempleo | % |

**Países disponibles:**

| Código | País |
|---|---|
| MEX | México |
| USA | Estados Unidos |
| BRA | Brasil |
| ARG | Argentina |
| CHL | Chile |
| COL | Colombia |

**Uso:**

1. Ir a la sección **"Fuentes de datos"** en el menú lateral.
2. Elegir país, indicador y rango de años.
3. Clic en **Consultar**.
4. Ver metadatos, gráfica, tabla y descargar CSV.

**Características:**

- Metadatos completos: fuente, indicador, unidad, periodo, fecha de consulta, URL.
- Normalización de series temporales.
- Detección de duplicados y valores faltantes.
- Manejo robusto de errores (conexión, HTTP, respuestas vacías).
- Exportación a CSV.

**Nota:** los datos son reales y provienen directamente del Banco Mundial.
Verificar la fecha de consulta antes de usarlos en análisis formales.

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
├── app.py # Aplicación principal de Streamlit
├── requirements.txt # Dependencias del proyecto
├── README.md # Este archivo
├── .gitignore
├── .gitattributes
├── app/
├── src/
│ ├── init.py
│ ├── data_validation.py # Validación de DataFrames
│ └── fuentes/ # Conectores de fuentes externas
│ ├── init.py
│ ├── base.py # Clase abstracta FuenteBase
│ ├── metadatos.py # Esquema de metadatos
│ ├── normalizacion.py # Funciones de normalización
│ └── world_bank.py # Conector del Banco Mundial
├── tests/
│ ├── test_data_validation.py # 6 pruebas
│ └── test_world_bank.py # 7 pruebas
├── data/
│ ├── raw/
│ │ └── pib_empleo_demo.csv
│ └── processed/
└── docs/
├── bitacora_semana_1.md
├── bitacora_semana_2.md
└── pendientes_semana_3.md