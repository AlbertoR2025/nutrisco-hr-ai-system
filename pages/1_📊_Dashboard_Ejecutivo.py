"""
Dashboard Ejecutivo - KPIs y Métricas Principales
Vista ejecutiva para jefaturas y equipo RRHH
"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path
import os

# ---------------------------------------------------------
# CARGA DE DATOS - VERSIÓN MEJORADA
# ---------------------------------------------------------

@st.cache_data
def cargar_conversaciones_desde_excel():
    """Carga la hoja de consultas 'Atención 2025' y la normaliza a un esquema común."""
    
    # Listar archivos en el directorio para debug
    st.write("🔍 **Buscando archivos en el directorio:**")
    current_dir = Path(".")
    data_dir = Path("data")
    
    st.write(f"Directorio actual: {current_dir.absolute()}")
    
    # Listar contenido del directorio actual
    if current_dir.exists():
        archivos = list(current_dir.glob("*"))
        st.write("📁 Contenido del directorio raíz:")
        for archivo in archivos:
            st.write(f"   - {archivo.name} (directorio: {archivo.is_dir()})")
    
    # Listar contenido de la carpeta data si existe
    if data_dir.exists():
        archivos_data = list(data_dir.glob("*"))
        st.write("📁 Contenido de la carpeta 'data':")
        for archivo in archivos_data:
            st.write(f"   - {archivo.name}")
    else:
        st.warning("⚠️ La carpeta 'data' no existe")
    
    # Posibles rutas y nombres de archivo
    posibles_rutas = [
        Path("data") / "Consultas-Atencion-Personas.xlsx",
        Path("data") / "Consultas Atención Personas.xlsx", 
        Path("data") / "Consultas-Atención-Personas.xlsx",
        Path("data") / "Consultas-Atención-Personas-Enriquecido.xlsx",
        Path("Consultas-Atencion-Personas.xlsx"),
        Path("Consultas Atención Personas.xlsx"),
    ]
    
    archivo_encontrado = None
    for ruta in posibles_rutas:
        if ruta.exists():
            archivo_encontrado = ruta
            st.success(f"✅ Archivo encontrado: {ruta}")
            break
    
    if archivo_encontrado is None:
        st.error("❌ No se pudo encontrar ningún archivo Excel con los nombres esperados")
        st.info("""
        Archivos esperados:
        - data/Consultas-Atencion-Personas.xlsx
        - data/Consultas Atención Personas.xlsx
        - data/Consultas-Atención-Personas-Enriquecido.xlsx
        """)
        return pd.DataFrame()

    try:
        # Leer el archivo Excel
        st.write(f"📖 Leyendo archivo: {archivo_encontrado}")
        
        # Mostrar las hojas disponibles
        excel_file = pd.ExcelFile(archivo_encontrado)
        st.write(f"📊 Hojas disponibles: {excel_file.sheet_names}")
        
        # Intentar leer la hoja "Atención 2025" o la primera hoja
        hoja = "Atención 2025"
        if hoja in excel_file.sheet_names:
            df = pd.read_excel(archivo_encontrado, sheet_name=hoja)
        else:
            st.warning(f"⚠️ No se encontró la hoja '{hoja}'. Usando la primera hoja: {excel_file.sheet_names[0]}")
            df = pd.read_excel(archivo_encontrado, sheet_name=excel_file.sheet_names[0])
        
        st.write("🔍 **Columnas originales en el archivo Excel:**")
        st.write(list(df.columns))
        st.write(f"📊 **Total de filas cargadas: {len(df)}**")

        # Mapeo exacto basado en las columnas que proporcionaste
        column_mapping = {
            'Fecha ': 'fecha',           # Espacio al final
            'Nombre ': 'usuario',        # Espacio al final  
            'Área': 'area',
            'Consulta': 'categoria',
            'Observación': 'consulta',
            'Respuesta': 'respuesta',
            'Estado': 'estado'
        }
        
        # Verificar qué columnas existen realmente
        columnas_existentes = []
        columnas_faltantes = []
        
        for col_original, col_nuevo in column_mapping.items():
            if col_original in df.columns:
                columnas_existentes.append((col_original, col_nuevo))
            else:
                columnas_faltantes.append(col_original)
        
        st.write("✅ **Columnas que serán renombradas:**")
        for col_orig, col_nuevo in columnas_existentes:
            st.write(f"   - '{col_orig}' → '{col_nuevo}'")
        
        if columnas_faltantes:
            st.warning(f"⚠️ **Columnas faltantes:** {columnas_faltantes}")
        
        # Renombrar solo las columnas que existen
        mapeo_a_aplicar = {orig: nuevo for orig, nuevo in columnas_existentes}
        df = df.rename(columns=mapeo_a_aplicar)
        
        st.write("✅ **Columnas después del renombrado:**")
        st.write(list(df.columns))

    except Exception as e:
        st.error(f"❌ Error al cargar el archivo Excel: {str(e)}")
        return pd.DataFrame()

    # Normalizar tipos y campos derivados
    if 'fecha' in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        # Contar filas con fechas válidas
        fechas_validas = df["fecha"].notna().sum()
        st.write(f"📅 Fechas válidas: {fechas_validas}/{len(df)}")
        
        # Eliminar filas donde la fecha es inválida
        filas_antes = len(df)
        df = df.dropna(subset=["fecha"])
        filas_despues = len(df)
        st.write(f"🗑️ Filas eliminadas por fecha inválida: {filas_antes - filas_despues}")
    else:
        st.error("❌ No se encontró la columna de fecha después del renombrado")
        return pd.DataFrame()

    if 'estado' in df.columns:
        df["estado"] = df["estado"].astype(str)
        df["derivado"] = df["estado"].str.lower().str.contains("derivado")
        df["resuelto_primer_contacto"] = ~df["derivado"]
        st.write(f"📋 Estados únicos: {df['estado'].unique()}")
    else:
        st.warning("⚠️ No se encontró columna 'estado', usando valores por defecto")
        df["derivado"] = False
        df["resuelto_primer_contacto"] = True

    # Crear columnas que podrían faltar
    if "tiempo_respuesta_mins" not in df.columns:
        df["tiempo_respuesta_mins"] = None

    df["tema_emergente"] = False
    df["satisfaccion"] = None

    st.write("📊 **Resumen del DataFrame procesado:**")
    st.write(f"   - Total de registros: {len(df)}")
    if 'fecha' in df.columns:
        st.write(f"   - Rango de fechas: {df['fecha'].min()} a {df['fecha'].max()}")
    if 'area' in df.columns:
        st.write(f"   - Áreas únicas: {df['area'].nunique()}")
    if 'categoria' in df.columns:
        st.write(f"   - Categorías únicas: {df['categoria'].nunique()}")

    return df


def calcular_kpis_df(df, fecha_desde, fecha_hasta):
    """Calcular KPIs principales usando el DataFrame."""
    if df.empty or 'fecha' not in df.columns:
        st.warning("⚠️ No hay datos disponibles para calcular KPIs")
        return {
            "total_consultas": 0,
            "tasa_resolucion_primer_contacto": 0.0,
            "tiempo_promedio_respuesta_mins": 0.0,
            "temas_emergentes_nuevos": 0,
            "tasa_derivacion": 0.0,
            "consultas_resueltas": 0,
            "consultas_derivadas": 0,
        }

    try:
        # Asegurarnos de que las fechas sean comparables
        mask = (df["fecha"] >= pd.Timestamp(fecha_desde)) & (df["fecha"] <= pd.Timestamp(fecha_hasta))
        dff = df.loc[mask].copy()

        total = len(dff)
        st.write(f"📈 Consultas en el rango de fechas: {total}")
        
        # Calcular derivados si existe la columna
        if 'derivado' in dff.columns:
            derivados = int(dff["derivado"].sum())
        else:
            derivados = 0
            
        resueltas = total - derivados

        if total > 0:
            tasa_derivacion = derivados / total * 100
            tasa_resolucion = resueltas / total * 100
        else:
            tasa_derivacion = 0.0
            tasa_resolucion = 0.0

        # Tiempo de respuesta
        if "tiempo_respuesta_mins" in dff.columns:
            t = dff["tiempo_respuesta_mins"].dropna()
            tiempo_prom = float(t.mean()) if not t.empty else 0.0
        else:
            tiempo_prom = 0.0

        # Temas emergentes (últimos 7 días)
        fecha_7d = fecha_hasta - timedelta(days=7)
        dff7 = dff[dff["fecha"] >= pd.Timestamp(fecha_7d)]
        
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
        
    except Exception as e:
        st.error(f"❌ Error al calcular KPIs: {e}")
        return {
            "total_consultas": 0,
            "tasa_resolucion_primer_contacto": 0.0,
            "tiempo_promedio_respuesta_mins": 0.0,
            "temas_emergentes_nuevos": 0,
            "tasa_derivacion": 0.0,
            "consultas_resueltas": 0,
            "consultas_derivadas": 0,
        }


def obtener_evolucion_temporal_df(df, fecha_desde, fecha_hasta):
    """Evolución diaria de consultas en el rango."""
    if df.empty or 'fecha' not in df.columns:
        return pd.DataFrame(columns=["Fecha", "Total"])
    
    try:
        mask = (df["fecha"] >= pd.Timestamp(fecha_desde)) & (df["fecha"] <= pd.Timestamp(fecha_hasta))
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
        
    except Exception as e:
        st.error(f"❌ Error al procesar datos temporales: {e}")
        return pd.DataFrame(columns=["Fecha", "Total"])


def obtener_distribucion_areas_df(df, fecha_desde, fecha_hasta):
    """Distribución de consultas por área en el rango."""
    if df.empty or "fecha" not in df.columns or "area" not in df.columns:
        return pd.DataFrame(columns=["area", "total"])
        
    try:
        mask = (df["fecha"] >= pd.Timestamp(fecha_desde)) & (df["fecha"] <= pd.Timestamp(fecha_hasta))
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
    except Exception as e:
        st.error(f"❌ Error al procesar distribución por áreas: {e}")
        return pd.DataFrame(columns=["area", "total"])


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

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
st.markdown("---")
st.markdown("### 🔍 Cargando datos...")
df_conversaciones = cargar_conversaciones_desde_excel()

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

# ---------------------------------------------------------
# KPIs PRINCIPALES
# ---------------------------------------------------------

st.markdown("### 📊 KPIs Principales")
kpis = calcular_kpis_df(df_conversaciones, fecha_desde, fecha_hasta)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total consultas", kpis["total_consultas"])
col2.metric("Resolución 1er contacto", f"{kpis['tasa_resolucion_primer_contacto']:.1f}%")
col3.metric("Derivadas", kpis["consultas_derivadas"], f"{kpis['tasa_derivacion']:.1f}%")
col4.metric("Temas emergentes (últ. 7d)", kpis["temas_emergentes_nuevos"])

# ---------------------------------------------------------
# GRÁFICOS
# ---------------------------------------------------------

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
            name="Consultas"
        )
    )
    fig_evo.update_layout(
        height=350,
        margin=dict(l=40, r=20, t=30, b=40),
        xaxis_title="Fecha",
        yaxis_title="Consultas",
        showlegend=False
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
            name="Consultas por área"
        )
    )
    fig_areas.update_layout(
        height=350,
        margin=dict(l=40, r=20, t=30, b=80),
        xaxis_title="Área",
        yaxis_title="Consultas",
        xaxis_tickangle=-45,
        showlegend=False
    )
    st.plotly_chart(fig_areas, use_container_width=True)
else:
    st.info("No hay datos de áreas para el rango seleccionado.")

# ---------------------------------------------------------
# TABLA DETALLADA
# ---------------------------------------------------------

st.markdown("### 📋 Detalle de consultas")

if not df_conversaciones.empty and 'fecha' in df_conversaciones.columns:
    mask = (df_conversaciones["fecha"] >= fecha_desde) & (
        df_conversaciones["fecha"] <= fecha_hasta
    )
    df_filtrado = df_conversaciones.loc[mask].copy()

    if not df_filtrado.empty:
        # Seleccionar solo las columnas que existen
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
    st.info("No hay datos disponibles para mostrar.")

# ---------------------------------------------------------
# INFORMACIÓN DE DEPURACIÓN (se puede comentar después)
# ---------------------------------------------------------

with st.expander("🔧 Información de Depuración"):
    st.write("### Estructura de datos cargada:")
    if not df_conversaciones.empty:
        st.write(f"**Dimensiones:** {df_conversaciones.shape}")
        st.write("**Columnas:**", list(df_conversaciones.columns))
        st.write("**Tipos de datos:**")
        st.write(df_conversaciones.dtypes)
        st.write("**Estadísticas descriptivas:**")
        st.write(df_conversaciones.describe(include='all', datetime_is_numeric=True))
    else:
        st.write("No se cargaron datos")
