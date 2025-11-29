# Crear archivo corregido
@"
\"\"\"
Análisis con Inteligencia Artificial - Migrado a OpenAI 1.x
Detección de Temas Emergentes y Análisis con GPT-4o
\"\"\"

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

sys.path.append(str(Path(__file__).parent.parent))
from utils.database import ChatDatabase

# CORRECCIÓN: Inicialización segura del cliente OpenAI
try:
    client = OpenAI(api_key=os.getenv(\"OPENAI_API_KEY\"))
except Exception as e:
    st.error(f\"Error inicializando OpenAI: {e}\")
    client = None

st.set_page_config(
    page_title=\"Análisis IA - Nutrisco\",
    page_icon=\"🤖\",
    layout=\"wide\"
)

# CSS
st.markdown(\"\"\"
<style>
header, footer, [data-testid=\"stToolbar\"], [data-testid=\"stDeployButton\"],
[data-testid=\"stDecoration\"] {
    display: none !important;
}

.stApp {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}

.ai-header {
    background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    padding: 2rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 2rem;
    text-align: center;
}

.tema-card {
    background: linear-gradient(135deg, #dc2626 0%, #ea580c 100%);
    padding: 1.5rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 1rem;
}

.insight-card {
    background: #1e293b;
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 4px solid #8b5cf6;
    margin-bottom: 1rem;
    color: #cbd5e1;
}

.insight-card h4 {
    color: #8b5cf6;
    margin: 0 0 0.5rem 0;
}
</style>
\"\"\", unsafe_allow_html=True)

# Header
st.markdown(\"\"\"
<div class=\"ai-header\">
    <h1>🤖 Análisis con Inteligencia Artificial</h1>
    <p>Detección de Temas Emergentes y Análisis de Tendencias</p>
</div>
\"\"\", unsafe_allow_html=True)

# El resto del código se mantiene igual...
# [PEGA AQUÍ EL RESTO DEL CÓDIGO ORIGINAL DE pages5_Analisis-IA.py]
\"\"@ | Out-File -FilePath \"pages/pages5_Analisis-IA.py\" -Encoding utf8