"""
Dashboard Ejecutivo con ETL automático integrado
ETL se ejecuta en Streamlit Cloud automáticamente
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import re

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

SHEET_ID = "1JqFay6hXlUuURwZFANmr6FXARZqfH7tI"
SHEET_GID = "836579878"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={SHEET_GID}"


# ============================================================================
# FUNCIONES ETL
# ============================================================================

def limpiar_fecha(fecha_raw):
    """Parsea fechas en múltiples formatos robustamente"""
    if pd.isna(fecha_raw):
        return pd.NaT
    
    # Si es número (serial de Excel/Sheets)
    if isinstance(fecha_raw, (int, float)):
        try:
            return pd.Timestamp('1899-12-30') + pd.Timedelta(days=int(fecha_raw))
        except:
            return pd.NaT
    
    fecha_str = str(fecha_raw).strip()
    
    # Probar formatos comunes
    formatos = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d",
        "%d/%m/%y", "%d-%m-%y", "%m/%d/%Y", "%m-%d-%Y"
    ]
    
    for formato in formatos:
        try:
            return pd.to_datetime(fecha_str, format=formato)
        except:
            continue
    
    # Último intento con detección automática
    try:
        return pd.to_datetime(fecha_str, dayfirst=True)
    except:
        return pd.NaT


def categorizar_estado(estado):
    """Normaliza estados"""
    if pd.isna(estado):
        return "Sin Estado"
    
    estado_lower = str(estado).lower()
    
    if any(x in estado_lower for x in ["derivad", "escalad"]):
        return "Derivado"
    elif any(x in estado_lower for x in ["resuel", "cerrad", "completad"]):
        return "Resuelto"
    elif any(x in estado_lower for x in ["pendiente", "proceso", "abierto"]):
        return "Pendiente"
    else:
        return "Otro"


def normalizar_area(area):
    """Estandariza nombres de áreas"""
    if pd.isna(area):
        return "Sin Área"
    
    area_str = str(area).strip()
    
    # Mapeo de áreas (ajusta según tu organización)
    mapeo = {
        "rrhh": "RRHH",
        "recursos humanos": "RRHH",
        "ti": "TI",
        "tecnologia": "TI",
        "sistemas": "TI",
        "finanzas": "Finanzas",
        "contabilidad": "Finanzas",
        "operaciones": "Operaciones",
        "ops": "Operaciones",
        "produccion": "Producción",
    }
    
    area_lower = area_str.lower()
    for key, value in mapeo.items():
        if key in area_lower:
            return value
    
    return area_str


@st.cache_data(ttl=600)  # Cache por 10 minutos
def ejecutar_etl():
    """
    ETL completo: Extrae de Google Sheets, limpia y transforma
    Se ejecuta automáticamente en Streamlit Cloud
    """
    with st.spinner("🔄 Cargando y limpiando datos..."):
        
        # EXTRACT
        try:
            df = pd.read_csv(CSV_URL)
        except Exception as e:
            st.error(f"❌ Error al extraer datos: {e}")
            return pd.DataFrame()
        
        if df.empty:
            st.warning("⚠️ Google Sheet está vacío")
            return pd.DataFrame()
        
        # TRANSFORM
        
        # 1. Renombrar columnas
        mapeo_cols = {
            "Fecha": "fecha_raw",
            "Nombre": "usuario",
            "Área": "area_raw",
            "Consulta": "categoria",
            "Observación": "consulta",
            "Respuesta": "respuesta",
            "Estado": "estado_raw",
        }
        df = df.rename(columns=mapeo_cols)
        
        # 2. Limpiar fechas
        if "fecha_raw" not in df.columns:
            st.error("❌ No se encontró columna 'Fecha' en el Sheet")
            return pd.DataFrame()
        
        df["fecha"] = df["fecha_raw"].apply(limpiar_fecha)
        
        # Mostrar diagnóstico solo si hay problemas
        fechas_invalidas = df["fecha"].isna().sum()
        if fechas_invalidas > 0:
            st.sidebar.warning(f"⚠️ {fechas_invalidas} fechas inválidas ignoradas")
        
        # Eliminar filas sin fecha
        df = df.dropna(subset=["fecha"])
        
        if df.empty:
            st.error("❌ No hay fechas válidas en los datos")
            return pd.DataFrame()
        
        # 3. Normalizar textos
        for col in ["usuario", "categoria", "consulta", "respuesta"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()
        
        # 4. Categorizar estado
        if "estado_raw" in df.columns:
            df["estado"] = df["estado_raw"].apply(categorizar_estado)
        else:
            df["estado"] = "Sin Estado"
        
        # 5. Normalizar áreas
        if "area_raw" in df.columns:
            df["area"] = df["area_raw"].apply(normalizar_area)
        else:
            df["area"] = "Sin Área"
        
        # 6. Columnas derivadas
        df["derivado"] = df["estado"] == "Derivado"
        df["resuelto"] = df["estado"] == "Resuelto"
        
        # 7. Metadata temporal
        df["año"] = df["fecha"].dt.year
        df["mes"] = df["fecha"].dt.month
        df["mes_nombre"] = df["fecha"].dt.month_name()
        df["dia_semana"] = df["fecha"].dt.day_name()
        df["trimestre"] = df["fecha"].dt.quarter
        
        # 8. Ordenar
        df = df.sort_values("fecha")
        
        return df


# ============================================================================
# FUNCIONES DE ANÁLISIS
# ============================================================================

def calcular_kpis(df, fecha_desde, fecha_hasta):
    """Calcula KPIs del periodo"""
    if df.empty:
        return {
            "total_consultas": 0,
            "tasa_resolucion": 0.0,
            "tasa_derivacion": 0.0,
            "consultas_resueltas": 0,
            "consultas_derivadas": 0,
            "temas_emergentes": 0,
        }

    mask = (df["fecha"] >= fecha_desde) & (df["fecha"] <= fecha_hasta)
    dff = df.loc[mask].copy()

    total = len(dff)
    derivados = int(dff["derivado"].sum())
    resueltas = int(dff["resuelto"].sum())

    tasa_derivacion = (derivados / total * 100) if total > 0 else 0.0
    tasa_resolucion = (resueltas / total * 100) if total > 0 else 0.0

    # Temas emergentes últimos 7 días
    fecha_7d = fecha_hasta - timedelta(days=7)
    temas_nuevos = dff[dff["fecha"] >= fecha_7d]["categoria"].nunique()

    return {
        "total_consultas": total,
        "tasa_resolucion": round(tasa_resolucion, 1),
        "tasa_derivacion": round(tasa_derivacion, 1),
        "consultas_resueltas": resueltas,
        "consultas_derivadas": derivados,
        "temas_emergentes": temas_nuevos,
    }


def obtener_evolucion_temporal(df, fecha_desde, fecha_hasta):
    """Evolución diaria de consultas"""
    if df.empty:
        return pd.DataFrame(columns=["Fecha", "Total"])

    mask = (df["fecha"] >= fecha_desde) & (df["fecha"] <= fecha_hasta)
    dff = df.loc[mask].copy()
    
    if dff.empty:
        return pd.DataFrame(columns=["Fecha", "Total"])

    resultado = (
        dff.groupby(dff["fecha"].dt.date)
        .size()
        .reset_index(name="Total")
        .rename(columns={"fecha": "Fecha"})
    )
    resultado["Fecha"] = pd.to_datetime(resultado["Fecha"])
    
    return resultado


def obtener_distribucion_areas(df, fecha_desde, fecha_hasta):
    """Distribución por área"""
    if df.empty:
        return pd.DataFrame(columns=["area", "total"])

    mask = (df["fecha"] >= fecha_desde) & (df["fecha"] <= fecha_hasta)
    dff = df.loc[mask].copy()
    
    if dff.empty:
        return pd.DataFrame(columns=["area", "total"])

    return (
        dff.groupby("area")
        .size()
        .reset_index(name="total")
        .sort_values("total", ascending=False)
    )


# ============================================================================
# INTERFAZ DE USUARIO
# ============================================================================

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

# Ejecutar ETL (se cachea automáticamente)
df = ejecutar_etl()

# Sidebar con info
with st.sidebar:
    if not df.empty:
        st.metric("📊 Registros totales", len(df))
        st.info(f"📅 {df['fecha'].min().date()} → {df['fecha'].max().date()}")
        
        # Botón para forzar recarga
        if st.button("🔄 Recargar datos", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    else:
        st.warning("⚠️ No hay datos disponibles")

# Si no hay datos, mostrar error y salir
if df.empty:
    st.error("❌ No se pudieron cargar los datos. Verifica el Google Sheet.")
    st.stop()

# Filtros de fecha
st.markdown("---")
col1, col2, col3 = st.columns([2, 2, 1])

if "fecha_desde" not in st.session_state:
    st.session_state.fecha_desde = df["fecha"].min().date()
if "fecha_hasta" not in st.session_state:
    st.session_state.fecha_hasta = df["fecha"].max().date()

with col1:
    desde = st.date_input("Desde", value=st.session_state.fecha_desde)
with col2:
    hasta = st.date_input("Hasta", value=st.session_state.fecha_hasta)
with col3:
    st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar", type="primary", use_container_width=True):
        st.session_state.fecha_desde = desde
        st.session_state.fecha_hasta = hasta
        st.rerun()

fecha_desde = datetime.combine(st.session_state.fecha_desde, datetime.min.time())
fecha_hasta = datetime.combine(st.session_state.fecha_hasta, datetime.max.time())

# KPIs principales
kpis = calcular_kpis(df, fecha_desde, fecha_hasta)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total consultas", kpis["total_consultas"])
col2.metric("Resolución 1er contacto", f"{kpis['tasa_resolucion']:.1f}%")
col3.metric("Derivadas", kpis["consultas_derivadas"], f"{kpis['tasa_derivacion']:.1f}%")
col4.metric("Temas emergentes (7d)", kpis["temas_emergentes"])

# Gráfico de evolución
st.markdown("### 📈 Evolución diaria de consultas")
df_evo = obtener_evolucion_temporal(df, fecha_desde, fecha_hasta)

if not df_evo.empty:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_evo["Fecha"],
            y=df_evo["Total"],
            mode="lines+markers",
            line=dict(color="#f97316", width=3),
            marker=dict(size=8),
        )
    )
    fig.update_layout(
        height=350,
        margin=dict(l=40, r=20, t=30, b=40),
        xaxis_title="Fecha",
        yaxis_title="Consultas",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay consultas en el rango seleccionado")

# Gráfico de áreas
st.markdown("### 🏢 Distribución por área")
df_areas = obtener_distribucion_areas(df, fecha_desde, fecha_hasta)

if not df_areas.empty:
    fig_areas = go.Figure(
        go.Bar(
            x=df_areas["area"],
            y=df_areas["total"],
            marker_color="#fb923c",
            text=df_areas["total"],
            textposition="outside",
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
    st.info("No hay datos de áreas para el rango seleccionado")

# Tabla detallada
st.markdown("### 📋 Detalle de consultas")

mask = (df["fecha"] >= fecha_desde) & (df["fecha"] <= fecha_hasta)
df_filtrado = df.loc[mask].copy()

if not df_filtrado.empty:
    columnas_mostrar = ["fecha", "usuario", "area", "categoria", "estado", "consulta"]
    columnas_disponibles = [c for c in columnas_mostrar if c in df_filtrado.columns]
    
    st.dataframe(
        df_filtrado[columnas_disponibles]
        .sort_values("fecha", ascending=False)
        .head(100),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Mostrando las últimas 100 de {len(df_filtrado)} consultas en el periodo")
else:
    st.info("No hay consultas en el rango de fechas seleccionado")
