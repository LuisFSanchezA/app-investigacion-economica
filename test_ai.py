"""Script temporal para probar el módulo de IA."""
import os
os.environ["GEMINI_API_KEY"] = "AQ.Ab8RN6K1Z9zvXQNzOGHlUD0a0E8EYqQMY2aH2rOpnEO6kvWJeQ"  # temporal

import streamlit as st
st.secrets = {"GEMINI_API_KEY": os.environ["GEMINI_API_KEY"]}

from src.ai import sugerir_preguntas, sugerir_objetivos, generar_protocolo

# Ya probamos preguntas, ahora objetivos y protocolo
print("=" * 60)
print("SUGERIR OBJETIVOS")
print("=" * 60)
print(sugerir_objetivos(
    "¿Cuál fue el impacto del incremento al salario mínimo en la Zona Libre "
    "de la Frontera Norte sobre la probabilidad de que un trabajador labore "
    "en la informalidad durante el periodo 2018–2022?"
))

print()
print("=" * 60)
print("GENERAR PROTOCOLO (resumido)")
print("=" * 60)
print(generar_protocolo(
    tema="informalidad laboral en México",
    pregunta="¿Cuál fue el impacto del incremento al salario mínimo en la Zona Libre de la Frontera Norte sobre la probabilidad de que un trabajador labore en la informalidad durante el periodo 2018–2022?",
    objetivos="Analizar el impacto del incremento al salario mínimo en la ZLFN sobre la informalidad laboral. Comparar municipios fronterizos vs no fronterizos. Estimar el efecto causal con diferencias en diferencias.",
))