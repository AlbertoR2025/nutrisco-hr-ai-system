import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de página
st.set_page_config(
    page_title="Prueba Conexión Completa",
    page_icon="🔌",
    layout="wide"
)

st.title("🔌 Prueba Completa de Conexión")
st.markdown("---")

# 1. PROBAR SECRETS
st.header("1. Verificación de Secrets")

col1, col2 = st.columns(2)

with col1:
    # Probar OpenAI Key
    try:
        openai_key = st.secrets["OPENAI_API_KEY"]
        st.success(f"✅ OPENAI_API_KEY")
        st.code(f"Key: {openai_key[:20]}...")
    except Exception as e:
        st.error(f"❌ OPENAI_API_KEY: {e}")

with col2:
    # Probar Google Service Account
    try:
        gcp = st.secrets["gcp_service_account"]
        st.success(f"✅ Google Service Account")
        st.code(f"Email: {gcp['client_email']}")
    except Exception as e:
        st.error(f"❌ Google Service Account: {e}")

st.markdown("---")

# 2. PROBAR CONEXIÓN GOOGLE SHEETS
st.header("2. Conexión con Google Sheets")

try:
    # Importar la función corregida
    from utils.google_sheets_connector import get_hr_data
    
    # URL del Google Sheet de RRHH
    SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1JqFay6hXlUuURwZFANmr6FXARZqfH7tI/edit#gid=836579878"
    
    # Usar la función corregida (SOLO recibe spreadsheet_url)
    with st.spinner("🔄 Conectando con Google Sheets..."):
        df = get_hr_data(SPREADSHEET_URL)
    
    if df.empty:
        st.error("❌ No se pudieron obtener datos del Google Sheet")
        st.info("""
        **🎯 Solución de Problemas:**
        1. **Verificar Compartición del Sheet:** Ve a tu Google Sheet → Compartir → Agrega: `nutrisco-hr-dashboard@adroit-producer-461122-c3.iam.gserviceaccount.com` → Editor
        2. **Verificar URL:** Asegúrate que la URL sea correcta
        3. **Verificar Secrets:** Revisa que todos los valores en Secrets sean correctos
        """)
        st.stop()
    
    st.success("✅ Autenticación con Google exitosa!")
    st.success("✅ Conexión con Google Sheets exitosa!")
    st.success(f"✅ Datos obtenidos: {len(df)} registros")
    
    # Mostrar información del dataset
    st.subheader("📊 Información del Dataset")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Registros", len(df))
    
    with col2:
        st.metric("Total Columnas", len(df.columns))
    
    with col3:
        st.metric("Última Actualización", datetime.now().strftime("%H:%M:%S"))
    
    # Mostrar columnas
    st.subheader("🗂️ Columnas Encontradas")
    st.write(f"**Lista completa:** {list(df.columns)}")
    
    # Análisis detallado de columnas
    st.subheader("🔍 Análisis de Columnas")
    for i, col in enumerate(df.columns, 1):
        non_null = df[col].notna().sum()
        dtype = df[col].dtype
        sample = str(df[col].iloc[0]) if not df.empty and len(df) > 0 else "N/A"
        
        st.write(f"{i}. **{col}**")
        st.write(f"   - Tipo: {dtype}")
        st.write(f"   - No nulos: {non_null}/{len(df)}")
        st.write(f"   - Ejemplo: `{sample[:50]}{'...' if len(sample) > 50 else ''}`")
    
    # Mostrar datos
    st.subheader("👀 Vista Previa de Datos")
    st.dataframe(df.head(10), use_container_width=True)
    
    # Estadísticas básicas
    if not df.empty:
        st.subheader("📈 Estadísticas Básicas")
        
        # Información de fechas si existe
        fecha_info = {}
        if 'fecha_creacion' in df.columns:
            fecha_info = {
                "fecha_minima": df['fecha_creacion'].min().strftime('%d/%m/%Y'),
                "fecha_maxima": df['fecha_creacion'].max().strftime('%d/%m/%Y')
            }
        
        st.json({
            "total_registros": len(df),
            "columnas": list(df.columns),
            **fecha_info
        })
    
except Exception as e:
    st.error(f"❌ Error en la conexión: {str(e)}")

# 3. INSTRUCCIONES PARA EL SIGUIENTE PASO
st.markdown("---")
st.header("🎯 Siguientes Pasos")

if st.button("🔄 Probar Conexión Nuevamente"):
    st.rerun()

st.success("""
**Cuando la conexión funcione correctamente:**
1. ✅ Verás los datos de tu Google Sheet
2. ✅ Podrás ver las columnas y registros
3. ✅ Procederemos a implementar el Dashboard completo
""")

# Footer
st.markdown("---")
st.markdown(f"**🕒 Última prueba:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
