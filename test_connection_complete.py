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
        st.code(f"Project: {gcp['project_id']}")
    except Exception as e:
        st.error(f"❌ Google Service Account: {e}")

st.markdown("---")

# 2. CONFIGURACIÓN DE PRUEBA
st.header("2. Configuración de Prueba")

# Input para el ID del Spreadsheet (igual que en el dashboard)
SPREADSHEET_ID = st.text_input(
    "ID de Google Sheets para probar",
    value="1JqFay6hXlUuURwZFANmr6FXARZqfH7tI",
    help="Solo el ID (parte después de /d/ en la URL)"
)

st.info("""
**💡 Nota:** Usando solo el ID del Spreadsheet para mayor confiabilidad.
Puedes usar:
- **Solo el ID:** `1JqFay6hXlUuURwZFANmr6FXARZqfH7tI` 
- **O URL completa:** Se extraerá automáticamente el ID
""")

# 3. PROBAR CONEXIÓN GOOGLE SHEETS
st.header("3. Conexión con Google Sheets")

if st.button("🚀 Ejecutar Prueba de Conexión", type="primary"):
    try:
        # Importar la función corregida
        from utils.google_sheets_connector import get_hr_data
        
        # Usar la función corregida
        with st.spinner("🔄 Conectando con Google Sheets..."):
            df = get_hr_data(SPREADSHEET_ID)
        
        if df.empty:
            st.error("❌ No se pudieron obtener datos del Google Sheet")
            
            st.info("""
            **🎯 Solución de Problemas:**
            
            1. **Verificar Compartición del Sheet:**
               - Ve a tu Google Sheet → Compartir
               - Agrega: `nutrisco-hr-dashboard@adroit-producer-461122-c3.iam.gserviceaccount.com`
               - Da permisos de **Editor**
            
            2. **Verificar ID:**
               - Asegúrate que el ID sea: `1JqFay6hXlUuURwZFANmr6FXARZqfH7tI`
            
            3. **Verificar que el Sheet tenga datos:**
               - La primera fila debe tener encabezados
               - Debe haber al menos una fila de datos
            """)
        else:
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
                sample_value = df[col].iloc[0] if not df.empty and len(df) > 0 else "N/A"
                sample = str(sample_value)[:50] + ('...' if len(str(sample_value)) > 50 else '')
                
                st.write(f"{i}. **{col}**")
                st.write(f"   - Tipo: {dtype}")
                st.write(f"   - No nulos: {non_null}/{len(df)}")
                st.write(f"   - Ejemplo: `{sample}`")
            
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
                
                stats_data = {
                    "total_registros": len(df),
                    "columnas": list(df.columns),
                    **fecha_info
                }
                st.json(stats_data)
    
    except Exception as e:
        st.error(f"❌ Error en la conexión: {str(e)}")
        
        # Información adicional para debugging
        st.info(f"""
        **🔧 Información de Debugging:**
        
        - **Error detallado:** `{str(e)}`
        - **ID usado:** `{SPREADSHEET_ID}`
        - **Service Account:** `nutrisco-hr-dashboard@adroit-producer-461122-c3.iam.gserviceaccount.com`
        
        **🎯 Pasos para solucionar:**
        
        1. **Verificar permisos:** El Sheet debe estar compartido con el Service Account
        2. **Verificar ID:** Confirma que el ID del Spreadsheet sea correcto
        3. **Verificar formato:** El Sheet debe tener datos en formato de tabla (con encabezados)
        """)

# 4. VERIFICACIÓN MANUAL
st.markdown("---")
st.header("🔍 Verificación Manual")

st.info("""
**Para verificar manualmente que todo está configurado correctamente:**

1. **✅ Service Account tiene acceso:**
   - Email: `nutrisco-hr-dashboard@adroit-producer-461122-c3.iam.gserviceaccount.com`
   - Permisos: **Editor**

2. **✅ El ID del spreadsheet es correcto:**
   - ID: `1JqFay6hXlUuURwZFANmr6FXARZqfH7tI`

3. **✅ El spreadsheet tiene datos:**
   - Debe tener al menos una hoja con datos
   - La primera fila debe tener encabezados de columna
""")

# 5. INSTRUCCIONES PARA EL SIGUIENTE PASO
st.markdown("---")
st.header("🎯 Siguientes Pasos")

if st.button("🔄 Ejecutar Prueba Nuevamente"):
    st.rerun()

st.success("""
**Cuando la conexión funcione correctamente:**
1. ✅ Verás los datos de tu Google Sheet
2. ✅ Podrás ver las columnas y registros  
3. ✅ El Dashboard Ejecutivo funcionará automáticamente
4. ✅ Podremos proceder con el Chatbot y otras funcionalidades
""")

# Footer
st.markdown("---")
st.markdown(f"**🕒 Última prueba:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
