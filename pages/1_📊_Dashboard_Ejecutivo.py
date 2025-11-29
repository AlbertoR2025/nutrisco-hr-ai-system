"""
Dashboard Ejecutivo - KPIs y Métricas Principales
Vista ejecutiva para jefaturas y equipo RRHH
"""

# =============================================
# SECCIÓN 1: IMPORTACIONES Y CONFIGURACIÓN
# =============================================

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

# =============================================
# SECCIÓN 2: CONFIGURACIÓN DE BASE DE DATOS
# =============================================

try:
    # INTENTAR USAR GOOGLE SHEETS (Streamlit Cloud)
    from utils.google_sheets_db import GoogleSheetsDatabase
    db = GoogleSheetsDatabase()
except ImportError:
    # FALLBACK A SQLite (Desarrollo Local)
    from utils.database import ChatDatabase
    db = ChatDatabase()

# =============================================
# SECCIÓN 3: CONFIGURACIÓN DE PÁGINA
# =============================================

st.set_page_config(
    page_title="Dashboard Ejecutivo - Nutrisco",
    page_icon="📊",
    layout="wide"
)

# =============================================
# SECCIÓN 4: CSS PERSONALIZADO
# =============================================

st.markdown("""
<style>
header, footer, [data-testid="stToolbar"], [data-testid="stDeployButton"],
[data-testid="stDecoration"] {
    display: none !important;
}

.stApp {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}

.metric-card {
    background: linear-gradient(135deg, #1e293b, #334155);
    padding: 1.5rem;
    border-radius: 16px;
    text-align: center;
    border: 1px solid #475569;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.metric-card h2 {
    color: #f97316;
    font-size: 2.8rem;
    margin: 0;
    font-weight: 700;
}

.metric-card p {
    color: #cbd5e1;
    margin: 0.5rem 0 0 0;
    font-size: 1.1rem;
    font-weight: 500;
}

.metric-card .meta {
    color: #64748b;
    font-size: 0.85rem;
    margin-top: 0.3rem;
}

.metric-good {
    border-left: 4px solid #10b981;
}

.metric-warning {
    border-left: 4px solid #f59e0b;
}

.metric-danger {
    border-left: 4px solid #ef4444;
}

.section-header {
    color: #f97316;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 2rem 0 1rem 0;
    border-bottom: 2px solid #475569;
    padding-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# =============================================
# SECCIÓN 5: HEADER PRINCIPAL
# =============================================

st.markdown("<h1 style='color: #f97316; text-align: center;'>📊 Dashboard Ejecutivo</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 1.1rem;'>Métricas y KPIs del Sistema de Atención a Personas</p>", unsafe_allow_html=True)

# =============================================
# SECCIÓN 6: FILTROS DE FECHA
# =============================================

st.markdown("---")
col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 1])

# Inicializar session state para fechas
if 'fecha_desde' not in st.session_state:
    st.session_state.fecha_desde = datetime.now() - timedelta(days=90)
if 'fecha_hasta' not in st.session_state:
    st.session_state.fecha_hasta = datetime.now()

with col_filtro1:
    fecha_desde = st.date_input(
        "Desde",
        value=st.session_state.fecha_desde,
        key="fecha_desde_input"
    )

with col_filtro2:
    fecha_hasta = st.date_input(
        "Hasta",
        value=st.session_state.fecha_hasta,
        key="fecha_hasta_input"
    )

with col_filtro3:
    st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar", use_container_width=True, type="primary"):
        st.session_state.fecha_desde = fecha_desde
        st.session_state.fecha_hasta = fecha_hasta
        st.rerun()

# Usar fechas del session state
fecha_desde = st.session_state.fecha_desde
fecha_hasta = st.session_state.fecha_hasta

# Convertir fechas a string para la BD
fecha_desde_str = fecha_desde.strftime("%Y-%m-%d 00:00:00")
fecha_hasta_str = fecha_hasta.strftime("%Y-%m-%d 23:59:59")

# =============================================
# SECCIÓN 7: CÁLCULO DE KPIs
# =============================================

# Calcular KPIs
kpis = db.calcular_kpis(fecha_desde=fecha_desde_str, fecha_hasta=fecha_hasta_str)

# =============================================
# SECCIÓN 8: KPIs PRINCIPALES
# =============================================

st.markdown("<div class='section-header'>🎯 KPIs Principales</div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h2>{kpis['total_consultas']}</h2>
        <p>Total Consultas</p>
        <p class="meta">Período seleccionado</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    tasa_resolucion = kpis['tasa_resolucion_primer_contacto']
    clase_meta = 'metric-good' if tasa_resolucion >= 70 else 'metric-warning' if tasa_resolucion >= 50 else 'metric-danger'
    
    st.markdown(f"""
    <div class="metric-card {clase_meta}">
        <h2>{tasa_resolucion}%</h2>
        <p>Resolución 1er Contacto</p>
        <p class="meta">Meta: ≥70%</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    tiempo_horas = kpis['tiempo_promedio_respuesta_mins'] / 60 if kpis['tiempo_promedio_respuesta_mins'] else 0
    clase_tiempo = 'metric-good' if tiempo_horas <= 24 else 'metric-warning' if tiempo_horas <= 48 else 'metric-danger'
    
    st.markdown(f"""
    <div class="metric-card {clase_tiempo}">
        <h2>{tiempo_horas:.1f}h</h2>
        <p>Tiempo Promedio Respuesta</p>
        <p class="meta">Meta: ≤24h</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <h2>{kpis['temas_emergentes_nuevos']}</h2>
        <p>Temas Emergentes</p>
        <p class="meta">Últimos 7 días</p>
    </div>
    """, unsafe_allow_html=True)

# =============================================
# SECCIÓN 9: KPIs SECUNDARIOS
# =============================================

st.markdown("<br>", unsafe_allow_html=True)
col5, col6, col7, col8 = st.columns(4)

with col5:
    st.metric(
        "Consultas Resueltas",
        f"{kpis['consultas_resueltas']}",
        delta=f"{kpis['tasa_resolucion_primer_contacto']}%"
    )

with col6:
    st.metric(
        "Consultas Derivadas",
        f"{kpis['consultas_derivadas']}",
        delta=f"-{kpis['tasa_derivacion']}%",
        delta_color="inverse"
    )

with col7:
    dias_periodo = max((fecha_hasta - fecha_desde).days, 1)
    promedio_diario = kpis['total_consultas'] / dias_periodo
    st.metric(
        "Promedio Diario",
        f"{promedio_diario:.1f}",
        delta="consultas/día"
    )

with col8:
    tasa_eficiencia = 100 - kpis['tasa_derivacion']
    st.metric(
        "Eficiencia Equipo",
        f"{tasa_eficiencia:.1f}%",
        delta="autonomía"
    )

# =============================================
# SECCIÓN 10: GRÁFICOS Y VISUALIZACIONES
# =============================================

st.markdown("<div class='section-header'>📈 Análisis Visual</div>", unsafe_allow_html=True)

# Fila 1: Top Temas + Evolución Temporal
col_g1, col_g2 = st.columns([1, 1])

with col_g1:
    st.markdown("#### 🔝 Top 10 Temas Más Recurrentes")
    
    df_temas = db.obtener_top_temas(limite=10, fecha_desde=fecha_desde_str, fecha_hasta=fecha_hasta_str)
    
    if not df_temas.empty:
        fig_temas = go.Figure()
        
        fig_temas.add_trace(go.Bar(
            x=df_temas['frecuencia'],
            y=df_temas['categoria'],
            orientation='h',
            marker=dict(
                color=df_temas['frecuencia'],
                colorscale='Oranges',
                showscale=False
            ),
            text=df_temas['frecuencia'],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Frecuencia: %{x}<extra></extra>'
        ))
        
        fig_temas.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            height=400,
            margin=dict(l=150, r=50, t=20, b=50),
            xaxis=dict(
                showgrid=True,
                gridcolor='#334155',
                title='Cantidad de Consultas'
            ),
            yaxis=dict(
                showgrid=False,
                categoryorder='total ascending'
            )
        )
        
        st.plotly_chart(fig_temas, use_container_width=True)
    else:
        st.info("No hay datos para el período seleccionado")

with col_g2:
    st.markdown("#### 📅 Evolución Temporal de Consultas")
    
    df_evolucion = db.obtener_evolucion_temporal(
        periodo='dia',
        fecha_desde=fecha_desde_str,
        fecha_hasta=fecha_hasta_str
    )
    
    if not df_evolucion.empty:
        fig_evolucion = go.Figure()
        
        fig_evolucion.add_trace(go.Scatter(
            x=df_evolucion.iloc[:, 0],
            y=df_evolucion['Total'],
            mode='lines+markers',
            name='Consultas',
            line=dict(color='#f97316', width=3),
            marker=dict(size=8, color='#ea580c'),
            fill='tozeroy',
            fillcolor='rgba(249, 115, 22, 0.2)',
            hovertemplate='<b>%{x}</b><br>Consultas: %{y}<extra></extra>'
        ))
        
        # Línea de promedio
        if len(df_evolucion) > 0:
            promedio = df_evolucion['Total'].mean()
            fig_evolucion.add_hline(
                y=promedio,
                line_dash="dash",
                line_color="#10b981",
                annotation_text=f"Promedio: {promedio:.1f}",
                annotation_position="right"
            )
        
        fig_evolucion.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            height=400,
            margin=dict(l=50, r=50, t=20, b=50),
            xaxis=dict(
                showgrid=True,
                gridcolor='#334155',
                title='Fecha'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#334155',
                title='Cantidad de Consultas'
            ),
            showlegend=False
        )
        
        st.plotly_chart(fig_evolucion, use_container_width=True)
    else:
        st.info("No hay datos para el período seleccionado")

# Fila 2: Volumen Semanal + Distribución por Área
col_g3, col_g4 = st.columns([1, 1])

with col_g3:
    st.markdown("#### 📊 Volumen por Semana")
    
    df_semanas = db.obtener_evolucion_temporal(
        periodo='semana',
        fecha_desde=fecha_desde_str,
        fecha_hasta=fecha_hasta_str
    )
    
    if not df_semanas.empty:
        fig_semanas = go.Figure()
        
        fig_semanas.add_trace(go.Bar(
            x=df_semanas.iloc[:, 0],
            y=df_semanas['Total'],
            marker=dict(
                color=df_semanas['Total'],
                colorscale='Oranges',
                showscale=False
            ),
            text=df_semanas['Total'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Consultas: %{y}<extra></extra>'
        ))
        
        fig_semanas.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            height=400,
            margin=dict(l=50, r=50, t=20, b=50),
            xaxis=dict(
                showgrid=False,
                title='Semana'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#334155',
                title='Cantidad de Consultas'
            )
        )
        
        st.plotly_chart(fig_semanas, use_container_width=True)
    else:
        st.info("No hay datos para el período seleccionado")

with col_g4:
    st.markdown("#### 🏢 Distribución por Área")
    
    df_areas = db.obtener_distribucion_areas()
    
    if not df_areas.empty:
        # Filtrar solo las áreas con más consultas (top 8)
        df_areas_top = df_areas.head(8)
        otros = df_areas['total'].iloc[8:].sum() if len(df_areas) > 8 else 0
        
        if otros > 0:
            df_areas_top = pd.concat([
                df_areas_top,
                pd.DataFrame({'area': ['Otras'], 'total': [otros]})
            ])
        
        fig_areas = go.Figure()
        
        fig_areas.add_trace(go.Pie(
            labels=df_areas_top['area'],
            values=df_areas_top['total'],
            hole=0.4,
            marker=dict(
                colors=px.colors.sequential.Oranges,
                line=dict(color='#0f172a', width=2)
            ),
            textinfo='label+percent',
            textposition='outside',
            hovertemplate='<b>%{label}</b><br>Consultas: %{value}<br>%{percent}<extra></extra>'
        ))
        
        fig_areas.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1', size=11),
            height=400,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.05
            )
        )
        
        st.plotly_chart(fig_areas, use_container_width=True)
    else:
        st.info("No hay datos de áreas disponibles")

# =============================================
# SECCIÓN 11: TABLA DE RESUMEN DETALLADO
# =============================================

st.markdown("<div class='section-header'>📋 Resumen Detallado</div>", unsafe_allow_html=True)

df_resumen = db.obtener_conversaciones(limite=500)

if not df_resumen.empty:
    # Filtrar por fechas
    df_resumen['fecha'] = pd.to_datetime(df_resumen['fecha'])
    df_resumen_filtrado = df_resumen[
        (df_resumen['fecha'].dt.normalize() >= pd.Timestamp(fecha_desde)) &
        (df_resumen['fecha'].dt.normalize() <= pd.Timestamp(fecha_hasta))
    ]
    
    if not df_resumen_filtrado.empty:
        st.dataframe(
            df_resumen_filtrado[['fecha', 'usuario', 'categoria', 'area', 'resuelto_primer_contacto', 'derivado']].head(20),
            use_container_width=True,
            hide_index=True
        )
        
        st.caption(f"Mostrando las últimas 20 de {len(df_resumen_filtrado)} consultas en el período")
    else:
        st.info("No hay consultas en el rango de fechas seleccionado")
else:
    st.info("No hay datos disponibles")

# =============================================
# SECCIÓN 12: FOOTER
# =============================================

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748b;'>Dashboard actualizado en tiempo real • Nutrisco © 2025</p>", unsafe_allow_html=True)
