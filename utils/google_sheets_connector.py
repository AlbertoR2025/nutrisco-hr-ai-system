import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime, timedelta
import numpy as np
import re

class HRSheetsConnector:
    def __init__(self):
        self.sheet = None
        self.df_raw = None
        self.df_clean = None
        
    def connect_to_sheets(self, credentials_info, spreadsheet_url_or_id, sheet_name=None):
        """Conectar con Google Sheets - VERSIÓN MEJORADA"""
        try:
            # Configurar scope
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Crear credenciales
            creds = Credentials.from_service_account_info(credentials_info, scopes=scope)
            client = gspread.authorize(creds)
            
            st.sidebar.write("🔗 Conectando con Google Sheets...")
            
            # Extraer el ID del spreadsheet
            if 'spreadsheets/d/' in spreadsheet_url_or_id:
                # Es una URL - extraer ID
                match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', spreadsheet_url_or_id)
                if match:
                    spreadsheet_id = match.group(1)
                else:
                    st.error("❌ No se pudo extraer el ID de la URL")
                    return False
            else:
                # Ya es un ID
                spreadsheet_id = spreadsheet_url_or_id
            
            # Abrir el spreadsheet
            spreadsheet = client.open_by_key(spreadsheet_id)
            st.sidebar.write(f"✅ Spreadsheet abierto: {spreadsheet.title}")
            
            # Obtener lista de hojas disponibles
            worksheets = spreadsheet.worksheets()
            sheet_names = [ws.title for ws in worksheets]
            st.sidebar.write(f"📋 Hojas disponibles: {sheet_names}")
            
            # Intentar encontrar la hoja correcta
            target_sheet = None
            
            # Método 1: Por nombre específico si se proporciona
            if sheet_name:
                try:
                    target_sheet = spreadsheet.worksheet(sheet_name)
                    st.sidebar.write(f"✅ Usando hoja por nombre: {sheet_name}")
                except:
                    st.sidebar.write(f"⚠️ No se encontró hoja con nombre: {sheet_name}")
            
            # Método 2: Buscar por GID si está en la URL
            if not target_sheet and 'gid=' in spreadsheet_url_or_id:
                gid_match = re.search(r'gid=(\d+)', spreadsheet_url_or_id)
                if gid_match:
                    target_gid = int(gid_match.group(1))
                    for ws in worksheets:
                        if ws.id == target_gid:
                            target_sheet = ws
                            st.sidebar.write(f"✅ Usando hoja por GID: {target_gid} - {ws.title}")
                            break
            
            # Método 3: Usar la primera hoja
            if not target_sheet:
                target_sheet = worksheets[0]
                st.sidebar.write(f"✅ Usando primera hoja: {target_sheet.title}")
            
            self.sheet = target_sheet
            st.sidebar.write(f"📊 Hoja seleccionada: {self.sheet.title}")
            return True
            
        except Exception as e:
            st.error(f"❌ Error conectando con Google Sheets: {str(e)}")
            st.info(f"""
            **🔧 Información para Debugging:**
            - URL/ID usado: `{spreadsheet_url_or_id}`
            - Service Account: `{credentials_info.get('client_email', 'No disponible')}`
            - Error: {str(e)}
            
            **🎯 Verifica:**
            1. Que el Sheet esté compartido con: `nutrisco-hr-dashboard@adroit-producer-461122-c3.iam.gserviceaccount.com`
            2. Que tenga permisos de **Editor**
            3. Que la hoja tenga datos
            """)
            return False
    
    def extract_data(self):
        """Extraer todos los datos de la hoja"""
        try:
            # Obtener todos los registros
            records = self.sheet.get_all_records()
            
            if not records:
                st.warning("⚠️ La hoja está vacía o no tiene datos en formato de tabla")
                return False
                
            self.df_raw = pd.DataFrame(records)
            
            if self.df_raw.empty:
                st.warning("⚠️ El DataFrame está vacío después de la conversión")
                return False
                
            st.sidebar.write(f"✅ Datos extraídos: {len(self.df_raw)} registros, {len(self.df_raw.columns)} columnas")
            return True
            
        except Exception as e:
            st.error(f"❌ Error extrayendo datos: {str(e)}")
            return False
    
    def transform_data(self):
        """Transformación robusta de datos RRHH"""
        if self.df_raw is None or self.df_raw.empty:
            st.error("❌ No hay datos para transformar")
            return False
        
        df = self.df_raw.copy()
        
        st.sidebar.write("🔄 Iniciando transformación de datos...")
        
        # 1. NORMALIZAR NOMBRES DE COLUMNAS
        df.columns = [self.normalize_column_name(col) for col in df.columns]
        st.sidebar.write(f"📝 Columnas normalizadas: {list(df.columns)}")
        
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
        st.sidebar.write(f"✅ Transformación completada: {len(self.df_clean)} registros limpios")
        return True
    
    def normalize_column_name(self, name):
        """Normalizar nombres de columnas"""
        if pd.isna(name):
            return 'columna_desconocida'
        
        name_str = str(name).strip().lower()
        
        # Remover tildes y caracteres especiales
        replacements = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u', ' ': '_', '-': '_', '(': '', ')': ''
        }
        
        for old, new in replacements.items():
            name_str = name_str.replace(old, new)
        
        return name_str
    
    def map_columns_intelligently(self, df):
        """Mapeo inteligente basado en patrones comunes"""
        mapping = {}
        
        # Buscar columnas por patrones
        for col in df.columns:
            col_lower = col.lower()
            
            if any(x in col_lower for x in ['fecha', 'date']):
                mapping[col] = 'fecha_raw'
            elif any(x in col_lower for x in ['usuario', 'nombre', 'colaborador', 'empleado']):
                mapping[col] = 'usuario'
            elif any(x in col_lower for x in ['area', 'departamento', 'depto']):
                mapping[col] = 'area_raw'
            elif any(x in col_lower for x in ['consulta', 'pregunta', 'solicitud', 'motivo']):
                mapping[col] = 'consulta'
            elif any(x in col_lower for x in ['respuesta', 'solucion', 'observacion', 'comentario']):
                mapping[col] = 'respuesta'
            elif any(x in col_lower for x in ['estado', 'status']):
                mapping[col] = 'estado_raw'
            elif any(x in col_lower for x in ['derivado', 'asignado']):
                mapping[col] = 'derivado_a'
        
        # Aplicar renombrado
        for old_name, new_name in mapping.items():
            df[new_name] = df[old_name]
        
        st.sidebar.write("🗂️ Columnas mapeadas:", mapping)
        return df
    
    def clean_dates_robust(self, df):
        """Limpieza robusta de fechas"""
        if 'fecha_raw' not in df.columns:
            st.sidebar.warning("⚠️ No se encontró columna de fecha, usando fecha actual")
            df['fecha_creacion'] = datetime.now()
            return df
        
        # Intentar diferentes formatos de fecha
        original_dates = df['fecha_raw'].copy()
        
        # Método 1: datetime normal
        df['fecha_creacion'] = pd.to_datetime(df['fecha_raw'], errors='coerce', dayfirst=True)
        
        # Método 2: Si hay muchos NaT, intentar formato específico
        if df['fecha_creacion'].isna().sum() > len(df) * 0.5:  # Si más del 50% son NaT
            try:
                df['fecha_creacion'] = pd.to_datetime(df['fecha_raw'], format='%d/%m/%Y', errors='coerce')
            except:
                pass
        
        # Método 3: Intentar con diferentes formatos
        if df['fecha_creacion'].isna().any():
            try:
                # Para formatos como "2023-12-31"
                mask = df['fecha_creacion'].isna()
                df.loc[mask, 'fecha_creacion'] = pd.to_datetime(
                    df.loc[mask, 'fecha_raw'], format='%Y-%m-%d', errors='coerce'
                )
            except:
                pass
        
        # Si aún hay fechas vacías, usar fecha actual
        nan_count = df['fecha_creacion'].isna().sum()
        if nan_count > 0:
            st.sidebar.warning(f"⚠️ {nan_count} fechas no pudieron parsearse, usando fecha actual")
            df['fecha_creacion'] = df['fecha_creacion'].fillna(pd.Timestamp.now())
        
        st.sidebar.write(f"📅 Fechas: {df['fecha_creacion'].min().strftime('%d/%m/%Y')} a {df['fecha_creacion'].max().strftime('%d/%m/%Y')}")
        return df
    
    def normalize_categories(self, df):
        """Normalizar áreas y estados"""
        # Normalizar áreas
        if 'area_raw' in df.columns:
            area_mapping = {
                'rrhh': 'RRHH', 'recursoshumanos': 'RRHH', 'rh': 'RRHH',
                'ti': 'TI', 'tecnologia': 'TI', 'sistemas': 'TI',
                'finanzas': 'Finanzas', 'contabilidad': 'Finanzas',
                'operaciones': 'Operaciones', 'produccion': 'Operaciones',
                'ventas': 'Ventas', 'comercial': 'Ventas',
                'marketing': 'Marketing',
                'administracion': 'Administración', 'admin': 'Administración'
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
                'pendiente': 'Pendiente', 'enproceso': 'Pendiente',
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
            df['estado'] = 'Resuelto'
        
        return df
    
    def calculate_derived_metrics(self, df):
        """Calcular métricas para KPIs"""
        # Resolución primer contacto
        df['resolucion_primer_contacto'] = (
            (df['estado'] == 'Resuelto') & 
            (df['respuesta'].notna()) & 
            (df['respuesta'].astype(str) != '') &
            (df['derivado_a'].isna() | (df['derivado_a'].astype(str) == ''))
        )
        
        # Tiempo desde creación
        df['dias_desde_creacion'] = (datetime.now() - df['fecha_creacion']).dt.days
        
        # Categorizar consultas
        df['categoria'] = self.categorize_consultas(df)
        
        return df
    
    def categorize_consultas(self, df):
        """Categorizar automáticamente las consultas"""
        if 'consulta' not in df.columns:
            return 'General'
        
        categorias = {
            'beneficios': ['bono', 'beneficio', 'prestacion', 'subsidio', 'ayuda'],
            'nomina': ['sueldo', 'pago', 'nomina', 'liquidacion', 'descuento'],
            'vacaciones': ['vacacion', 'permiso', 'día libre', 'descanso'],
            'capacitacion': ['curso', 'capacitacion', 'training', 'entrenamiento'],
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
        required_columns = {
            'usuario': 'Usuario no especificado',
            'consulta': 'Consulta no especificada', 
            'respuesta': 'En proceso',
            'area': 'Otros',
            'estado': 'Pendiente'
        }
        
        for col, default in required_columns.items():
            if col not in df.columns:
                df[col] = default
        
        return df
    
    def get_clean_data(self):
        """Obtener datos limpios"""
        return self.df_clean

# Función principal para usar en Streamlit
def get_hr_data(spreadsheet_url_or_id, sheet_name=None):
    """Función principal para obtener datos de RRHH"""
    try:
        # Obtener secrets
        credentials_info = dict(st.secrets["gcp_service_account"])
        connector = HRSheetsConnector()
        
        # Conectar y obtener datos
        if connector.connect_to_sheets(credentials_info, spreadsheet_url_or_id, sheet_name):
            if connector.extract_data():
                if connector.transform_data():
                    return connector.get_clean_data()
        
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ Error obteniendo datos: {str(e)}")
        return pd.DataFrame()
