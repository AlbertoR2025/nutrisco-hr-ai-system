"""
Dashboard Ejecutivo - KPIs y Métricas Principales
Vista ejecutiva para jefaturas y equipo RRHH
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path

# Ruta de datos (Excel incluido en el repo)
DATA_EXCEL = Path("data") / "Consultas-Atencion-Personas-Enriquecido.xlsx"


@st.cache_data
def cargar_conversaciones_desde_excel():
    """Carga el Excel y lo normaliza a un esquema común."""
    if not DATA_EXCEL.exists():
        return pd.DataFrame()

    df = pd.read_excel(DATA_EXCEL)

    # Ajustar nombres EXACTOS a los encabezados de tu Excel
    df = df.rename(
        columns={
            "Fecha": "fecha",
            "Usuario": "usuario",
            "Área": "area",
            "Consulta": "consulta",
            "Respuesta": "respuesta",
            "Categoría": "categoria",
            "Derivado": "derivado",
            "Tiempo_Respuesta_min": "tiempo_respuesta_mins",
        }
    )

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df["derivado"] = df["derivado"].astype(bool)

    # Derivar campos equivalentes a los que usaba SQLite
    df["resuelto_primer_contacto"] = ~df["derivado"]
    df["tema_emergente"] = False
    df["satisfaccion"] = None

    return df


def calcular_kpis_df(df, fecha_desde, fecha_hasta):
    """Replica calcular_kpis pero sobre el DataFrame en memoria."""
    if df.empty:
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
    derivados = int(dff["derivado"].sum())
    resueltas = total - derivados

    if total > 0:
        tasa_derivacion = derivados / total * 100
        tasa_resolucion = resueltas / total * 100
    else:
        tasa_derivacion = 0.0
        tasa_resolucion = 0.0

    tasa_derivacion = max(0.0, min(100.0, tasa_derivacion))
    tasa_resolucion = max(0.0, min(100.0, tasa_resolucion))

    if "tiempo_respuesta_mins" in dff.columns:
        t = dff["tiempo_respuesta_mins"].dropna()
        tiempo_prom = float(t.mean()) if not t.empty else 0.0
    else:
        tiempo_prom = 0.0

    # Temas emergentes: aquí solo contamos categorías distintas en últimos 7 días
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


def obtener_top_temas_df(df, fecha_desde, fecha_hasta, limite=10):
    mask = (df["fecha"] >= fecha_desde) & (df["fecha"] <= fecha_hasta)
    dff = df.loc[mask]
    if dff.empty:
        return pd.DataFrame(columns=["categoria", "frecuencia"])
    return (
        dff.groupby("categoria")
        .size()
        .reset_index(name="frecuencia")
        .sort_values("frecuencia", ascending=False)
        .head(limite)
    )


def obtener_evolucion_temporal_df(df, periodo, fecha_desde, fecha_hasta):
    mask = (df["fecha"] >= fecha_desde) & (df["fecha"] <= fecha_hasta)
    dff = df.loc[mask].copy()
    if dff.empty:
        return pd.DataFrame(columns=["Periodo", "Total"])

    if periodo == "dia":
        dff["Periodo"] = dff["fecha"].dt.strftime("%Y-%m-%d")
        label = "Día"
    elif periodo == "semana":
        dff["Periodo"] = dff["fecha"].dt.strftime("%Y-W%W")
        label = "Semana"
    else:
        dff["Periodo"] = dff["fecha"].dt.strftime("%Y-%m")
        label = "Mes"

    out = dff.groupby("Periodo").size().reset_index(name="Total")
    out = out.rename(columns={"Periodo": label})
    return out


def obtener_distribucion_areas_df(df):
    if df.empty:
        return pd.DataFrame(columns=["area", "total"])
    dff = df.copy()
    dff["area"] = dff["area"].fillna("Sin Área")
    return (
        dff.groupby("area")
        .size()
        .reset_index(name="total")
        .sort_values("total", ascending=False)
    )


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

st.set_page_config(
    page_title="Dashboard Ejecutivo - Nutrisco",
    page_icon="📊",
    layout="wide",
)

# CSS (igual que tu código original) ...

# Header
st.markdown(
    "<h1 style='color: #f97316; text-align: center;'>📊 Dashboard Ejecutivo</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: #94a3b8; font-size: 1.1rem;'>Métricas y KPIs del Sistema de Atención a Personas</p>",
    unsafe_allow_html=True,
)

# Cargar datos
df_conversaciones = cargar_conversaciones_desde_excel()

# Filtros de fecha
st.markdown("---")
col_filtro1, col_filtro2, col_filtro3 = st.columns([2, 2, 1])

if "fecha_desde" not in st.session_state:
    st.session_state.fecha_desde = datetime.now() - timedelta(days=90)
if "fecha_hasta" not in st.session_state:
    st.session_state.fecha_hasta = datetime.now()

with col_filtro1:
    fecha_desde = st.date_input("Desde", value=st.session_state.fecha_desde)

with col_filtro2:
    fecha_hasta = st.date_input("Hasta", value=st.session_state.fecha_hasta)

with col_filtro3:
    st.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar", use_container_width=True, type="primary"):
        st.session_state.fecha_desde = fecha_desde
        st.session_state.fecha_hasta = fecha_hasta
        st.rerun()

fecha_desde = datetime.combine(st.session_state.fecha_desde, datetime.min.time())
fecha_hasta = datetime.combine(st.session_state.fecha_hasta, datetime.max.time())

# KPIs
kpis = calcular_kpis_df(df_conversaciones, fecha_desde, fecha_hasta)

# A partir de aquí puedes dejar TODO tu código original de tarjetas,
# gráficos y tabla, cambiando únicamente las llamadas:
# - db.obtener_top_temas(...)  -> obtener_top_temas_df(df_conversaciones, ...)
# - db.obtener_evolucion_temporal(...) -> obtener_evolucion_temporal_df(...)
# - db.obtener_distribucion_areas() -> obtener_distribucion_areas_df(df_conversaciones)
# - db.obtener_conversaciones(...) -> usar directamente df_conversaciones filtrado

