"""
Google Sheets Database Adapter para Streamlit Cloud
Mantiene compatibilidad total con ChatDatabase original
"""

import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

class GoogleSheetsDatabase:
    def __init__(self):
        # URL pública de tu Google Sheets
        self.sheet_url = "https://docs.google.com/spreadsheets/d/1JqFay6hXlUuURwZFANmr6FXARZqfH7tI/export?format=csv"
        self.df = None
        self._cargar_datos()
    
    def _cargar_datos(self):
        """Carga y procesa datos desde Google Sheets"""
        try:
            # 1. CARGAR DATOS DESDE GOOGLE SHEETS
            self.df = pd.read_csv(self.sheet_url)
            
            # 2. MAPEO DE COLUMNAS (igual a tu Excel original)
            column_mapping = {
                'Fecha ': 'fecha',
                'Nombre ': 'usuario', 
                'Área': 'area',
                'Consulta': 'categoria',
                'Observación': 'consulta',
                'Respuesta': 'respuesta',
                'Estado': 'estado'
            }
            
            # Renombrar solo columnas que existen
            existing_columns = {k: v for k, v in column_mapping.items() if k in self.df.columns}
            self.df = self.df.rename(columns=existing_columns)
            
            # 3. PROCESAMIENTO DE DATOS
            self._procesar_datos()
            
            st.success(f"✅ Datos cargados: {len(self.df)} registros")
            
        except Exception as e:
            st.error(f"❌ Error cargando Google Sheets: {e}")
            self.df = pd.DataFrame()
    
    def _procesar_datos(self):
        """Procesamiento idéntico a tu versión local"""
        # Procesar fechas
        if 'fecha' in self.df.columns:
            self.df['fecha'] = pd.to_datetime(self.df['fecha'], errors='coerce')
            self.df = self.df.dropna(subset=['fecha'])
        
        # Procesar estados y derivados
        if 'estado' in self.df.columns:
            self.df['estado'] = self.df['estado'].astype(str)
            self.df['derivado'] = self.df['estado'].str.lower().str.contains('derivado')
            self.df['resuelto_primer_contacto'] = ~self.df['derivado']
        
        # Columnas adicionales para compatibilidad
        if 'tiempo_respuesta_mins' not in self.df.columns:
            self.df['tiempo_respuesta_mins'] = None
        
        self.df['tema_emergente'] = False
        self.df['satisfaccion'] = None
    
    def calcular_kpis(self, fecha_desde=None, fecha_hasta=None):
        """CALCULA KPIs - Mismo método que tu SQLite original"""
        if self.df.empty:
            return self._kpis_vacios()
        
        try:
            # Filtrar por fechas
            df_filtrado = self._filtrar_por_fechas(fecha_desde, fecha_hasta)
            
            # Cálculos idénticos a tu versión
            total = len(df_filtrado)
            derivados = int(df_filtrado['derivado'].sum()) if 'derivado' in df_filtrado.columns else 0
            resueltas = total - derivados

            # Tasas
            if total > 0:
                tasa_derivacion = derivados / total * 100
                tasa_resolucion = resueltas / total * 100
            else:
                tasa_derivacion = 0.0
                tasa_resolucion = 0.0

            # Tiempo de respuesta
            if "tiempo_respuesta_mins" in df_filtrado.columns:
                t = df_filtrado["tiempo_respuesta_mins"].dropna()
                tiempo_prom = float(t.mean()) if not t.empty else 0.0
            else:
                tiempo_prom = 0.0

            # Temas emergentes (últimos 7 días)
            fecha_7d = datetime.now() - timedelta(days=7)
            dff7 = df_filtrado[df_filtrado["fecha"] >= fecha_7d]
            
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
            st.error(f"Error calculando KPIs: {e}")
            return self._kpis_vacios()

    # =============================================
    # MÉTODOS COMPATIBLES - MISMA INTERFAZ QUE SQLite
    # =============================================

    def obtener_top_temas(self, limite=10, fecha_desde=None, fecha_hasta=None):
        """Top temas más recurrentes"""
        if self.df.empty:
            return pd.DataFrame(columns=['categoria', 'frecuencia'])
        
        df_filtrado = self._filtrar_por_fechas(fecha_desde, fecha_hasta)
        
        if 'categoria' not in df_filtrado.columns:
            return pd.DataFrame(columns=['categoria', 'frecuencia'])
        
        top_temas = df_filtrado['categoria'].value_counts().head(limite).reset_index()
        top_temas.columns = ['categoria', 'frecuencia']
        return top_temas

    def obtener_evolucion_temporal(self, periodo='dia', fecha_desde=None, fecha_hasta=None):
        """Evolución temporal de consultas"""
        if self.df.empty:
            return pd.DataFrame()
        
        df_filtrado = self._filtrar_por_fechas(fecha_desde, fecha_hasta)
        
        if periodo == 'dia':
            evolucion = df_filtrado.groupby(df_filtrado['fecha'].dt.date).size().reset_index()
            evolucion.columns = ['Fecha', 'Total']
            evolucion['Fecha'] = pd.to_datetime(evolucion['Fecha'])
        
        return evolucion

    def obtener_distribucion_areas(self):
        """Distribución por área"""
        if self.df.empty or 'area' not in self.df.columns:
            return pd.DataFrame(columns=['area', 'total'])
        
        distribucion = self.df['area'].fillna('Sin Área').value_counts().reset_index()
        distribucion.columns = ['area', 'total']
        return distribucion.sort_values('total', ascending=False)

    def detectar_temas_emergentes(self, umbral_frecuencia=5, dias_recientes=7):
        """Detecta temas emergentes"""
        if self.df.empty:
            return pd.DataFrame(columns=['categoria', 'frecuencia_reciente'])
        
        fecha_limite = datetime.now() - timedelta(days=dias_recientes)
        df_reciente = self.df[self.df['fecha'] >= fecha_limite]
        
        if 'categoria' not in df_reciente.columns:
            return pd.DataFrame(columns=['categoria', 'frecuencia_reciente'])
        
        temas_recientes = df_reciente['categoria'].value_counts().reset_index()
        temas_recientes.columns = ['categoria', 'frecuencia_reciente']
        return temas_recientes[temas_recientes['frecuencia_reciente'] >= umbral_frecuencia]

    def obtener_conversaciones(self, limite=500):
        """Obtiene conversaciones"""
        if self.df.empty:
            return pd.DataFrame()
        return self.df.head(limite).copy()

    def buscar_conversaciones(self, query_texto=None, fecha_desde=None, fecha_hasta=None, 
                             categoria=None, area=None, derivado=None):
        """Búsqueda de conversaciones"""
        if self.df.empty:
            return pd.DataFrame()
        
        df_filtrado = self._filtrar_por_fechas(fecha_desde, fecha_hasta)
        
        # Aplicar filtros
        if query_texto:
            mask = (df_filtrado['consulta'].str.contains(query_texto, case=False, na=False) |
                   df_filtrado['respuesta'].str.contains(query_texto, case=False, na=False))
            df_filtrado = df_filtrado[mask]
        
        if categoria and categoria != "Todas":
            df_filtrado = df_filtrado[df_filtrado['categoria'] == categoria]
        
        if area and area != "Todas":
            df_filtrado = df_filtrado[df_filtrado['area'] == area]
        
        if derivado is not None:
            df_filtrado = df_filtrado[df_filtrado['derivado'] == derivado]
        
        return df_filtrado

    # =============================================
    # MÉTODOS DUMMY PARA COMPATIBILIDAD
    # =============================================

    def registrar_busqueda(self, usuario_buscador, query_busqueda, filtros=None, resultado_encontrado=True):
        """No implementado en Sheets - solo para compatibilidad"""
        pass

    def guardar_conversacion(self, *args, **kwargs):
        """No implementado en Sheets - solo para compatibilidad"""
        pass

    # =============================================
    # MÉTODOS AUXILIARES INTERNOS
    # =============================================

    def _filtrar_por_fechas(self, fecha_desde=None, fecha_hasta=None):
        """Filtra DataFrame por rango de fechas"""
        df_filtrado = self.df.copy()
        
        if fecha_desde:
            fecha_desde_dt = pd.to_datetime(fecha_desde)
            df_filtrado = df_filtrado[df_filtrado['fecha'] >= fecha_desde_dt]
        
        if fecha_hasta:
            fecha_hasta_dt = pd.to_datetime(fecha_hasta)
            df_filtrado = df_filtrado[df_filtrado['fecha'] <= fecha_hasta_dt]
        
        return df_filtrado

    def _kpis_vacios(self):
        """Retorna KPIs vacíos"""
        return {
            "total_consultas": 0,
            "tasa_resolucion_primer_contacto": 0.0,
            "tiempo_promedio_respuesta_mins": 0.0,
            "temas_emergentes_nuevos": 0,
            "tasa_derivacion": 0.0,
            "consultas_resueltas": 0,
            "consultas_derivadas": 0,
        }