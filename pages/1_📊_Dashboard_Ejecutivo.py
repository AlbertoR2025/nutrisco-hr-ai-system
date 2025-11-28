import streamlit as st
import pandas as pd
from pathlib import Path

# Configuración básica de la página
st.set_page_config(page_title="DEBUG Dashboard Ejecutivo", page_icon="🐞", layout="wide")

st.markdown(
    "<h1 style='color:#f97316;text-align:center;'>DEBUG Dashboard Ejecutivo</h1>",
    unsafe_allow_html=True,
)

# Ruta al Excel (carpeta data en el repo)
DATA_EXCEL = Path("data") / "Consultas-Atencion-Personas.xlsx"


@st.cache_data
def cargar_conversaciones_desde_excel():
    """Carga directa de la hoja 'Atención 2025' SIN renombrar, solo para debug."""
    if not DATA_EXCEL.exists():
        st.warning(f"No se encontró el archivo: {DATA_EXCEL}")
        return pd.DataFrame()

    try:
        df = pd.read_excel(DATA_EXCEL, sheet_name="Atención 2025")
    except Exception as e:
        st.error(f"Error al leer el Excel: {e}")
        return pd.DataFrame()

    return df


# ---------------------------------------------------------
# CARGA Y MUESTRA DE DATOS
# ---------------------------------------------------------

df_conversaciones = cargar_conversaciones_desde_excel()

st.subheader("Estado de los datos cargados")

st.write("Filas:", len(df_conversaciones))
st.write("Columnas:", list(df_conversaciones.columns))

if not df_conversaciones.empty:
    st.dataframe(df_conversaciones.head(), use_container_width=True)
else:
    st.info("El DataFrame está vacío. Revisa que el archivo y la hoja existan en la carpeta 'data/'.")
