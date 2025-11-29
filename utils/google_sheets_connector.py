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
        
    def connect_to_sheets(self, credentials_info, spreadsheet_url_or_id):
        """Conectar con Google Sheets - VERSIÓN SIMPLIFICADA Y ROBUSTA"""
        try:
            # Configurar scope
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Crear credenciales
            creds = Credentials.from_service_account_info(credentials_info, scopes=scope)
            client = gspread.authorize(creds)
            
            # EXTRAER EL ID DEL SPREADSHEET DE FORMA ROBUSTA
            spreadsheet_id = self.extract_spreadsheet_id(spreadsheet_url_or_id)
            if not spreadsheet_id:
                st.error("❌ No se pudo extraer el ID del spreadsheet")
                return False
            
            st.sidebar.write(f"🔗 Conectando con Spreadsheet ID: {spreadsheet_id}")
            
            # Intentar abrir el spreadsheet
            try:
                spreadsheet = client.open_by_key(spreadsheet_id)
                st.sidebar.write(f"✅ Spreadsheet abierto: {spreadsheet.title}")
            except Exception as e:
                st.error(f"❌ No se pudo abrir el spreadsheet: {str(e)}")
                st.info(f"💡 Verifica que el Sheet esté compartido con: {credentials_info.get('client_email')}")
                return False
            
            # Obtener lista de hojas
            worksheets = spreadsheet.worksheets()
            if not worksheets:
                st.error("❌ El spreadsheet no tiene hojas")
                return False
            
            sheet_names = [ws.title for ws in worksheets]
            st.sidebar.write(f"📋 Hojas disponibles: {sheet_names}")
            
            # USAR LA PRIMERA HOJA (más simple y confiable)
            self.sheet = worksheets[0]
            st.sidebar.write(f"✅ Usando hoja: {self.sheet.title}")
            
            return True
            
        except Exception as e:
            st.error(f"❌ Error crítico conectando con Google Sheets: {str(e)}")
            return False
    
    def extract_spreadsheet_id(self, spreadsheet_url_or_id):
        """Extraer el ID del spreadsheet de forma robusta"""
        # Si ya es un ID (solo letras, números y guiones)
        if re.match(r'^[a-zA-Z0-9-_]+$', str(spreadsheet_url_or_id)):
            return spreadsheet_url_or_id
        
        # Si es una URL, extraer el ID
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'd/([a-zA-Z0-9-_]+)/'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, str(spreadsheet_url_or_id))
            if match:
                return match.group(1)
        
        return None
    
    def extract_data(self):
        """Extraer datos de la hoja"""
        try:
            records = self.sheet.get_all_records()
            
            if not records:
                st.warning("⚠️ La hoja está vacía o no tiene datos en formato de tabla")
                return False
                
            self.df_raw = pd.DataFrame(records)
            
            if self.df_raw.empty:
                st.warning("⚠️ No se pudieron extraer datos")
                return False
                
            st.sidebar.write(f"✅ Datos extraídos: {len(self.df_raw)} registros")
            return True
            
        except Exception as e:
            st.error(f"❌ Error extrayendo datos: {str(e)}")
            return False
    
    def transform_data(self):
        """Transformación básica de datos"""
        if self.df_raw is None or self.df_raw.empty:
            return False
        
        df = self.df_raw.copy()
        
        # Normalizar nombres de columnas
        df.columns = [self.normalize_column_name(col) for col in df.columns]
        
        # Mapeo básico de columnas
        column_mapping = {
            'fecha': 'fecha_creacion',
            'fechacreacion': 'fecha_creacion',
            'date': 'fecha_creacion',
            'usuario': 'usuario',
            'nombre': 'usuario',
            'colaborador': 'usuario',
            'area': 'area',
            'departamento': 'area',
            'consulta': 'consulta',
            'pregunta': 'consulta',
            'respuesta': 'respuesta',
            'solucion': 'respuesta',
            'estado': 'estado',
            'status': 'estado'
        }
        
        # Aplicar mapeo
        for old_pattern, new_name in column_mapping.items():
            for col in df.columns:
                if old_pattern in col:
                    df[new_name] = df[col]
                    break
        
        # Limpiar fechas
        if 'fecha_creacion' in df.columns:
            df['fecha_creacion'] = pd.to_datetime(df['fecha_creacion'], errors='coerce', dayfirst=True)
            df['fecha_creacion'] = df['fecha_creacion'].fillna(datetime.now())
        
        # Validar datos críticos
        if 'usuario' not in df.columns:
            df['usuario'] = 'Usuario no especificado'
        if 'consulta' not in df.columns:
            df['consulta'] = 'Consulta no especificada'
        if 'respuesta' not in df.columns:
            df['respuesta'] = 'En proceso'
        if 'estado' not in df.columns:
            df['estado'] = 'Pendiente'
        if 'area' not in df.columns:
            df['area'] = 'RRHH'
        
        self.df_clean = df
        st.sidebar.write(f"✅ Datos transformados: {len(self.df_clean)} registros")
        return True
    
    def normalize_column_name(self, name):
        """Normalizar nombre de columna"""
        if pd.isna(name):
            return 'columna_desconocida'
        
        name_str = str(name).strip().lower()
        replacements = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n', ' ': '_'}
        
        for old, new in replacements.items():
            name_str = name_str.replace(old, new)
        
        return name_str
    
    def get_clean_data(self):
        """Obtener datos limpios"""
        return self.df_clean

# Función principal
def get_hr_data(spreadsheet_url_or_id):
    """Función principal para obtener datos"""
    try:
        credentials_info = dict(st.secrets["gcp_service_account"])
        connector = HRSheetsConnector()
        
        if connector.connect_to_sheets(credentials_info, spreadsheet_url_or_id):
            if connector.extract_data():
                if connector.transform_data():
                    return connector.get_clean_data()
        
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return pd.DataFrame()
