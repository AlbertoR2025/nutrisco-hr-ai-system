"""
Sistema de Atención a Personas con IA - Nutrisco
Home / Landing Page
"""

import streamlit as st
from pathlib import Path

# Configuración de página
st.set_page_config(
    page_title="Panel de Control - Nutrisco",
    page_icon="🎛️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "Sistema RRHH Nutrisco © 2025"
    }

)

# CSS personalizado
st.markdown("""
<style>
header, footer, [data-testid="stToolbar"], [data-testid="stDeployButton"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {
    display: none !important;
}

.stApp {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}

.main-header {
    background: linear-gradient(135deg, #ea580c 0%, #dc2626 100%);
    padding: 3rem 2rem;
    border-radius: 24px;
    text-align: center;
    color: white;
    margin-bottom: 3rem;
    box-shadow: 0 20px 50px rgba(234, 88, 12, 0.35);
}

.main-header h1 {
    font-size: 2.8rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.02em;
}

.main-header p {
    font-size: 1.3rem;
    margin: 1rem 0 0 0;
    opacity: 0.95;
}

.feature-card {
    background: #1e293b;
    padding: 2rem;
    border-radius: 16px;
    border-left: 4px solid #f97316;
    margin-bottom: 1.5rem;
    transition: all 0.3s ease;
}

.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(249, 115, 22, 0.3);
}

.feature-card h3 {
    color: #f97316;
    margin: 0 0 0.5rem 0;
}

.feature-card p {
    color: #cbd5e1;
    margin: 0;
}

.stats-card {
    background: linear-gradient(135deg, #1e293b, #334155);
    padding: 1.5rem;
    border-radius: 12px;
    text-align: center;
    border: 1px solid #475569;
}

.stats-card h2 {
    color: #f97316;
    font-size: 2.5rem;
    margin: 0;
}

.stats-card p {
    color: #94a3b8;
    margin: 0.5rem 0 0 0;
}
</style>
""", unsafe_allow_html=True)

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🏢 Sistema de Atención a Personas</h1>
    <p>Plataforma Inteligente RRHH - Nutrisco</p>
</div>
""", unsafe_allow_html=True)

# Descripción
st.markdown("""
### 👋 Bienvenido al Sistema de Gestión RRHH

Este sistema automatiza la atención a colaboradores, analiza tendencias y optimiza 
los procesos del equipo de Recursos Humanos mediante Inteligencia Artificial.
""")

# Características principales
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Dashboard Ejecutivo</h3>
        <p>KPIs en tiempo real, gráficos de tendencias y métricas clave de desempeño del equipo.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <h3>🔍 Búsqueda Avanzada</h3>
        <p>Encuentra cualquier conversación histórica en segundos con filtros inteligentes.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>🤖 Chatbot Inteligente</h3>
        <p>Respuestas automáticas 24/7 a preguntas frecuentes de colaboradores.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="feature-card">
        <h3>📑 Análisis con IA</h3>
        <p>Detecta temas emergentes y genera resúmenes automáticos semanales.</p>
    </div>
    """, unsafe_allow_html=True)

# Estadísticas rápidas
st.markdown("### 📈 Vista Rápida del Sistema")

# Cargar KPIs si existe la BD
try:
    from utils.database import ChatDatabase
    db = ChatDatabase()
    kpis = db.calcular_kpis()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h2>{kpis['total_consultas']}</h2>
            <p>Total Consultas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h2>{kpis['tasa_resolucion_primer_contacto']}%</h2>
            <p>Resolución 1er Contacto</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <h2>{kpis['tiempo_promedio_respuesta_mins']:.0f}h</h2>
            <p>Tiempo Promedio</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stats-card">
            <h2>{kpis['temas_emergentes_nuevos']}</h2>
            <p>Temas Emergentes</p>
        </div>
        """, unsafe_allow_html=True)

except Exception as e:
    st.info("💡 Ejecuta primero el script de migración: `python scripts/migrate_excel_to_sqlite.py`")

# Instrucciones
st.markdown("---")
st.markdown("""
### 🚀 Comenzar a Usar el Sistema

**Para empleados:**
- Usa el **Chatbot Colaboradores** para consultas rápidas 24/7

**Para el equipo RRHH:**
1. **Dashboard Ejecutivo** - Visualiza KPIs y tendencias
2. **Búsqueda Historial** - Encuentra conversaciones pasadas
3. **Análisis IA** - Revisa temas emergentes y resúmenes

**Documentación:**
- [Manual Usuario Final](docs/MANUAL_USUARIO_FINAL.md)
- [Manual Operaciones RRHH](docs/MANUAL_OPERACIONES.md)
""")

# Footer
st.markdown("---")
st.markdown("""
<p style='text-align: center; color: #64748b; font-size: 0.9rem;'>
Sistema desarrollado para Nutrisco • 2025 • Powered by AI
</p>
""", unsafe_allow_html=True)
