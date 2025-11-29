"""
Dashboard Ejecutivo - KPIs y Métricas Principales
Vista ejecutiva para jefaturas y equipo RRHH
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd


# ============================================================================
# SECCIÓN 1: CONFIGURACIÓN DE GOOGLE SHEETS
# ============================================================================

SHEET_ID = "1JqFay6hXlUuURwZFANmr6FXARZqfH7tI"
SHEET_GID = "836579878"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={SHEET_GID}"


# ============================================================================
# SECCIÓN 2: FUNCIÓN DE CARGA DE DATOS
# ============================================================================

@st.cache_data(ttl=600)
def cargar_conversaciones_desde_google_sheets():
    """Carga la hoja de consultas desde Google Sheets."""
    try:
        df = pd.read_csv(CSV_URL)
    except Exception as e:
        st.error(f"❌ Error al cargar Google Sheet: {e}")
        return pd.DataFrame()

    if df.empty:
        st.warning("El Google Sheet está vacío")
        return pd.DataFrame()

    # Renombrar columnas
    df = df.rename(
        columns={
            "Fecha": "fecha",
            "Nombre": "usuario",
            "Área": "area",
            "Consulta": "categoria",
            "Observación": "consulta",
            "Respuesta": "respuesta",
            "Estado": "estado",
        }
    )

    # Si tienen espacio al final
    if "fecha" not in df.columns and "Fecha " in df.columns:
        df = df.rename(columns={"Fecha ": "fecha", "Nombre ": "usuario"})

    if "fecha" not in df.columns:
        st.error(f"❌ La columna 'fecha' no existe. Columnas: {list(df.columns)[:5]}")
        return pd.DataFrame()

    # 🔍 DEBUG: Ver primeras 5 fechas RAW
    st.sidebar.write("🔍 Primeras fechas RAW:")
    st.sidebar.write(df["fecha"].head().tolist())
    
    # Convertir fecha con formato específico
    df["fecha"] = pd.to_datetime(df["fecha"], format="%d/%m/%Y", errors="coerce")
    
    # Si falló, intentar detección automática
    if df["fecha"].isna().all():
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    # Mostrar cuántas fechas son inválidas
    fechas_invalidas = df["fecha"].isna().sum()
    if fechas_invalidas > 0:
        st.sidebar.warning(f"⚠️ {fechas_invalidas} filas con fechas inválidas")
    
    # Eliminar filas sin fecha válida
    df = df.dropna(subset=["fecha"])

    # Agregar columnas derivadas
    if "estado" in df.columns:
        df["estado"] = df["estado"].astype(str)
        df["derivado"] = df["estado"].str.lower().str.contains("derivado", na=False)
    else:
        df["estado"] = ""
        df["derivado"] = False

    df["resuelto_primer_contacto"] = ~df["derivado"]

    if "tiempo_respuesta_mins" not in df.columns:
        df["tiempo_respuesta_mins"] = None

    if "categoria" not in df.columns:
        df["categoria"] = "Sin categoría"

    df["tema_emergente"] = False
    df["satisfaccion"] = None

    return df


# ============================================================================
# SECCIÓN 3: FUNCIONES DE CÁLCULO DE KPIs
# ============================================================================

def calcular_kpis_df(df, fecha_desde, fecha_hasta):
    """Calcular KPIs principales usando el DataFrame."""
    if df.empty or "fecha" not in df.columns:
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
    derivados = int(dff["derivado"].sum()) if total > 0 else 0
    resueltas = total - derivados

    if total > 0:
        tasa_derivacion = derivados / total * 100
        tasa_resolucion = resueltas / total * 100
    else:
        tasa_derivacion = 0.0
        tasa_resolucion = 0.0

    tasa_derivacion = max(0.0, min(100.0, tasa_derivacion))
    tasa_resolucion = max(0.0, min(100.0, tasa_resolucion))

    t = dff.get("tiempo_respuesta_mins", pd.Series(dtype=float)).dropna()
    tiempo_prom = float(t.mean()) if not t.empty else 0.0

    fecha_7d = fecha_hasta - timedelta(days=7)
    dff7 = dff[dff["fecha"] >= fecha_7d]
    temas_nuevos = dff7["categoria"].nunique()

    return {
        "total_consultas": total,
        "tasa_resolucion_primer_contacto": round(tasa_resolucion, 1),
        "tiempo_promedio_respuesta_mins": round(tiempo_prom, 1),
        "temas_emergentes_nuevos": int(temas_nuevos),
        "tasa_derivacion": round(tasa_derivacion, 1),
        "consultas_resueltas": int(resueltas),
        "consultas_derivadas": int(derivados),
    }


# ============================================================================
# SECCIÓN 4: FUNCIONES PARA GRÁFICOS
# ============================================================================

def obtener_evolucion_temporal_df(df, fecha_desde, fecha_hasta):
    """Evolución diaria de consultas en el rango."""
    if df.empty or "fecha" not in df.columns:
        return pd.DataFrame(columns=["Fecha", "Total"])

    mask = (df["fecha"] >= fecha_desde) & (df["fecha"] <= fecha_hasta)
    dff = df.loc[mask].copy()
    if dff.empty:
        return pd.DataFrame(columns=["Fecha", "Total"])

    out = (
        dff.groupby(dff["fecha"].dt.date)
        .size()
        .reset_index(name="Total")
        .rename(columns={"fecha": "Fecha"})
    )
    out["Fecha"] = pd.to_datetime(out["Fecha"])
    return out


def obtener_distribucion_areas_df(df, fecha_desde, fecha_hasta):
    """Distribución de consultas por área en el rango."""
    if df.empty or "fecha" not in df.columns:
        return pd.DataFrame(columns=["area", "total"])

    mask = (df["fecha"] >= fecha_desde) & (df["fecha"] <= fecha_hasta)
    dff = df.loc[mask].copy()
    if dff.empty or "area" not in dff.columns:
        return pd.DataFrame(columns=["area", "total"])

    dff["area"] = dff["area"].fillna("Sin Área")
    return (
        dff.groupby("area")
        .size()
        .reset_index(name="total")
        .sort_values("total", ascending=False)
    )


# ============================================================================
# SECCIÓN 5: CONFIGURACIÓN DE LA PÁGINA
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


# ============================================================================
# SECCIÓN 6: CARGA DE DATOS Y SIDEBAR
# ============================================================================

df_conversaciones = cargar_conversaciones_desde_google_sheets()

with st.sidebar:
    st.metric("📊 Filas cargadas", len(df_conversaciones))
    if not df_conversaciones.empty and "fecha" in df_conversaciones.columns:
        fecha_min = df_conversaciones["fecha"].min().date()
        fecha_max = df_conversaciones["fecha"].max().date()
        st.info(f"📅 {fecha_min} → {fecha_max}")


# ============================================================================
# SECCIÓN 7: FILTROS DE FECHA
# ============================================================================

st.markdown("---")
col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 1])

if "fecha_desde" not in st.session_state:
    st.session_state.fecha_desde = datetime(2020, 1, 1).date()
if "fecha_hasta" not in st.session_state:
    st.session_state.fecha_hasta = datetime.now().date()

with col_filtro1:
    fecha_desde_input = st.date_input("Desde", value=st.session_state.fecha_desde)

with col_filtro2:
    fecha_hasta_input = st.date_input("Hasta", value=st.session_state.fecha_hasta)

with col_filtro3:
    st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar", use_container_width=True, type="primary"):
        st.session_state.fecha_desde = fecha_desde_input
        st.session_state.fecha_hasta = fecha_hasta_input
        st.cache_data.clear()
        st.rerun()

fecha_desde = datetime.combine(st.session_state.fecha_desde, datetime.min.time())
fecha_hasta = datetime.combine(st.session_state.fecha_hasta, datetime.max.time())


# ============================================================================
# SECCIÓN 8: KPIs PRINCIPALES
# ============================================================================

kpis = calcular_kpis_df(df_conversaciones, fecha_desde, fecha_hasta)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total consultas", kpis["total_consultas"])
col2.metric("Resolución 1er contacto", f"{kpis['tasa_resolucion_primer_contacto']:.1f}%")
col3.metric("Derivadas", kpis["consultas_derivadas"], f"{kpis['tasa_derivacion']:.1f}%")
col4.metric("Temas emergentes (últ. 7d)", kpis["temas_emergentes_nuevos"])


# ============================================================================
# SECCIÓN 9: GRÁFICO DE EVOLUCIÓN TEMPORAL
# ============================================================================

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


# ============================================================================
# SECCIÓN 10: GRÁFICO DE DISTRIBUCIÓN POR ÁREA
# ============================================================================

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


# ============================================================================
# SECCIÓN 11: TABLA DETALLADA
# ============================================================================

st.markdown("### 📋 Detalle de consultas")

if not df_conversaciones.empty and "fecha" in df_conversaciones.columns:
    mask = (df_conversaciones["fecha"] >= fecha_desde) & (
        df_conversaciones["fecha"] <= fecha_hasta
    )
    df_filtrado = df_conversaciones.loc[mask].copy()
else:
    df_filtrado = pd.DataFrame()

if not df_filtrado.empty:
    columnas_tabla = [
        c
        for c in ["fecha", "usuario", "area", "categoria", "consulta", "respuesta", "estado"]
        if c in df_filtrado.columns
    ]
    st.dataframe(
        df_filtrado[columnas_tabla]
        .sort_values("fecha", ascending=False)
        .head(50),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Mostrando {min(50, len(df_filtrado))} de {len(df_filtrado)} consultas.")
else:
    st.info("No hay consultas en el rango de fechas seleccionado.")
