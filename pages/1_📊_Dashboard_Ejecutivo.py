"""
ETL Pipeline: Google Sheets → Parquet limpio
Extrae, transforma y limpia datos de Google Sheets para análisis
"""

import pandas as pd
import numpy as np
from datetime import datetime
import re

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

SHEET_ID = "1JqFay6hXlUuURwZFANmr6FXARZqfH7tI"
SHEET_GID = "836579878"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&gid={SHEET_GID}"
OUTPUT_FILE = "consultas_limpias.parquet"


# ============================================================================
# FUNCIONES DE LIMPIEZA
# ============================================================================

def limpiar_fecha(fecha_str):
    """
    Parsea fechas en múltiples formatos:
    - DD/MM/YYYY
    - YYYY-MM-DD
    - DD-MM-YYYY
    - Número serial de Excel (ej: 44865)
    """
    if pd.isna(fecha_str):
        return pd.NaT
    
    # Si es número (serial de Excel)
    if isinstance(fecha_str, (int, float)):
        try:
            # Excel cuenta desde 1900-01-01
            return pd.Timestamp('1899-12-30') + pd.Timedelta(days=int(fecha_str))
        except:
            return pd.NaT
    
    # Si es string, probar múltiples formatos
    fecha_str = str(fecha_str).strip()
    
    formatos = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d/%m/%y",
        "%d-%m-%y",
    ]
    
    for formato in formatos:
        try:
            return pd.to_datetime(fecha_str, format=formato)
        except:
            continue
    
    # Último intento: detección automática
    try:
        return pd.to_datetime(fecha_str, dayfirst=True)
    except:
        return pd.NaT


def normalizar_texto(texto):
    """Normaliza texto: trim, lowercase, sin caracteres raros"""
    if pd.isna(texto):
        return ""
    texto = str(texto).strip()
    # Eliminar múltiples espacios
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def categorizar_estado(estado_raw):
    """Estandariza estados"""
    if pd.isna(estado_raw):
        return "Sin Estado"
    
    estado = str(estado_raw).lower().strip()
    
    if "derivad" in estado or "escalad" in estado:
        return "Derivado"
    elif "resuel" in estado or "cerrad" in estado or "completad" in estado:
        return "Resuelto"
    elif "pendiente" in estado or "en proceso" in estado:
        return "Pendiente"
    else:
        return "Otro"


def categorizar_area(area_raw):
    """Estandariza nombres de áreas"""
    if pd.isna(area_raw):
        return "Sin Área"
    
    area = str(area_raw).strip()
    
    # Mapeo de áreas conocidas (agregar según tu org)
    mapeo = {
        "rrhh": "RRHH",
        "recursos humanos": "RRHH",
        "ti": "TI",
        "tecnologia": "TI",
        "finanzas": "Finanzas",
        "contabilidad": "Finanzas",
        "operaciones": "Operaciones",
        "ops": "Operaciones",
    }
    
    area_lower = area.lower()
    for key, value in mapeo.items():
        if key in area_lower:
            return value
    
    return area


# ============================================================================
# ETL PRINCIPAL
# ============================================================================

def extraer_datos():
    """Extrae datos desde Google Sheets"""
    print("📥 Extrayendo datos de Google Sheets...")
    try:
        df = pd.read_csv(CSV_URL)
        print(f"✅ Extraídas {len(df)} filas, {len(df.columns)} columnas")
        return df
    except Exception as e:
        print(f"❌ Error en extracción: {e}")
        return pd.DataFrame()


def transformar_datos(df):
    """Limpia y transforma los datos"""
    print("\n🔄 Transformando datos...")
    
    if df.empty:
        print("❌ DataFrame vacío")
        return df
    
    # 1. Renombrar columnas
    columnas_originales = df.columns.tolist()
    print(f"Columnas originales: {columnas_originales}")
    
    mapeo_columnas = {
        "Fecha": "fecha",
        "Nombre": "usuario",
        "Área": "area",
        "Consulta": "categoria",
        "Observación": "consulta",
        "Respuesta": "respuesta",
        "Estado": "estado",
    }
    
    df = df.rename(columns=mapeo_columnas)
    
    # 2. Limpiar fechas
    print("📅 Limpiando fechas...")
    if "fecha" in df.columns:
        df["fecha"] = df["fecha"].apply(limpiar_fecha)
        fechas_invalidas = df["fecha"].isna().sum()
        print(f"   - Fechas inválidas: {fechas_invalidas}/{len(df)}")
        
        # Eliminar filas sin fecha válida
        df = df.dropna(subset=["fecha"])
        print(f"   - Filas restantes: {len(df)}")
    else:
        print("⚠️ No se encontró columna 'fecha'")
        return pd.DataFrame()
    
    # 3. Normalizar textos
    print("📝 Normalizando textos...")
    columnas_texto = ["usuario", "categoria", "consulta", "respuesta"]
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].apply(normalizar_texto)
    
    # 4. Estandarizar estado
    print("🏷️ Categorizando estados...")
    if "estado" in df.columns:
        df["estado_original"] = df["estado"]
        df["estado"] = df["estado"].apply(categorizar_estado)
        print(f"   - Estados únicos: {df['estado'].unique()}")
    
    # 5. Estandarizar áreas
    print("🏢 Categorizando áreas...")
    if "area" in df.columns:
        df["area_original"] = df["area"]
        df["area"] = df["area"].apply(categorizar_area)
        print(f"   - Áreas únicas: {df['area'].unique()}")
    
    # 6. Agregar columnas derivadas
    print("➕ Agregando columnas derivadas...")
    df["derivado"] = df["estado"] == "Derivado"
    df["resuelto_primer_contacto"] = df["estado"] == "Resuelto"
    
    # 7. Agregar metadata
    df["fecha_carga"] = datetime.now()
    df["año"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.month
    df["dia_semana"] = df["fecha"].dt.day_name()
    df["trimestre"] = df["fecha"].dt.quarter
    
    # 8. Ordenar por fecha
    df = df.sort_values("fecha")
    
    print(f"\n✅ Transformación completa: {len(df)} filas finales")
    return df


def cargar_datos(df, output_file):
    """Guarda datos limpios en Parquet"""
    print(f"\n💾 Guardando datos en {output_file}...")
    try:
        df.to_parquet(output_file, compression="snappy", index=False)
        file_size = pd.io.parquet.to_parquet(df, None).getbuffer().nbytes / 1024
        print(f"✅ Archivo guardado ({file_size:.1f} KB)")
        
        # Guardar también CSV de respaldo
        csv_file = output_file.replace(".parquet", ".csv")
        df.to_csv(csv_file, index=False, encoding="utf-8-sig")
        print(f"✅ CSV de respaldo: {csv_file}")
        
        return True
    except Exception as e:
        print(f"❌ Error al guardar: {e}")
        return False


def generar_reporte_calidad(df):
    """Genera reporte de calidad de datos"""
    print("\n" + "="*60)
    print("📊 REPORTE DE CALIDAD DE DATOS")
    print("="*60)
    
    print(f"\n📈 Dimensiones:")
    print(f"   - Filas: {len(df)}")
    print(f"   - Columnas: {len(df.columns)}")
    
    print(f"\n📅 Rango de fechas:")
    if "fecha" in df.columns and not df.empty:
        print(f"   - Desde: {df['fecha'].min()}")
        print(f"   - Hasta: {df['fecha'].max()}")
        print(f"   - Días cubiertos: {(df['fecha'].max() - df['fecha'].min()).days}")
    
    print(f"\n🔍 Valores nulos por columna:")
    nulos = df.isnull().sum()
    for col, count in nulos[nulos > 0].items():
        pct = (count / len(df)) * 100
        print(f"   - {col}: {count} ({pct:.1f}%)")
    
    print(f"\n📊 Distribución por estado:")
    if "estado" in df.columns:
        for estado, count in df["estado"].value_counts().items():
            pct = (count / len(df)) * 100
            print(f"   - {estado}: {count} ({pct:.1f}%)")
    
    print(f"\n🏢 Distribución por área:")
    if "area" in df.columns:
        for area, count in df["area"].value_counts().head(5).items():
            pct = (count / len(df)) * 100
            print(f"   - {area}: {count} ({pct:.1f}%)")
    
    print("\n" + "="*60)


# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================

def ejecutar_pipeline():
    """Ejecuta el pipeline ETL completo"""
    print("\n" + "="*60)
    print("🚀 INICIANDO PIPELINE ETL")
    print("="*60)
    
    # Extract
    df_raw = extraer_datos()
    if df_raw.empty:
        print("\n❌ Pipeline abortado: no hay datos")
        return False
    
    # Transform
    df_clean = transformar_datos(df_raw)
    if df_clean.empty:
        print("\n❌ Pipeline abortado: transformación falló")
        return False
    
    # Load
    success = cargar_datos(df_clean, OUTPUT_FILE)
    if not success:
        print("\n❌ Pipeline abortado: error al guardar")
        return False
    
    # Quality Report
    generar_reporte_calidad(df_clean)
    
    print("\n" + "="*60)
    print("✅ PIPELINE COMPLETADO EXITOSAMENTE")
    print("="*60)
    print(f"\n📁 Archivo de salida: {OUTPUT_FILE}")
    print(f"🔧 Úsalo en Streamlit con: pd.read_parquet('{OUTPUT_FILE}')")
    
    return True


if __name__ == "__main__":
    ejecutar_pipeline()
