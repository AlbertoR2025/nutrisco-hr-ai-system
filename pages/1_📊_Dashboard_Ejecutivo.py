import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Agregar utils al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))

from advanced_database import AdvancedHRDatabase

# Configuración de página
st.set_page_config(
    page_title="Dashboard Ejecutivo RRHH",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título principal
st.title("📊 Dashboard Ejecutivo RRHH")
st.markdown("Métricas y KPIs del Sistema de Atención a Colaboradores")

# Inicializar base de datos
@st.cache_resource
def load_database():
    return AdvancedHRDatabase()

db = load_database()

# Sidebar para filtros
st.sidebar.header("🎛️ Filtros")

# Fechas por defecto (últimos 3 meses)
default_end = datetime.now()
default_start = default_end - timedelta(days=90)

col1, col2 = st.sidebar.columns(2)
with col1:
    fecha_desde = st.date_input(
        "Desde",
        value=default_start,
        max_value=datetime.now()
    )
with col2:
    fecha_hasta = st.date_input(
        "Hasta", 
        value=default_end,
        max_value=datetime.now()
    )

# Botón para actualizar
if st.sidebar.button("🔄 Actualizar Dashboard"):
    st.rerun()

# Mostrar datos cargados
st.sidebar.markdown("---")
st.sidebar.metric("📊 Registros Cargados", f"{len(db.df):,}")

# KPIs Principales
st.markdown("---")
st.subheader("🎯 KPIs Principales")

try:
    # Obtener KPIs
    kpis = db.get_kpis(fecha_desde, fecha_hasta)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Consultas",
            value=f"{kpis['total_consultas']:,}",
            delta=f"Período seleccionado"
        )
    
    with col2:
        st.metric(
            label="Resolución 1er Contacto",
            value=f"{kpis['resolucion_primer_contacto']:.1f}%",
            delta=f"Meta: ≥70%",
            delta_color="normal" if kpis['resolucion_primer_contacto'] >= 70 else "inverse"
        )
    
    with col3:
        st.metric(
            label="Tiempo Promedio Respuesta",
            value=f"{kpis['tiempo_promedio_respuesta']:.1f}h",
            delta=f"Meta: ≤24h",
            delta_color="normal" if kpis['tiempo_promedio_respuesta'] <= 24 else "inverse"
        )
    
    with col4:
        st.metric(
            label="Temas Emergentes",
            value=kpis['temas_emergentes'],
            delta="Últimos 7 días"
        )
    
    # KPIs Secundarios
    st.markdown("---")
    st.subheader("📈 Métricas de Desempeño")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Consultas Resueltas",
            value=kpis['consultas_resueltas'],
            delta=f"{kpis['tasa_resolucion']:.1f}%"
        )
    
    with col2:
        st.metric(
            label="Consultas Derivadas",
            value=kpis['consultas_derivadas'],
            delta=f"{kpis['tasa_derivacion']:.1f}%"
        )
    
    with col3:
        st.metric(
            label="Promedio Diario",
            value=f"{kpis['promedio_diario']:.1f}",
            delta="consultas/día"
        )
    
    with col4:
        st.metric(
            label="Eficiencia Equipo",
            value=f"{kpis['eficiencia_equipo']:.1f}%",
            delta="autonomía"
        )
    
    # Análisis Visual
    st.markdown("---")
    st.subheader("📊 Análisis Visual")
    
    # Dos columnas para gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔝 Top 10 Temas Más Recurrentes**")
        try:
            top_temas = db.get_top_topics(limit=10, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
            if not top_temas.empty:
                fig = px.bar(
                    top_temas,
                    x='Cantidad',
                    y='Tema',
                    orientation='h',
                    title="Temas Más Frecuentes",
                    color='Cantidad',
                    color_continuous_scale='blues'
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos para mostrar en el período seleccionado")
        except Exception as e:
            st.error(f"Error generando gráfico de temas: {str(e)}")
    
    with col2:
        st.markdown("**📈 Tendencias Mensuales**")
        try:
            trends_data = db.get_trends_data()
            if not trends_data.empty:
                fig = px.line(
                    trends_data,
                    x='mes',
                    y='cantidad',
                    color='categoria_estandar',
                    title="Evolución de Consultas por Categoría",
                    markers=True
                )
                fig.update_layout(xaxis_title="Mes", yaxis_title="Cantidad de Consultas")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No hay datos de tendencias disponibles")
        except Exception as e:
            st.error(f"Error generando gráfico de tendencias: {str(e)}")
    
    # Análisis por departamento
    st.markdown("**🏢 Métricas por Departamento**")
    try:
        dept_metrics = db.get_department_metrics()
        if not dept_metrics.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(
                    dept_metrics,
                    values='total_consultas',
                    names='departamento',
                    title="Distribución de Consultas por Departamento"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = px.bar(
                    dept_metrics,
                    x='departamento',
                    y='tiempo_promedio_horas',
                    title="Tiempo Promedio de Respuesta por Departamento",
                    color='tiempo_promedio_horas',
                    color_continuous_scale='rdylgn_r'
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de departamentos disponibles")
    except Exception as e:
        st.error(f"Error generando análisis por departamento: {str(e)}")

except Exception as e:
    st.error(f"❌ Error en el dashboard: {str(e)}")
    st.info("💡 Sugerencia: Ejecuta el ETL primero para limpiar los datos")

# Footer
st.markdown("---")
st.markdown(
    "**💡 Tip:** Usa el ETL para transformar tus datos crudos en información lista para análisis. "
    "Ejecuta `1_ETL_Data_Cleaning.ipynb` antes de usar este dashboard."
)
