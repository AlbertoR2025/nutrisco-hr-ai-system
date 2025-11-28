import streamlit as st
import pandas as pd
from pathlib import Path

DATA_EXCEL = Path("data") / "Consultas-Atencion-Personas.xlsx"

@st.cache_data
def cargar_conversaciones_desde_excel():
    if not DATA_EXCEL.exists():
        return pd.DataFrame()
    # OJO: la misma hoja que estás usando
    df = pd.read_excel(DATA_EXCEL, sheet_name="Atención 2025")
    return df

st.set_page_config(page_title="DEBUG", page_icon="🐞", layout="wide")

df_conversaciones = cargar_conversaciones_desde_excel()

st.write("Columnas df_conversaciones:", list(df_conversaciones.columns))
st.write(df_conversaciones.head())
st.stop()
