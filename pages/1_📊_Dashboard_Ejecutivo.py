import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio utils al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.google_sheets_connector import get_hr_data

# Configuración de página
st.set_page_config(
    page_title="Dashboard Ejecutivo RRHH",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal con estilo profesional
st.markdown("""
<style>
.hero-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    color: white;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}
.hero-title {
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}
.hero-subtitle {
    font-size: 1.2rem;
    opacity: 0.9;
}
</style>

<div class="hero-header">
    <div class="hero-title">📊 Dashboard Ejecutivo RRHH</div>
    <div class="hero-subtitle">Sistema de Gestión de Consultas - Nutrisco</div>
</div>
""", unsafe_allow_html=True)

# Sidebar para configuración
st.sidebar.header("⚙️ Configuración")

# Credenciales de Google Sheets (usar secrets de Streamlit)
SPREADSHEET_URL = st.sidebar.text_input(
    "ID de Google Sheets",
    value="1JqFay6hXlUuURwZFANmr6FXARZqfH7tI",
    help="ID del Google Sheet de RRHH (solo la parte después de /d/)"
)

# Cargar datos
with st.spinner("🔄 Cargando datos desde Google Sheets..."):
    df = get_hr_data(SPREADSHEET_URL)

# Cargar datos
with st.spinner("🔄 Cargando datos desde Google Sheets..."):
    df = get_hr_data(SPREADSHEET_URL)

# Verificar si hay datos
if df.empty:
    st.error("""
    ❌ No se pudieron cargar los datos. Verifica:
    1. Que la URL de Google Sheets sea correcta
    2. Que el Sheet esté compartido con el service account
    3. Que haya datos en la hoja
    """)
    st.stop()

# Mostrar información de datos cargados
st.sidebar.success(f"✅ {len(df)} registros cargados")
st.sidebar.write(f"📅 Período: {df['fecha_creacion'].min().strftime('%d/%m/%Y')} - {df['fecha_creacion'].max().strftime('%d/%m/%Y')}")

# Filtros en sidebar
st.sidebar.header("🎛️ Filtros")

# Fechas por defecto (últimos 3 meses)
default_end = datetime.now()
default_start = default_end - timedelta(days=90)

col1, col2 = st.sidebar.columns(2)
with col1:
    fecha_desde = st.date_input("Desde", value=default_start)
with col2:
    fecha_hasta = st.date_input("Hasta", value=default_end)

# Filtro por área
areas = ['Todos'] + sorted(df['area'].unique().tolist())
area_seleccionada = st.sidebar.selectbox("Área", areas)

# Aplicar filtros
df_filtrado = df.copy()
df_filtrado = df_filtrado[
    (df_filtrado['fecha_creacion'].dt.date >= fecha_desde) & 
    (df_filtrado['fecha_creacion'].dt.date <= fecha_hasta)
]

if area_seleccionada != 'Todos':
    df_filtrado = df_filtrado[df_filtrado['area'] == area_seleccionada]

# CALCULAR KPIs
total_consultas = len(df_filtrado)
consultas_resueltas = len(df_filtrado[df_filtrado['estado'] == 'Resuelto'])
consultas_derivadas = len(df_filtrado[df_filtrado['estado'] == 'Derivado'])

tasa_resolucion = (consultas_resueltas / total_consultas * 100) if total_consultas > 0 else 0
tasa_derivacion = (consultas_derivadas / total_consultas * 100) if total_consultas > 0 else 0

# Resolución primer contacto
if 'resolucion_primer_contacto' in df_filtrado.columns:
    resolucion_primer_contacto = (df_filtrado['resolucion_primer_contacto'].sum() / total_consultas * 100) if total_consultas > 0 else 0
else:
    resolucion_primer_contacto = 0

# Temas emergentes (últimos 7 días)
ultimos_7_dias = datetime.now() - timedelta(days=7)
temas_emergentes = len(df_filtrado[df_filtrado['fecha_creacion'] >= ultimos_7_dias]['categoria'].unique())

# Tiempo promedio de respuesta (días)
if 'dias_desde_creacion' in df_filtrado.columns:
    tiempo_promedio = df_filtrado['dias_desde_creacion'].mean()
else:
    tiempo_promedio = 0

# ============================================================================
# KPIs PRINCIPALES
# ============================================================================

st.subheader("🎯 KPIs Principales")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Consultas",
        value=f"{total_consultas:,}",
        delta="Período seleccionado"
    )

with col2:
    st.metric(
        label="Resolución 1er Contacto", 
        value=f"{resolucion_primer_contacto:.1f}%",
        delta="Meta: ≥70%",
        delta_color="normal" if resolucion_primer_contacto >= 70 else "inverse"
    )

with col3:
    st.metric(
        label="Tiempo Promedio",
        value=f"{tiempo_promedio:.1f}d",
        delta="Meta: ≤2d",
        delta_color="normal" if tiempo_promedio <= 2 else "inverse"
    )

with col4:
    st.metric(
        label="Temas Emergentes",
        value=temas_emergentes,
        delta="Últimos 7 días"
    )

# ============================================================================
# KPIs SECUNDARIOS
# ============================================================================

st.subheader("📈 Métricas de Desempeño")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Consultas Resueltas",
        value=f"{consultas_resueltas:,}",
        delta=f"{tasa_resolucion:.1f}%"
    )

with col2:
    st.metric(
        label="Consultas Derivadas", 
        value=f"{consultas_derivadas:,}",
        delta=f"{tasa_derivacion:.1f}%"
    )

with col3:
    # Eficiencia calculada
    eficiencia = 100 - tasa_derivacion
    st.metric(
        label="Eficiencia Equipo",
        value=f"{eficiencia:.1f}%",
        delta="autonomía"
    )

with col4:
    # Promedio diario
    dias_periodo = (fecha_hasta - fecha_desde).days + 1
    promedio_diario = total_consultas / dias_periodo if dias_periodo > 0 else 0
    st.metric(
        label="Promedio Diario",
        value=f"{promedio_diario:.1f}",
        delta="consultas/día"
    )

# ============================================================================
# GRÁFICOS Y VISUALIZACIONES
# ============================================================================

st.markdown("---")
st.subheader("📊 Análisis Visual")

# Dos columnas para gráficos
col1, col2 = st.columns(2)

with col1:
    # Consultas por área
    st.markdown("**📋 Distribución por Área**")
    area_counts = df_filtrado['area'].value_counts()
    fig = px.pie(
        values=area_counts.values,
        names=area_counts.index,
        title="Consultas por Área"
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Evolución temporal
    st.markdown("**📈 Evolución Temporal**")
    daily_counts = df_filtrado.groupby(df_filtrado['fecha_creacion'].dt.date).size()
    fig = px.line(
        x=daily_counts.index,
        y=daily_counts.values,
        title="Consultas por Día",
        labels={'x': 'Fecha', 'y': 'Número de Consultas'}
    )
    st.plotly_chart(fig, use_container_width=True)

# Gráfico de categorías
st.markdown("**🎯 Consultas por Categoría**")
categoria_counts = df_filtrado['categoria'].value_counts()
fig = px.bar(
    x=categoria_counts.values,
    y=categoria_counts.index,
    orientation='h',
    title="Top Categorías de Consultas",
    labels={'x': 'Número de Consultas', 'y': 'Categoría'}
)
st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TABLA DE DETALLES
# ============================================================================

st.markdown("---")
st.subheader("📋 Detalle de Consultas")

# Mostrar columnas relevantes
columnas_mostrar = ['fecha_creacion', 'usuario', 'area', 'categoria', 'consulta', 'estado']
columnas_disponibles = [col for col in columnas_mostrar if col in df_filtrado.columns]

st.dataframe(
    df_filtrado[columnas_disponibles].head(50),
    use_container_width=True,
    height=400
)

# ============================================================================
# RESUMEN EJECUTIVO
# ============================================================================

st.markdown("---")
st.subheader("📋 Resumen Ejecutivo")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**📈 Tendencias**")
    st.write(f"- 📊 **Volumen total:** {total_consultas} consultas en el período")
    st.write(f"- ✅ **Efectividad:** {tasa_resolucion:.1f}% de consultas resueltas")
    st.write(f"- ⚡ **Respuesta:** {tiempo_promedio:.1f} días promedio")
    st.write(f"- 🎯 **Autonomía:** {resolucion_primer_contacto:.1f}% resueltas en primer contacto")

with col2:
    st.markdown("**🔍 Insights**")
    area_mas_consultas = df_filtrado['area'].mode()[0] if not df_filtrado.empty else "N/A"
    categoria_mas_comun = df_filtrado['categoria'].mode()[0] if not df_filtrado.empty else "N/A"
    
    st.write(f"- 🏢 **Área más activa:** {area_mas_consultas}")
    st.write(f"- 📝 **Tema principal:** {categoria_mas_comun}")
    st.write(f"- 🔥 **Temas emergentes:** {temas_emergentes} categorías nuevas")
    st.write(f"- 📅 **Período analizado:** {fecha_desde} a {fecha_hasta}")

# Footer
st.markdown("---")
st.markdown(f"**🔄 Última actualización:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
