# Plataforma de investigación económica

[![Tests](https://github.com/LuisFSanchezA/app-investigacion-economica/actions/workflows/tests.yml/badge.svg)](https://github.com/LuisFSanchezA/app-investigacion-economica/actions/workflows/tests.yml)

Herramienta para organizar y explorar el proceso de investigación económica:
desde la pregunta inicial hasta el análisis de datos y la construcción del tema.

## Estado del proyecto

**Versión 0.2-beta** — beta interna.

Módulos actuales:

- **Pregunta**: definición y refinamiento de la pregunta de investigación (funcional).
- **Literatura**: organización de fuentes académicas, bibliometría y redes de co-autoría (funcional, con OpenAlex).
- **Datos**: carga, validación y visualización de datos económicos (funcional).
- **Tema**: diagnóstico, delimitación, enunciado, justificación y resumen ejecutivo (funcional; la IA es opcional).

## Fuentes de datos integradas

### Banco Mundial

API pública del Banco Mundial para consultar series económicas reales.

| Código | Nombre | Unidad |
|---|---|---|
| `NY.GDP.MKTP.CD` | PIB | USD corrientes |
| `NY.GDP.PCAP.CD` | PIB per cápita | USD corrientes |
| `SP.POP.TOTL` | Población total | personas |
| `SL.UEM.TOTL.ZS` | Tasa de desempleo | % |

Países: MEX, USA, BRA, ARG, CHL, COL.

### INEGI

Conector para la API de Indicadores del INEGI (BIE-BISE/2.0).

- Catálogo de 5 indicadores (PIB, población, desocupación, inflación).
- Filtrado **siempre por entidad**, incluido `"0"` (Nacional).
- Requiere `INEGI_TOKEN` (ver [Configuración de secretos](#configuración-de-secretos)).

### Banxico (SIE)

Conector para el Sistema de Información Económica del Banco de México.

- Series económicas (tipo de cambio, tasas, inflación, etc.).
- Requiere `BANXICO_TOKEN` (ver [Configuración de secretos](#configuración-de-secretos)).

### OpenAlex

Conector para la API de OpenAlex (literatura académica).

- Búsqueda de corpus, metadatos y redes de co-autoría / co-palabras.
- Requiere `OPENALEX_API_KEY` y `OPENALEX_EMAIL` (ver [Configuración de secretos](#configuración-de-secretos)).

**Nota:** los datos son reales y provienen directamente de las fuentes.
Verificar la fecha de consulta antes de usarlos en análisis formales.

## Requisitos

- Python 3.12 o superior
- Git (opcional, para control de versiones)
- VS Code (recomendado)

## Instalación

```bash
git clone <url-del-repositorio>
cd investigacion-economica
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
streamlit run app.py
```

Para desarrollo (incluye `pytest`):

```bash
pip install -r requirements-dev.txt
python -m pytest -v
```

## Configuración de secretos

La app usa secretos para las fuentes que requieren autenticación. Copia el
ejemplo y rellena tus valores:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Variables usadas:

| Variable | Servicio | Dónde obtenerla |
|---|---|---|
| `OPENALEX_API_KEY` | OpenAlex | https://openalex.org/ |
| `OPENALEX_EMAIL` | OpenAlex (polite pool) | tu correo institucional |
| `INEGI_TOKEN` | INEGI | https://www.inegi.org.mx/servicios/api_indicadores.html |
| `BANXICO_TOKEN` | Banxico (SIE) | https://www.banxico.org.mx/SieAPIRest/service/v1/token |
| `GEMINI_API_KEY` | Google AI Studio (Gemini) | https://aistudio.google.com/app/apikey |
| `GEMINI_MODEL` | Gemini (config, no secreto) | ej. `gemini-2.0-flash` |

**Nunca** subas `.streamlit/secrets.toml` al repositorio (ya está en `.gitignore`).
En Streamlit Cloud, configura los secretos en el panel de la app.

## Uso de IA

La sección **Tema** ofrece sugerencias de IA (enunciado, justificación y resumen
ejecutivo) mediante Gemini. Consideraciones:

- La IA es un **acelerador opcional**, no un requisito. La UI funciona sin IA:
  el estudiante puede llenar los campos manualmente.
- La latencia de Gemini en hora pico puede ser de **30-60s** por llamada; hay
  cache de 24h por combinación de insumos.
- El resultado de la IA es un **borrador**: debe verificarse y editarse.
- Si no hay `GEMINI_API_KEY`, los botones de IA muestran un aviso en lugar de fallar.

## Declaración de uso de IA

Este proyecto usa IA generativa (Gemini) como herramienta de apoyo para
sugerir borradores de enunciado, justificación y resumen ejecutivo. Los
resultados de la IA **no sustituyen** el juicio del estudiante ni la
verificación de fuentes. Todo texto generado debe revisarse, editarse y
validarse antes de usarse en un trabajo académico. El uso de IA en este
proyecto se declara en línea con las buenas prácticas de transparencia
académica.

## Tests

- Estado actual: **152 tests**.
- Correr: `python -m pytest -v` (requiere `requirements-dev.txt`).
- CI: GitHub Actions corre `pytest` en cada push (ver badge arriba).

## Estructura del proyecto

```
investigacion-economica/
├── app.py                      # Aplicación principal de Streamlit
├── requirements.txt            # Dependencias de producción
├── requirements-dev.txt        # Dependencias de desarrollo (pytest)
├── README.md
├── .gitignore
├── .gitattributes
├── .streamlit/
│   └── secrets.toml.example    # Plantilla de secretos (sin valores reales)
├── app/
│   ├── seccion_tema.py
│   └── ...                     # Otras secciones (Pregunta, Literatura, Datos)
├── src/
│   ├── __init__.py
│   ├── data_validation.py      # Validación de DataFrames
│   ├── ai/                     # Prompts, asistente y cache de Tema
│   │   ├── __init__.py
│   │   ├── prompts_tema.py
│   │   ├── asistente_tema.py
│   │   └── cache_tema.py
│   └── fuentes/                # Conectores de fuentes externas
│       ├── __init__.py
│       ├── base.py
│       ├── metadatos.py
│       ├── normalizacion.py
│       ├── world_bank.py
│       ├── inegi.py
│       ├── banxico.py
│       └── openalex.py
├── tests/
│   ├── test_data_validation.py
│   ├── test_world_bank.py
│   ├── test_inegi.py
│   ├── test_banxico.py
│   ├── test_openalex.py
│   ├── test_asistente_tema.py
│   ├── test_flujo_e2e.py
│   └── ...
├── data/
│   ├── raw/
│   └── processed/
└── docs/
    ├── bitacora_semana_1.md
    ├── bitacora_semana_2.md
    └── bitacora_2026-11-20.md
```

> Ajusta los nombres de archivos de `app/` y `src/fuentes/` si no coinciden
> exactamente con tu repo.

## Deploy

### Streamlit Cloud (recomendado)

1. Sube el repo a GitHub.
2. En [share.streamlit.io](https://share.streamlit.io), conecta el repo.
3. Entry point: `app.py`.
4. En **Settings → Secrets**, pega el contenido de tu `secrets.toml` local
   (con los valores reales).
5. Deploy.

### Notas de deploy

- `requirements.txt` no incluye `pytest` (está en `requirements-dev.txt`).
- La app debe degradar elegantemente si falta un secreto: muestra un aviso,
  no crashea.
- Verificar que `.streamlit/secrets.toml` **no** esté en el repo.

## Roadmap

- [x] Banco Mundial
- [x] INEGI
- [x] Banxico (SIE)
- [x] OpenAlex + bibliometría
- [x] Sección Tema (UI + IA opcional)
- [x] Hardening (README, secrets, tests E2E)
- [ ] Deploy en Streamlit Cloud ← en curso
- [ ] Evaluar IA de pago (Gemini tier pago) si la latencia es problema
- [ ] F5b/F5c (post-beta): dataset NodOS + tesis vecinas con embeddings