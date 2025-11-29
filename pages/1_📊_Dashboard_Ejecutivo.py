"""
Dashboard Ejecutivo - KPIs y Métricas Principales
Vista ejecutiva para jefaturas y equipo RRHH
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import requests
import io

# ---------------------------------------------------------
# CONFIGURACIÓN GOOGLE SHEETS SIMPLIFICADA
# ---------------------------------------------------------

@st.cache_data(ttl=300)  # Cache de 5 minutos
def cargar_datos_desde_google_sheets():
    """Carga datos desde Google Sheets usando CSV público"""
    try:
        # URL directa para exportar como CSV - FÁCIL Y SIMPLE
        SHEET_URL = "https://docs.google.com/spreadsheets/d/1JqFay6hXlUuURwZFANmr6FXARZqfH7tI/export?format=csv"
        
        st.info("📥 Cargando datos desde Google Sheets...")
        
        # Leer directamente con pandas
        df = pd.read_csv(SHEET_URL)
        
        if df.empty:
            st.warning("⚠️ El DataFrame está vacío")
            return df
            
        st.success(f"✅ Datos cargados correctamente: {len(df)} registros")
        return df
        
    except Exception as e:
        st.error(f"❌ Error cargando desde Google Sheets: {e}")
        st.info("""
        🔧 **Solución de problemas:**
        1. Verifica que tu Google Sheet esté compartido como **"Cualquier persona con el enlace puede ver"**
        2. Ve a 'Compartir' → 'Configuración de acceso general' → 'Cualquier persona con el enlace'
        3. Asegúrate de que el ID de la hoja sea correcto
        """)
        return pd.DataFrame()

def procesar_dataframe(df):
    """Procesa el DataFrame igual que tu versión original"""
    if df.empty:
        return df
    
    # Mapeo de columnas EXACTO como tenías en local
    column_mapping = {
        'Fecha ': 'fecha',
        'Nombre ': 'usuario', 
        'Área': 'area',
        'Consulta': 'categoria',
        'Observación': 'consulta',
        'Respuesta': 'respuesta',
        'Estado': 'estado'
    }
    
    # Renombrar columnas que existan
    existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
    df = df.rename(columns=existing_columns)
    
    # Procesamiento de fechas
    if 'fecha' in df.columns:
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
        df = df.dropna(subset=['fecha'])
    
    # Procesamiento de estados
    if 'estado' in df.columns:
        df['estado'] = df['estado'].astype(str)
        df['derivado'] = df['estado'].str.lower().str.contains('derivado')
        df['resuelto_primer_contacto'] = ~df['derivado']
    
    # Columnas adicionales
    if 'tiempo_respuesta_mins' not in df.columns:
        df['tiempo_respuesta_mins'] = None
    
    df['tema_emergente'] = False
    df['satisfaccion'] = None
    
    return df

# ---------------------------------------------------------
# FUNCIONES ORIGINALES DEL DASHBOARD (MANTENER)
# ---------------------------------------------------------

def calcular_kpis_df(df, fecha_desde, fecha_hasta):
    """Calcular KPIs principales usando el DataFrame."""
    if df.empty or 'fecha' not in df.columns:
        return {
            "total_consultas": 0,
            "tasa_resolucion_primer_contacto": 0.0,
            "tiempo_promedio_respuesta_mins": 0.0,
            "temas_emergentes_nuevos": 0,
            "tasa_derivacion": 0.0,
            "consultas_resueltas": 0,
            "consultas_derivadas": 0,
        }

    mask = (df["fecha"] >= fecha_desde) & (df["fecha"] <= fecha_hasta)
    dff = df.loc[mask].copy()

    total = len(dff)
    derivados = int(dff["derivado"].sum()) if 'derivado' in dff.columns else 0
    resueltas = total - derivados

    if total > 0:
        tasa_derivacion = derivados / total * 100
        tasa_resolucion = resueltas / total * 100
    else:
        tasa_derivacion = 0.0
        tasa_resolucion = 0.0

    tasa_derivacion = max(0.0, min(100.0, tasa_derivacion))
    tasa_resolucion = max(0.0, min(100.0, tasa_resolucion))

    # Tiempo de respuesta
    if "tiempo_respuesta_mins" in dff.columns:
        t = dff["tiempo_respuesta_mins"].dropna()
        tiempo_prom = float(t.mean()) if not t.empty else 0.0
    else:
        tiempo_prom = 0.0

    # Temas emergentes (últimos 7 días)
    fecha_7d = fecha_hasta - timedelta(days=7)
    dff7 = dff[dff["fecha"] >= fecha_7d]
    
    if 'categoria' in dff7.columns:
        temas_nuevos = dff7["categoria"].nunique()
    else:
        temas_nuevos = 0

    return {
        "total_consultas": total,
        "tasa_resolucion_primer_contacto": round(tasa_resolucion, 1),
        "tiempo_promedio_respuesta_mins": round(tiempo_prom, 1),
        "temas_emergentes_nuevos": int(temas_nuevos),
        "tasa_derivacion": round(tasa_derivacion, 1),
        "consultas_resueltas": int(resueltas),
        "consultas_derivadas": int(derivados),
    }

def obtener_evolucion_temporal_df(df, fecha_desde, fecha_hasta):
    """Evolución diaria de consultas en el rango."""
    if df.empty or 'fecha' not in df.columns:
        return pd.DataFrame(columns=["Fecha", "Total"])
    
    mask = (df["fecha"] >= fecha_desde) & (df["fecha"] <= fecha_hasta)
    dff = df.loc[mask].copy()
    
    if dff.empty:
        return pd.DataFrame(columns=["Fecha", "Total"])
        
    out = (
        dff.groupby(dff["fecha"].dt.date)
        .size()
        .reset_index(name="Total")
    )
    out = out.rename(columns={"fecha": "Fecha"})
    out["Fecha"] = pd.to_datetime(out["Fecha"])
    return out

def obtener_distribucion_areas_df(df, fecha_desde, fecha_hasta):
    """Distribución de consultas por área en el rango."""
    if df.empty or "fecha" not in df.columns or "area" not in df.columns:
        return pd.DataFrame(columns=["area", "total"])
        
    mask = (df["fecha"] >= fecha_desde) & (df["fecha"] <= fecha_hasta)
    dff = df.loc[mask].copy()
    
    if dff.empty:
        return pd.DataFrame(columns=["area", "total"])
        
    dff["area"] = dff["area"].fillna("Sin Área")
    return (
        dff.groupby("area")
        .size()
        .reset_index(name="total")
        .sort_values("total", ascending=False)
    )

# ---------------------------------------------------------
# INTERFAZ STREAMLIT
# ---------------------------------------------------------

def main():
    st.set_page_config(
        page_title="Dashboard Ejecutivo - Nutrisco",
        page_icon="📊",
        layout="wide",
    )

    st.markdown(
        "<h1 style='color: #f97316; text-align: center;'>📊 Dashboard Ejecutivo</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align: center; color: #94a3b8; font-size: 1.1rem;'>Métricas y KPIs del Sistema de Atención a Personas</p>",
        unsafe_allow_html=True,
    )

    # Cargar datos
    with st.spinner("🔄 Cargando datos desde Google Sheets..."):
        df_raw = cargar_datos_desde_google_sheets()
        df_conversaciones = procesar_dataframe(df_raw)

    # Mostrar información de debug si hay datos
    if not df_conversaciones.empty:
        with st.expander("🔍 Ver datos cargados (debug)"):
            st.write("**Columnas:**", list(df_conversaciones.columns))
            st.write("**Primeras filas:**", df_conversaciones.head(3))
            st.write(f"**Total de registros:** {len(df_conversaciones)}")
            if 'fecha' in df_conversaciones.columns:
                st.write(f"**Rango de fechas:** {df_conversaciones['fecha'].min()} a {df_conversaciones['fecha'].max()}")

    # Filtros de fecha
    st.markdown("---")
    col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 1])

    if "fecha_desde" not in st.session_state:
        st.session_state.fecha_desde = datetime.now() - timedelta(days=90)
    if "fecha_hasta" not in st.session_state:
        st.session_state.fecha_hasta = datetime.now()

    with col_filtro1:
        fecha_desde_input = st.date_input("Desde", value=st.session_state.fecha_desde)

    with col_filtro2:
        fecha_hasta_input = st.date_input("Hasta", value=st.session_state.fecha_hasta)

    with col_filtro3:
        st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar", use_container_width=True, type="primary"):
            st.session_state.fecha_desde = fecha_desde_input
            st.session_state.fecha_hasta = fecha_hasta_input
            st.rerun()

    fecha_desde = datetime.combine(st.session_state.fecha_desde, datetime.min.time())
    fecha_hasta = datetime.combine(st.session_state.fecha_hasta, datetime.max.time())

    # KPIs PRINCIPALES
    if not df_conversaciones.empty:
        kpis = calcular_kpis_df(df_conversaciones, fecha_desde, fecha_hasta)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total consultas", kpis["total_consultas"])
        col2.metric("Resolución 1er contacto", f"{kpis['tasa_resolucion_primer_contacto']:.1f}%")
        col3.metric("Derivadas", kpis["consultas_derivadas"], f"{kpis['tasa_derivacion']:.1f}%")
        col4.metric("Temas emergentes (últ. 7d)", kpis["temas_emergentes_nuevos"])

        # GRÁFICOS
        st.markdown("### 📈 Evolución diaria de consultas")
        df_evo = obtener_evolucion_temporal_df(df_conversaciones, fecha_desde, fecha_hasta)

        if not df_evo.empty:
            fig_evo = go.Figure()
            fig_evo.add_trace(
                go.Scatter(
                    x=df_evo["Fecha"],
                    y=df_evo["Total"],
                    mode="lines+markers",
                    line=dict(color="#f97316", width=3),
                )
            )
            fig_evo.update_layout(
                height=350,
                margin=dict(l=40, r=20, t=30, b=40),
                xaxis_title="Fecha",
                yaxis_title="Consultas",
            )
            st.plotly_chart(fig_evo, use_container_width=True)
        else:
            st.info("No hay consultas en el rango seleccionado.")

        st.markdown("### 🏢 Distribución por área")
        df_areas = obtener_distribucion_areas_df(df_conversaciones, fecha_desde, fecha_hasta)

        if not df_areas.empty:
            fig_areas = go.Figure(
                go.Bar(
                    x=df_areas["area"],
                    y=df_areas["total"],
                    marker_color="#fb923c",
                )
            )
            fig_areas.update_layout(
                height=350,
                margin=dict(l=40, r=20, t=30, b=80),
                xaxis_title="Área",
                yaxis_title="Consultas",
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig_areas, use_container_width=True)
        else:
            st.info("No hay datos de áreas para el rango seleccionado.")

        # TABLA DETALLADA
        st.markdown("### 📋 Detalle de consultas")

        mask = (df_conversaciones["fecha"] >= fecha_desde) & (
            df_conversaciones["fecha"] <= fecha_hasta
        )
        df_filtrado = df_conversaciones.loc[mask].copy()

        if not df_filtrado.empty:
            columnas_disponibles = []
            columnas_deseadas = ["fecha", "usuario", "area", "categoria", "consulta", "respuesta", "estado"]
            
            for col in columnas_deseadas:
                if col in df_filtrado.columns:
                    columnas_disponibles.append(col)
            
            st.dataframe(
                df_filtrado[columnas_disponibles].sort_values("fecha", ascending=False).head(50),
                use_container_width=True,
                hide_index=True,
            )
            st.caption(f"Mostrando {min(50, len(df_filtrado))} de {len(df_filtrado)} consultas.")
        else:
            st.info("No hay consultas en el rango de fechas seleccionado.")
            
    else:
        st.error("No hay datos disponibles para mostrar el dashboard.")

if __name__ == "__main__":
    main()
