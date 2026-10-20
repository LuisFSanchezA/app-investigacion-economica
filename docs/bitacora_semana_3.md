# Pendientes para la semana 3

## Objetivo general
Ampliar las fuentes de datos e integrar la sección de "Pregunta" con asistencia de IA.

## Tareas sugeridas

### Fuentes de datos
- [ ] Integrar Banco de México (Banxico) con API.
- [ ] Integrar INEGI (descarga manual o API).
- [ ] Agregar más indicadores del Banco Mundial.
- [ ] Agregar más países.

### IA (sección Pregunta)
- [ ] Integrar DeepSeek o Gemini para sugerir preguntas de investigación.
- [ ] Integrar sugerencia de objetivos (general y específicos).
- [ ] Integrar generación de borrador de protocolo.
- [ ] Configurar `secrets.toml` con las API keys.
- [ ] Probar con 2-3 temas de ejemplo.

### Infraestructura
- [ ] Subir el repositorio a GitHub.
- [ ] Configurar GitHub Actions para correr pytest en cada push.
- [ ] Agregar más pruebas automatizadas.

### Interfaz
- [ ] Diseñar la sección "Literatura".
- [ ] Diseñar la sección "Tema".

## Recordatorio
- Mantener la regla de los 15 minutos para errores.
- Una fuente de datos a la vez.
- Documentar cada decisión pedagógica, no solo la técnica.

# Semana 3 — IA y ampliación de fuentes

## Lunes 19 de octubre de 2026 (o fecha actual)
- Se configuró GitHub Actions para correr pytest en cada push.
- Se agregó badge de estado al README.
- Se creó el release v0.2.0 marcando el cierre de la semana 2.

## Integración de IA (sección Pregunta)
- Se instaló el SDK `google-genai` de Google Gemini.
- Se configuró `.streamlit/secrets.toml` con `GEMINI_API_KEY` (excluido de Git).
- Se creó el módulo `src/ai/`:
  - `prompts.py`: prompts pedagógicos para sugerir preguntas, objetivos y protocolo.
  - `asistente.py`: funciones `sugerir_preguntas`, `sugerir_objetivos`, `generar_protocolo` con reintentos automáticos.
  - `__init__.py`: expone las funciones.
- Se integró la sección "Pregunta" en `app.py`:
  - Paso 1: input de tema.
  - Paso 2: botón para sugerir preguntas (5 preguntas con variables, periodo y contexto).
  - Paso 3: input para la pregunta final.
  - Paso 4: botón para sugerir objetivos (general + 4 específicos).
  - Paso 5: botón para generar borrador de protocolo completo.
  - Descarga del protocolo en Markdown.
  - Manejo de errores con mensajes claros.
- Se probó con el tema "informalidad laboral en México":
  - Sugerencias de altísima calidad (acotó el tema, marcó [VERIFICAR], recomendó opción con justificación metodológica).
  - Protocolo completo con título, planteamiento, pregunta, objetivos, justificación, marco teórico, hipótesis, metodología (con especificación DiD), cronograma y 10 referencias reales.
- Se agregaron reintentos automáticos (3 intentos, 5s entre cada uno) para manejar saturación del modelo (error 503).

## Modelo usado
- Google Gemini `gemini-3.8-flash` (tier gratuito: 1,500 requests/día).
- Costo: $0 para el volumen esperado de uso.

## Pendientes
- Agregar pruebas automatizadas con mock para el módulo de IA.
- Documentar el uso de IA en el README (declaración de uso).
- Evaluar si conviene migrar a DeepSeek para producción (más barato, misma calidad).
- Seguir con Banxico/INEGI como fuentes adicionales.

## Martes 20 de octubre de 2026 
- Se creó `tests/test_ai.py` con 9 pruebas automatizadas usando mock de Gemini.
- Pruebas implementadas:
  1. `test_sugerir_preguntas_exitoso`: verifica que se devuelve texto.
  2. `test_sugerir_preguntas_tema_vacio`: verifica ValueError con tema vacío.
  3. `test_sugerir_objetivos_exitoso`: verifica que se devuelve texto.
  4. `test_sugerir_objetivos_pregunta_vacia`: verifica ValueError con pregunta vacía.
  5. `test_generar_protocolo_exitoso`: verifica que se devuelve texto.
  6. `test_generar_protocolo_faltan_datos`: verifica ValueError sin tema o pregunta.
  7. `test_error_saturacion`: verifica que un 503 se convierte en ConnectionError.
  8. `test_error_modelo_no_disponible`: verifica que un 404 se convierte en ConnectionError.
  9. `test_sin_api_key`: verifica ValueError si falta GEMINI_API_KEY.
- Se eliminó `test_ai.py` de la raíz (script temporal) para evitar conflictos con pytest.
- Resultado: 22 pruebas aprobadas en total (9 + 6 + 7) en 12.82 segundos.
- El CI de GitHub Actions ahora también valida el módulo de IA (con mock, sin necesidad de API key real).