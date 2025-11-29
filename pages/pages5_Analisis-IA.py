"""
Análisis con Inteligencia Artificial - Migrado a OpenAI 1.x
Detección de Temas Emergentes y Análisis con GPT-4o
"""

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

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(
    page_title="Análisis IA - Nutrisco",
    page_icon="🤖",
    layout="wide"
)

# CSS
st.markdown("""
<style>
header, footer, [data-testid="stToolbar"], [data-testid="stDeployButton"],
[data-testid="stDecoration"] {
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
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="ai-header">
    <h1>🤖 Análisis con Inteligencia Artificial</h1>
    <p>Detección de Temas Emergentes y Análisis de Tendencias</p>
</div>
""", unsafe_allow_html=True)

# Inicializar
db = ChatDatabase()

def generar_analisis_ia(df_conversaciones, dias):
    """Genera análisis con GPT-4o"""
    if df_conversaciones.empty:
        return "No hay conversaciones disponibles."
    
    # Filtrar últimos N días
    df_reciente = df_conversaciones.copy()
    df_reciente["fecha"] = pd.to_datetime(df_reciente["fecha"])
    fecha_limite = pd.Timestamp.now() - pd.Timedelta(days=dias)
    df_reciente = df_reciente[df_reciente["fecha"] >= fecha_limite]
    
    if df_reciente.empty:
        return f"No hay conversaciones en los últimos {dias} días."
    
    # Preparar contexto
    total = len(df_reciente)
    categorias = df_reciente["categoria"].value_counts().to_dict()
    derivados = (
        df_reciente["derivado"].sum()
        if "derivado" in df_reciente.columns
        else 0
    )
    
    # Ejemplos de consultas
    ejemplos = "\n".join(
        [
            f"- {row['categoria']}: {row['consulta'][:100]}..."
            for _, row in df_reciente.head(5).iterrows()
        ]
    )
    
    contexto = f"""
Total de consultas: {total}
Categorías: {categorias}
Consultas derivadas: {derivados}

Ejemplos de consultas recientes:
{ejemplos}
"""
    
    prompt = f"""
Eres un analista senior de Recursos Humanos especializado en atención al colaborador.

Analiza las siguientes consultas de los últimos {dias} días y genera un informe ejecutivo sobre:

1. **Temas más frecuentes** (Top 3)
2. **Temas emergentes** que están aumentando
3. **Recomendaciones accionables** para el equipo RRHH

DATOS:
{contexto}

Formato de respuesta:
- Conciso y directo (máximo 400 palabras)
- Usa bullets y emojis
- Enfócate en insights accionables
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un analista experto en RRHH que proporciona "
                        "insights claros y accionables."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=800,
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error al generar análisis: {str(e)}"

def generar_resumen_ejecutivo(df_conversaciones):
    """Genera resumen ejecutivo"""
    if df_conversaciones.empty:
        return "No hay datos disponibles."
    
    total = len(df_conversaciones)

    if "derivado" in df_conversaciones.columns:
        col = df_conversaciones["derivado"]

        # Normalizar a booleano:
        # True = derivado (no resuelto por el bot), False = resuelto por el bot
        if col.dtype == bool:
            derivados_bool = col
        elif col.dtype in ["int64", "float64"]:
            derivados_bool = col.astype(bool)
        else:
            derivados_bool = (
                col.astype(str)
                .str.strip()
                .str.lower()
                .map(
                    {
                        "si": True,
                        "sí": True,
                        "true": True,
                        "1": True,
                        "no": False,
                        "false": False,
                        "0": False,
                    }
                )
                .fillna(False)
            )

        resueltos = (~derivados_bool).sum()
    else:
        resueltos = 0

    tasa_resolucion = (resueltos / total * 100) if total > 0 else 0
    # st.write("DEBUG tasa_resolucion =", tasa_resolucion)
    categorias = (
        df_conversaciones["categoria"]
        .value_counts()
        .head(5)
        .to_dict()
    )
    
    prompt = f"""
Genera un resumen ejecutivo del estado del sistema de atención RRHH.

DATOS:
Total conversaciones: {total}
Tasa de resolución: {tasa_resolucion:.1f}%
Top 5 categorías: {categorias}

Incluye:
1. Estado general del servicio
2. Principales categorías de consultas
3. Áreas de mejora identificadas
4. Recomendaciones estratégicas (máximo 3)

Formato: Profesional, conciso (máximo 300 palabras)
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un consultor estratégico de RRHH.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=600,
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error: {str(e)}"

def generar_recomendaciones(df_conversaciones):
    """Genera recomendaciones específicas"""
    if df_conversaciones.empty:
        return "No hay datos suficientes."
    
    total = len(df_conversaciones)
    derivados = df_conversaciones["derivado"].sum()
    tasa_derivacion = (derivados / total * 100) if total > 0 else 0
    categorias_top = (
        df_conversaciones["categoria"].value_counts().head(5).to_dict()
    )
    
    prompt = f"""
Como consultor de RRHH, genera 5 recomendaciones específicas y accionables basadas en:

MÉTRICAS:
- Total consultas: {total}
- Tasa de derivación: {tasa_derivacion:.1f}%
- Top categorías: {categorias_top}

Genera recomendaciones priorizadas en formato:
1. **Título**: Descripción breve y acción concreta
2. **Título**: Descripción breve y acción concreta
...

Máximo 250 palabras.
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en optimización de procesos RRHH.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error: {str(e)}"

# Tabs
tab1, tab2, tab3 = st.tabs(
    ["🔥 Temas Emergentes", "📊 Resumen Ejecutivo", "💡 Recomendaciones"]
)

# TAB 1
with tab1:
    st.markdown("### 🔥 Detección de Temas Emergentes")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        periodo = st.selectbox(
            "Período de análisis",
            ["Últimos 7 días", "Últimos 14 días", "Últimos 30 días"],
        )
    
    with col2:
        umbral = st.number_input(
            "Umbral de frecuencia", min_value=3, max_value=20, value=5
        )
    
    if st.button("🔍 Analizar", type="primary", use_container_width=True):
        with st.spinner("Analizando con GPT-4o..."):
            dias = int(periodo.split()[1])
            df_conversaciones = db.obtener_conversaciones(limite=1000)
            
            if not df_conversaciones.empty:
                temas_emergentes = db.detectar_temas_emergentes(
                    umbral_frecuencia=umbral, dias_recientes=dias
                )
                
                st.markdown(
                    f"### 🎯 {len(temas_emergentes)} Temas Emergentes Detectados"
                )
                
                for idx, row in temas_emergentes.iterrows():
                    tema = row["categoria"]
                    freq = row["frecuencia_reciente"]
                    porcentaje = (freq / len(df_conversaciones) * 100)
                    
                    st.markdown(
                        f"""
                    <div class="tema-card">
                        <h3>🔥 {tema}</h3>
                        <p><strong>Frecuencia:</strong> {freq} menciones ({porcentaje:.1f}% del total)</p>
                        <p><strong>Período:</strong> Últimos {dias} días</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                
                if not temas_emergentes.empty:
                    st.bar_chart(
                        temas_emergentes.set_index("categoria")[
                            "frecuencia_reciente"
                        ]
                    )
                
                st.markdown("---")
                st.markdown("### 🤖 Análisis Inteligente (GPT-4o)")
                
                analisis = generar_analisis_ia(df_conversaciones, dias)
                st.markdown(
                    f'<div class="insight-card">{analisis}</div>',
                    unsafe_allow_html=True,
                )

# TAB 2
with tab2:
    st.markdown("### 📊 Resumen Ejecutivo")
    
    if st.button("📝 Generar Resumen", type="primary"):
        with st.spinner("Generando resumen con GPT-4o..."):
            df_conversaciones = db.obtener_conversaciones(limite=1000)
            
            if not df_conversaciones.empty:
                resumen = generar_resumen_ejecutivo(df_conversaciones)
                st.markdown(
                    f'<div class="insight-card">{resumen}</div>',
                    unsafe_allow_html=True,
                )
                
                st.markdown("### 📈 Métricas Clave")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Conversaciones", len(df_conversaciones))
                with col2:
                    derivados = df_conversaciones["derivado"].sum()
                    st.metric("Consultas Derivadas", derivados)
                with col3:
                    categorias_unicas = df_conversaciones["categoria"].nunique()
                    st.metric("Categorías Únicas", categorias_unicas)

# TAB 3
with tab3:
    st.markdown("### 💡 Recomendaciones Estratégicas")
    
    if st.button("🚀 Generar Recomendaciones", type="primary"):
        with st.spinner("Generando recomendaciones con GPT-4o..."):
            df_conversaciones = db.obtener_conversaciones(limite=1000)
            
            if not df_conversaciones.empty:
                recomendaciones = generar_recomendaciones(df_conversaciones)
                st.markdown(
                    f'<div class="insight-card"><h4>📋 Recomendaciones Priorizadas</h4>{recomendaciones}</div>',
                    unsafe_allow_html=True,
                )

st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #64748b;'>Análisis con IA • Nutrisco © 2025</p>",
    unsafe_allow_html=True,
)
