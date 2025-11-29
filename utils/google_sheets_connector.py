import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime, timedelta
import numpy as np

class HRSheetsConnector:
    def __init__(self):
        self.sheet = None
        self.df_raw = None
        self.df_clean = None
        
    @st.cache_resource(show_spinner=False)
    def connect_to_sheets(_self, credentials_info, spreadsheet_url):
        """Conectar con Google Sheets usando service account"""
        try:
            # Configurar scope
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Crear credenciales desde el dict
            creds = Credentials.from_service_account_info(credentials_info, scopes=scope)
            client = gspread.authorize(creds)
            
            # Abrir por URL
            _self.sheet = client.open_by_url(spreadsheet_url).sheet1
            return True
            
        except Exception as e:
            st.error(f"❌ Error conectando con Google Sheets: {str(e)}")
            return False
    
    def extract_data(self):
        """Extraer todos los datos de la hoja"""
        try:
            records = self.sheet.get_all_records()
            self.df_raw = pd.DataFrame(records)
            
            st.success(f"✅ Datos extraídos: {len(self.df_raw)} registros")
            return True
            
        except Exception as e:
            st.error(f"❌ Error extrayendo datos: {str(e)}")
            return False
    
    def transform_data(self):
        """Transformación robusta de datos RRHH"""
        if self.df_raw is None or self.df_raw.empty:
            st.error("No hay datos para transformar")
            return False
        
        df = self.df_raw.copy()
        
        # DEBUG: Mostrar columnas originales
        st.sidebar.write("🔍 Columnas originales:", df.columns.tolist())
        
        # 1. NORMALIZAR NOMBRES DE COLUMNAS
        df.columns = [self.normalize_column_name(col) for col in df.columns]
        
        # 2. MAPEO INTELIGENTE DE COLUMNAS
        df = self.map_columns_intelligently(df)
        
        # 3. LIMPIAR FECHAS CON MÚLTIPLOS INTENTOS
        df = self.clean_dates_robust(df)
        
        # 4. NORMALIZAR CATEGORÍAS
        df = self.normalize_categories(df)
        
        # 5. CALCULAR MÉTRICAS DERIVADAS
        df = self.calculate_derived_metrics(df)
        
        # 6. VALIDAR Y COMPLETAR DATOS
        df = self.validate_and_complete_data(df)
        
        self.df_clean = df
        st.success(f"✅ Datos transformados: {len(self.df_clean)} registros limpios")
        return True
    
    def normalize_column_name(self, name):
        """Normalizar nombres de columnas de forma robusta"""
        if pd.isna(name):
            return 'columna_desconocida'
        
        name_str = str(name).strip().lower()
        
        # Remover tildes y caracteres especiales
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u', ' ': '_', '-': '_'
        }
        
        for old, new in replacements.items():
            name_str = name_str.replace(old, new)
        
        return name_str
    
    def map_columns_intelligently(self, df):
        """Mapeo inteligente basado en patrones comunes"""
        
        # Buscar columnas que podrían ser cada tipo
        fecha_candidates = [col for col in df.columns if any(x in col for x in ['fecha', 'date', 'fech'])]
        usuario_candidates = [col for col in df.columns if any(x in col for x in ['usuario', 'nombre', 'colaborador', 'empleado'])]
        area_candidates = [col for col in df.columns if any(x in col for x in ['area', 'departamento', 'depto'])]
        consulta_candidates = [col for col in df.columns if any(x in col for x in ['consulta', 'pregunta', 'solicitud', 'motivo'])]
        respuesta_candidates = [col for col in df.columns if any(x in col for x in ['respuesta', 'solucion', 'observacion'])]
        estado_candidates = [col for col in df.columns if any(x in col for x in ['estado', 'status'])]
        
        # Asignar la primera columna candidata encontrada
        mapping = {}
        if fecha_candidates: mapping['fecha_raw'] = fecha_candidates[0]
        if usuario_candidates: mapping['usuario'] = usuario_candidates[0]
        if area_candidates: mapping['area_raw'] = area_candidates[0]
        if consulta_candidates: mapping['consulta'] = consulta_candidates[0]
        if respuesta_candidates: mapping['respuesta'] = respuesta_candidates[0]
        if estado_candidates: mapping['estado_raw'] = estado_candidates[0]
        
        # Aplicar renombrado
        for new_name, old_name in mapping.items():
            df[new_name] = df[old_name]
            
        st.sidebar.write("🗂️ Columnas mapeadas:", mapping)
        return df
    
    def clean_dates_robust(self, df):
        """Limpieza robusta de fechas con múltiples intentos"""
        if 'fecha_raw' not in df.columns:
            st.warning("⚠️ No se encontró columna de fecha")
            df['fecha_creacion'] = datetime.now()
            return df
        
        # Intentar diferentes métodos de parsing
        fecha_series = df['fecha_raw']
        
        # Método 1: Intentar datetime normal
        df['fecha_creacion'] = pd.to_datetime(fecha_series, errors='coerce', dayfirst=True)
        
        # Método 2: Si falla, intentar formato específico DD/MM/YYYY
        if df['fecha_creacion'].isna().any():
            try:
                mask = df['fecha_creacion'].isna()
                df.loc[mask, 'fecha_creacion'] = pd.to_datetime(
                    df.loc[mask, 'fecha_raw'], format='%d/%m/%Y', errors='coerce'
                )
            except:
                pass
        
        # Método 3: Si aún falla, intentar formato YYYY-MM-DD
        if df['fecha_creacion'].isna().any():
            try:
                mask = df['fecha_creacion'].isna()
                df.loc[mask, 'fecha_creacion'] = pd.to_datetime(
                    df.loc[mask, 'fecha_raw'], format='%Y-%m-%d', errors='coerce'
                )
            except:
                pass
        
        # Método 4: Si son números de Excel/Sheets
        if df['fecha_creacion'].isna().any():
            try:
                mask = df['fecha_creacion'].isna()
                # Convertir números de Excel a fechas
                excel_serial_numbers = pd.to_numeric(df.loc[mask, 'fecha_raw'], errors='coerce')
                df.loc[mask, 'fecha_creacion'] = pd.to_datetime(
                    '1899-12-30') + pd.to_timedelta(excel_serial_numbers, unit='D')
            except:
                pass
        
        # Si aún hay fechas vacías, usar fecha actual
        df['fecha_creacion'] = df['fecha_creacion'].fillna(pd.Timestamp.now())
        
        st.sidebar.write("📅 Fechas procesadas - Mín:", df['fecha_creacion'].min(), "Máx:", df['fecha_creacion'].max())
        return df
    
    def normalize_categories(self, df):
        """Normalizar áreas y estados"""
        # Normalizar áreas
        if 'area_raw' in df.columns:
            area_mapping = {
                'rrhh': 'RRHH', 'recursos humanos': 'RRHH', 'rh': 'RRHH',
                'ti': 'TI', 'tecnologías de información': 'TI', 'sistemas': 'TI',
                'finanzas': 'Finanzas', 'contabilidad': 'Finanzas',
                'operaciones': 'Operaciones', 'producción': 'Operaciones',
                'ventas': 'Ventas', 'comercial': 'Ventas',
                'marketing': 'Marketing',
                'administración': 'Administración', 'admin': 'Administración'
            }
            
            df['area'] = (
                df['area_raw']
                .astype(str)
                .str.lower()
                .str.strip()
                .map(area_mapping)
                .fillna('Otros')
            )
        
        # Normalizar estados
        if 'estado_raw' in df.columns:
            estado_mapping = {
                'resuelto': 'Resuelto', 'completado': 'Resuelto', 'cerrado': 'Resuelto',
                'pendiente': 'Pendiente', 'en proceso': 'Pendiente',
                'derivado': 'Derivado', 'asignado': 'Derivado'
            }
            
            df['estado'] = (
                df['estado_raw']
                .astype(str)
                .str.lower()
                .str.strip()
                .map(estado_mapping)
                .fillna('Sin Estado')
            )
        else:
            df['estado'] = 'Resuelto'  # Por defecto
        
        return df
    
    def calculate_derived_metrics(self, df):
        """Calcular métricas para KPIs"""
        # Resolución primer contacto (si no está derivado y está resuelto)
        df['resolucion_primer_contacto'] = (
            (df['estado'] == 'Resuelto') & 
            (~df['respuesta'].isna()) & 
            (df['respuesta'] != '')
        )
        
        # Tiempo de respuesta (si tenemos fecha de creación)
        df['dias_desde_creacion'] = (datetime.now() - df['fecha_creacion']).dt.days
        
        # Categorizar consultas por contenido
        df['categoria'] = self.categorize_consultas(df)
        
        return df
    
    def categorize_consultas(self, df):
        """Categorizar automáticamente las consultas"""
        if 'consulta' not in df.columns:
            return 'General'
        
        categorias = {
            'beneficios': ['bono', 'beneficio', 'prestación', 'subsidio', 'ayuda'],
            'nomina': ['sueldo', 'pago', 'nómina', 'liquidación', 'descuento'],
            'vacaciones': ['vacacion', 'permiso', 'día libre', 'descanso'],
            'capacitacion': ['curso', 'capacitación', 'training', 'entrenamiento'],
            'equipo': ['laptop', 'computador', 'herramienta', 'equipo'],
            'sistema': ['sistema', 'software', 'plataforma', 'acceso', 'login']
        }
        
        def asignar_categoria(texto):
            if pd.isna(texto):
                return 'General'
            
            texto_str = str(texto).lower()
            for categoria, palabras in categorias.items():
                if any(palabra in texto_str for palabra in palabras):
                    return categoria
            return 'General'
        
        return df['consulta'].apply(asignar_categoria)
    
    def validate_and_complete_data(self, df):
        """Validar y completar datos críticos"""
        # Asegurar columnas críticas
        if 'usuario' not in df.columns:
            df['usuario'] = 'Usuario no especificado'
        
        if 'consulta' not in df.columns:
            df['consulta'] = 'Consulta no especificada'
        
        if 'respuesta' not in df.columns:
            df['respuesta'] = 'En proceso'
        
        # Validar fechas
        fecha_maxima = datetime.now() + timedelta(days=1)  # Permitir hasta mañana
        df['fecha_creacion'] = df['fecha_creacion'].clip(upper=fecha_maxima)
        
        return df
    
    def get_clean_data(self):
        """Obtener datos limpios"""
        return self.df_clean

# Función principal para usar en Streamlit
@st.cache_resource(show_spinner="Conectando con Google Sheets...")
def get_hr_data(credentials_info, spreadsheet_url):
    """Función principal para obtener datos de RRHH"""
    connector = HRSheetsConnector()
    
    if connector.connect_to_sheets(credentials_info, spreadsheet_url):
        if connector.extract_data():
            if connector.transform_data():
                return connector.get_clean_data()
    
    return pd.DataFrame()  # Retornar DataFrame vacío en caso de error