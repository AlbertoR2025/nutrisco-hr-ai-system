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

    formatos =
