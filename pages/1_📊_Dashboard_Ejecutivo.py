"""
📊 Dashboard Ejecutivo - Nutrisco
Métricas y KPIs del Sistema de Atención a Personas
Lee datos desde Google Sheets (CSV público), normaliza columnas y fechas.
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

# ============================================================================
# CONFIGURACIÓN GOOGLE SHEETS
# ============================================================================

SHEET_ID = "1JqFay6hXlUuURwZFANmr6FXARZqfH7tI"
SHEET_GID = "836579878"

# CSV público del Sheet (asegúrate que el sheet está compartido como
# “Cualquiera con el enlace puede ver”)
CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?"
    f"tqx=out:csv&gid={SHEET_GID}"
)

# ============================================================================
# FUNCIONES ETL
# ============================================================================

def limpiar_fecha(fecha_raw):
    """Parsea fechas de forma robusta desde Google Sheets."""
    if pd.isna(fecha_raw):
        return pd.NaT

    # Números seriales Excel/Sheets
    if isinstance(fecha_raw, (int, float)):
        try:
            return pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(fecha_raw))
        except Exception:
            return pd.NaT

    s = str(fecha_raw).strip()

    formatos = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%y",
        "%d-%m-%y",
        "%m/%d/%Y",
        "%m-%d-%Y",
    ]

    for fmt in formatos:
        try:
            return pd.to_datetime(s, format=fmt)
        except Exception:
            continue

    # Último intento automático
    try:
        return pd.to_datetime(s, dayfirst=True)
    except Exception:
        return pd.NaT


def categorizar_estado(estado_raw):
    """Normaliza el estado de la consulta."""
    if pd.isna(estado_raw):
        return "Sin Estado"

    s = str(estado_raw).lower()

    if "deriv" in s or "escala" in s:
        return "Derivado"
    if "resuel" in s or "cerrad" in s or "complet" in s:
        return "Resuelto"
    if "pend" in s or "proceso" in s or "abiert" in s:
        return "Pendiente"
    return "Otro"


def normalizar_area(area_raw):
    """Normaliza nombres de áreas."""
    if pd.isna(area_raw):
        return "Sin Área"

    s = str(area_raw).strip()
    s_lower = s.lower()

    mapeo = {
        "rrhh": "RRHH",
        "recursos humanos": "RRHH",
        "ti": "TI",
        "tecnolog": "TI",
        "sistema": "TI",
        "finanza": "Finanzas",
        "contab": "Finanzas",
        "operacion": "Operaciones",
        "ops": "Operaciones",
        "producci": "Producción",
    }

    for key, value in mapeo.items():
        if key in s_lower:
            return value

    return s


@st.cache_data(ttl=600)
def cargar_y_transformar_datos():
    """
    ETL completo:
    - Lee CSV desde Google Sheets
    - Normaliza nombres de columnas
    - Limpia fechas y campos de texto
    - Genera columnas derivadas
    """
    try:
        df = pd.read_csv(CSV_URL)
    except Exception as e:
        st.error(f"❌ Error al cargar Google Sheet: {e}")
        return pd.DataFrame()

    if df.empty:
        st.warning("⚠️ El Google Sheet está vacío.")
        return pd.DataFrame()

    # 1) Normalizar nombres de columnas (strip + lower)
    columnas_originales = df.columns.tolist()
    df.columns = [c.strip().lower() for c in df.columns]

    # 2) Mapear a nombres internos estándar
    # Ajusta los keys según cómo estén EXACTAMENTE en tu Sheet (en minúsculas)
    mapeo_columnas = {
        "fecha": "fecha_raw",
        "nombre": "usuario",
        "área": "area_raw",
        "area": "area_raw",
        "consulta": "categoria",
        "observación": "consulta",
        "observacion": "consulta",
        "respuesta": "respuesta",
        "estado": "estado_raw",
    }

    df = df.rename(columns=mapeo_columnas)

    # Debug opcional: ver columnas detectadas
    st.sidebar.write("Columnas detectadas (normalizadas):")
    st.sidebar.write(df.columns.tolist())

    # 3) Validar que haya columna de fecha
    if "fecha_raw" not in df.columns:
        st.error("❌ No se encontró ninguna columna de fecha ('Fecha'). "
                 "Revisa el Google Sheet y que la columna se llame 'Fecha'.")
        return pd.DataFrame()

    # 4) Limpiar fechas
    df["fecha"] = df["fecha_raw"].apply(limpiar_fecha)
    fechas_invalidas = df["fecha"].isna().sum()
    if fechas_invalidas > 0:
        st.sidebar.warning(f"⚠️ {fechas_invalidas} filas con fecha inválida serán ignoradas.")
    df = df.dropna(subset=["fecha"])

    if df.empty:
        st.error("❌ Todas las filas quedaron sin fecha válida después de limpiar.")
        return pd.DataFrame()

    # 5) Limpiar textos
    for col in ["usuario", "categoria", "consulta", "respuesta"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    # 6) Normalizar estado
    if "estado_raw" in df.columns:
        df["estado"] = df["estado_raw"].apply(categorizar_estado)
    else:
        df["estado"] = "Sin Estado"

    # 7) Normalizar área
    if "area_raw" in df.columns:
        df["area"] = df["area_raw"].apply(normalizar_area)
    else:
        df["area"] = "Sin Área"

    # 8) Columnas derivadas
    df["derivado"] = df["estado"] == "Derivado"
    df["resuelto"] = df["estado"] == "Resuelto"

    # 9) Metadatos de fecha
    df["año"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["mes_nombre"] = df["fecha"].dt.month_name()
    df["dia_semana"] = df["fecha"].dt.day_name()
    df["trimestre"] = df["fecha"].dt.quarter

    # 10) Ordenar
    df = df.sort_values("fecha")

    return df

# ============================================================================
# FUNCIONES DE ANÁLISIS / KPI
# ============================================================================

def calcular_kpis(df, fecha_desde, fecha_hasta):
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
    derivados = int(dff["derivado"].sum()) if "derivado" in dff.columns else 0
    resueltas = int(dff["resuelto"].sum()) if "resuelto" in dff.columns else 0

    tasa_derivacion = derivados / total * 100 if total > 0 else 0.0
    tasa_resolucion = resueltas / total * 100 if total > 0 else 0.0

    fecha_7d = fecha_hasta - timedelta(days=7)
    temas_nuevos = (
        dff[dff["fecha"] >= fecha_7d]["categoria"].nunique()
        if "categoria" in dff.columns
        else 0
    )

    return {
        "total_consultas": total,
        "tasa_resolucion": round(tasa_resolucion, 1),
        "tasa_derivacion": round(tasa_derivacion, 1),
        "consultas_resueltas": resueltas,
        "consultas_derivadas": derivados,
        "temas_emergentes": temas_nuevos,
    }


def obtener_evolucion_temporal(df, fecha_desde, fecha_hasta):
    if df.empty:
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


def obtener_distribucion_areas(df, fecha_desde, fecha_hasta):
    if df.empty:
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
# UI PRINCIPAL
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
    "<p style='text-align: center; color: #94a3b8; font-size: 1.1rem;'>"
    "Métricas y KPIs del Sistema de Atención a Personas</p>",
    unsafe_allow_html=True,
)

# Cargar datos (ETL completo)
df = cargar_y_transformar_datos()

# Sidebar
