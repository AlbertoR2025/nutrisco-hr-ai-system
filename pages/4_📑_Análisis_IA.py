"""
Análisis con IA - Detección de Temas Emergentes y Resúmenes
Análisis inteligente para identificar patrones y tendencias
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from utils.database import ChatDatabase

# Configuración de página
st.set_page_config(
    page_title="Análisis IA - Nutrisco",
    page_icon="📑",
    layout="wide"
)

# CSS personalizado
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
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    padding: 2rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 2rem;
    text-align: center;
}

.tema-emergente {
    background: linear-gradient(135deg, #dc2626, #ea580c);
    padding: 1.5rem;
    border-radius: 12px;
    color: white;
    margin-bottom: 1rem;
    border-left: 5px solid #fbbf24;
}

.tema-emergente h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.3rem;
}

.insight-box {
    background: #1e293b;
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 4px solid #10b981;
    margin-bottom: 1rem;
}

.insight-box h4 {
    color: #10b981;
    margin: 0 0 0.5rem 0;
}

.recomendacion {
    background: rgba(99, 102, 241, 0.1);
    padding: 1rem;
    border-radius: 8px;
    border-left: 3px solid #6366f1;
    margin: 0.5rem 0;
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

# Inicializar base de datos
db = ChatDatabase()

# Tabs principales
tab1, tab2, tab3 = st.tabs([
    "🔥 Temas Emergentes",
    "📊 Resumen Ejecutivo",
    "💡 Recomendaciones"
])

# TAB 1: TEMAS EMERGENTES
with tab1:
    st.markdown("### 🔥 Detección de Temas Emergentes")
    st.markdown("Identificación automática de temas que han aumentado su frecuencia recientemente")
    
    col_t1, col_t2, col_t3 = st.columns(3)
    
    with col_t1:
        dias_analisis = st.selectbox(
            "Período de análisis",
            [7, 14, 30, 60],
            format_func=lambda x: f"Últimos {x} días"
        )
    
    with col_t2:
        umbral_frecuencia = st.number_input(
            "Umbral de frecuencia",
            min_value=3,
            max_value=50,
            value=5,
            help="Cantidad mínima de menciones para considerar un tema como emergente"
        )
    
    with col_t3:
        if st.button("🔍 Analizar", use_container_width=True, type="primary"):
            st.rerun()
    
    # Detectar temas emergentes
    df_emergentes = db.detectar_temas_emergentes(
        umbral_frecuencia=umbral_frecuencia,
        dias_recientes=dias_analisis
    )
    
    if not df_emergentes.empty:
        st.markdown(f"#### 🎯 {len(df_emergentes)} Temas Emergentes Detectados")
        
        # Mostrar cada tema emergente
        for idx, row in df_emergentes.iterrows():
            porcentaje = (row['frecuencia_reciente'] / df_emergentes['frecuencia_reciente'].sum()) * 100
            
            st.markdown(f"""
            <div class="tema-emergente">
                <h3>🔥 {row['categoria']}</h3>
                <p><strong>Frecuencia:</strong> {row['frecuencia_reciente']} menciones ({porcentaje:.1f}% del total)</p>
                <p><strong>Período:</strong> Últimos {dias_analisis} días</p>
                <p><strong>Recomendación:</strong> Considerar crear FAQ o material de apoyo específico</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Gráfico de temas emergentes
        st.markdown("#### 📊 Visualización")
        
        fig_emergentes = go.Figure()
        
        fig_emergentes.add_trace(go.Bar(
            x=df_emergentes['categoria'],
            y=df_emergentes['frecuencia_reciente'],
            marker=dict(
                color=df_emergentes['frecuencia_reciente'],
                colorscale='Reds',
                showscale=False
            ),
            text=df_emergentes['frecuencia_reciente'],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Menciones: %{y}<extra></extra>'
        ))
        
        fig_emergentes.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            height=400,
            xaxis=dict(
                showgrid=False,
                title='Tema'
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#334155',
                title='Frecuencia'
            )
        )
        
        st.plotly_chart(fig_emergentes, use_container_width=True)
        
    else:
        st.info(f"No se detectaron temas emergentes con más de {umbral_frecuencia} menciones en los últimos {dias_analisis} días.")

# TAB 2: RESUMEN EJECUTIVO
with tab2:
    st.markdown("### 📊 Resumen Ejecutivo")
    
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        periodo_resumen = st.selectbox(
            "Período",
            ["Última semana", "Último mes", "Últimos 3 meses", "Último año"]
        )
    
    with col_r2:
        if st.button("📄 Generar Resumen", use_container_width=True, type="primary"):
            st.rerun()
    
    # Calcular fechas según período
    if periodo_resumen == "Última semana":
        fecha_desde = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        dias = 7
    elif periodo_resumen == "Último mes":
        fecha_desde = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        dias = 30
    elif periodo_resumen == "Últimos 3 meses":
        fecha_desde = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        dias = 90
    else:
        fecha_desde = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        dias = 365
    
    fecha_hasta = datetime.now().strftime("%Y-%m-%d")
    
    # Obtener KPIs del período
    kpis = db.calcular_kpis(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    
    # Métricas del período
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    
    with col_m1:
        st.metric("Total Consultas", kpis['total_consultas'])
    
    with col_m2:
        st.metric("Resolución 1er Contacto", f"{kpis['tasa_resolucion_primer_contacto']}%")
    
    with col_m3:
        st.metric("Tiempo Promedio", f"{kpis['tiempo_promedio_respuesta_mins']/60:.1f}h")
    
    with col_m4:
        st.metric("Consultas Derivadas", kpis['consultas_derivadas'])
    
    # Insights automáticos
    st.markdown("#### 💡 Insights Clave")
    
    # Insight 1: Volumen
    promedio_diario = kpis['total_consultas'] / dias
    st.markdown(f"""
    <div class="insight-box">
        <h4>📈 Volumen de Consultas</h4>
        <p>Se recibieron <strong>{kpis['total_consultas']} consultas</strong> en los últimos {dias} días, 
        con un promedio de <strong>{promedio_diario:.1f} consultas diarias</strong>.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Insight 2: Eficiencia
    if kpis['tasa_resolucion_primer_contacto'] >= 70:
        estado_resolucion = "✅ Excelente"
        color = "#10b981"
    elif kpis['tasa_resolucion_primer_contacto'] >= 50:
        estado_resolucion = "⚠️ Bueno"
        color = "#f59e0b"
    else:
        estado_resolucion = "❌ Mejorable"
        color = "#ef4444"
    
    st.markdown(f"""
    <div class="insight-box">
        <h4>🎯 Eficiencia de Resolución</h4>
        <p>El chatbot resuelve <strong>{kpis['tasa_resolucion_primer_contacto']}%</strong> de las consultas 
        en el primer contacto. Estado: <strong style="color: {color};">{estado_resolucion}</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Insight 3: Tiempo de respuesta
    tiempo_horas = kpis['tiempo_promedio_respuesta_mins'] / 60
    if tiempo_horas <= 24:
        estado_tiempo = "✅ Dentro de meta"
    else:
        estado_tiempo = "⚠️ Supera meta de 24h"
    
    st.markdown(f"""
    <div class="insight-box">
        <h4>⏱️ Tiempo de Respuesta</h4>
        <p>Tiempo promedio de respuesta: <strong>{tiempo_horas:.1f} horas</strong>. {estado_tiempo}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Top temas del período
    st.markdown("#### 🔝 Temas Más Consultados")
    
    df_top_temas = db.obtener_top_temas(limite=5, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
    
    if not df_top_temas.empty:
        fig_top = go.Figure()
        
        fig_top.add_trace(go.Pie(
            labels=df_top_temas['categoria'],
            values=df_top_temas['frecuencia'],
            hole=0.4,
            marker=dict(
                colors=px.colors.sequential.Oranges
            ),
            textinfo='label+percent',
            textposition='outside'
        ))
        
        fig_top.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#cbd5e1'),
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig_top, use_container_width=True)

# TAB 3: RECOMENDACIONES
with tab3:
    st.markdown("### 💡 Recomendaciones Inteligentes")
    st.markdown("Sugerencias basadas en el análisis de datos y patrones detectados")
    
    # Obtener datos para recomendaciones
    kpis_rec = db.calcular_kpis()
    df_emergentes_rec = db.detectar_temas_emergentes(umbral_frecuencia=5, dias_recientes=7)
    
    # Recomendación 1: Mejorar resolución
    if kpis_rec['tasa_resolucion_primer_contacto'] < 70:
        st.markdown("""
        <div class="recomendacion">
            <h4>🎯 Mejorar Tasa de Resolución</h4>
            <p><strong>Situación actual:</strong> {:.1f}% de resolución en primer contacto</p>
            <p><strong>Meta:</strong> ≥70%</p>
            <p><strong>Acciones sugeridas:</strong></p>
            <ul>
                <li>Revisar y actualizar FAQs del chatbot</li>
                <li>Entrenar el modelo con más ejemplos reales</li>
                <li>Agregar respuestas predefinidas para temas recurrentes</li>
            </ul>
        </div>
        """.format(kpis_rec['tasa_resolucion_primer_contacto']), unsafe_allow_html=True)
    
    # Recomendación 2: Crear FAQs para temas emergentes
    if not df_emergentes_rec.empty:
        temas_lista = ", ".join(df_emergentes_rec['categoria'].head(3).tolist())
        st.markdown(f"""
        <div class="recomendacion">
            <h4>📚 Crear Material de Apoyo</h4>
            <p><strong>Temas emergentes detectados:</strong> {temas_lista}</p>
            <p><strong>Acciones sugeridas:</strong></p>
            <ul>
                <li>Crear documentos o videos explicativos</li>
                <li>Actualizar la base de conocimiento del chatbot</li>
                <li>Considerar sesiones informativas para empleados</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Recomendación 3: Reducir tiempo de respuesta
    if kpis_rec['tiempo_promedio_respuesta_mins'] > 1440:  # Más de 24h
        st.markdown(f"""
        <div class="recomendacion">
            <h4>⚡ Reducir Tiempo de Respuesta</h4>
            <p><strong>Tiempo actual:</strong> {kpis_rec['tiempo_promedio_respuesta_mins']/60:.1f} horas</p>
            <p><strong>Meta:</strong> ≤24 horas</p>
            <p><strong>Acciones sugeridas:</strong></p>
            <ul>
                <li>Implementar respuestas automáticas para casos simples</li>
                <li>Revisar carga de trabajo del equipo</li>
                <li>Priorizar consultas urgentes automáticamente</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Recomendación 4: Análisis de patrones
    st.markdown("""
    <div class="recomendacion">
        <h4>🔍 Análisis Continuo</h4>
        <p><strong>Recomendaciones generales:</strong></p>
        <ul>
            <li>Revisar este dashboard semanalmente</li>
            <li>Monitorear temas emergentes constantemente</li>
            <li>Actualizar el sistema con feedback real de empleados</li>
            <li>Capacitar al equipo en nuevos procesos detectados</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Exportar recomendaciones
    st.markdown("---")
    
    if st.button("📥 Exportar Reporte Completo", use_container_width=True):
        # Crear reporte en texto
        reporte = f"""
REPORTE DE ANÁLISIS IA - SISTEMA RRHH NUTRISCO
Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}

KPIs PRINCIPALES:
- Total Consultas: {kpis_rec['total_consultas']}
- Resolución 1er Contacto: {kpis_rec['tasa_resolucion_primer_contacto']}%
- Tiempo Promedio: {kpis_rec['tiempo_promedio_respuesta_mins']/60:.1f}h
- Temas Emergentes: {kpis_rec['temas_emergentes_nuevos']}

TEMAS EMERGENTES DETECTADOS:
{df_emergentes_rec.to_string() if not df_emergentes_rec.empty else 'Ninguno'}

RECOMENDACIONES:
1. Mejorar tasa de resolución a ≥70%
2. Crear FAQs para temas emergentes
3. Mantener tiempo de respuesta <24h
4. Análisis continuo semanal
        """
        
        st.download_button(
            label="💾 Descargar Reporte (.txt)",
            data=reporte,
            file_name=f"reporte_ia_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748b;'>Análisis con IA • Nutrisco © 2025</p>", unsafe_allow_html=True)
