import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

class AdvancedHRDatabase:
    def __init__(self, data_path='data/cleaned_hr_data.csv'):
        self.data_path = data_path
        self.df = self._load_data()
        
    def _load_data(self):
        """Cargar datos limpios con cache"""
        try:
            df = pd.read_csv(self.data_path, parse_dates=['fecha_creacion'])
            print(f"✅ Datos cargados: {len(df)} registros")
            return df
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return pd.DataFrame()
    
    def get_kpis(self, fecha_desde=None, fecha_hasta=None):
        """Calcular KPIs avanzados"""
        df_filtrado = self._filter_by_date(fecha_desde, fecha_hasta)
        
        if df_filtrado.empty:
            return self._get_empty_kpis()
        
        # KPIs principales
        total_consultas = len(df_filtrado)
        
        # Resolución primer contacto
        resolucion_primer_contacto = self._calculate_first_contact_resolution(df_filtrado)
        
        # Tiempo promedio de respuesta
        tiempo_promedio = self._calculate_avg_response_time(df_filtrado)
        
        # Temas emergentes (últimos 7 días)
        temas_emergentes = self._calculate_emerging_topics(df_filtrado)
        
        # KPIs secundarios
        consultas_resueltas = len(df_filtrado[df_filtrado['estado'] == 'completado'])
        consultas_derivadas = len(df_filtrado[df_filtrado['derivado_a'].notna()])
        promedio_diario = self._calculate_daily_average(df_filtrado)
        eficiencia_equipo = self._calculate_team_efficiency(df_filtrado)
        
        return {
            'total_consultas': total_consultas,
            'resolucion_primer_contacto': resolucion_primer_contacto,
            'tiempo_promedio_respuesta': tiempo_promedio,
            'temas_emergentes': temas_emergentes,
            'consultas_resueltas': consultas_resueltas,
            'tasa_resolucion': (consultas_resueltas / total_consultas * 100) if total_consultas > 0 else 0,
            'consultas_derivadas': consultas_derivadas,
            'tasa_derivacion': (consultas_derivadas / total_consultas * 100) if total_consultas > 0 else 0,
            'promedio_diario': promedio_diario,
            'eficiencia_equipo': eficiencia_equipo
        }
    
    def _filter_by_date(self, fecha_desde, fecha_hasta):
        """Filtrar por rango de fechas"""
        df = self.df.copy()
        
        if fecha_desde:
            fecha_desde = pd.to_datetime(fecha_desde)
            df = df[df['fecha_creacion'] >= fecha_desde]
        
        if fecha_hasta:
            fecha_hasta = pd.to_datetime(fecha_hasta)
            df = df[df['fecha_creacion'] <= fecha_hasta]
        
        return df
    
    def _calculate_first_contact_resolution(self, df):
        """Calcular tasa de resolución en primer contacto"""
        if 'resolucion_primer_contacto' in df.columns:
            resolved_first = df['resolucion_primer_contacto'].sum()
            return (resolved_first / len(df)) * 100
        return 75.0  # Valor por defecto
    
    def _calculate_avg_response_time(self, df):
        """Calcular tiempo promedio de respuesta"""
        if 'tiempo_respuesta_horas' in df.columns:
            return df['tiempo_respuesta_horas'].mean()
        return 24.0  # Valor por defecto
    
    def _calculate_emerging_topics(self, df):
        """Calcular temas emergentes (últimos 7 días)"""
        last_7_days = datetime.now() - timedelta(days=7)
        emerging = df[df['fecha_creacion'] >= last_7_days]
        
        if 'categoria_estandar' in emerging.columns:
            return emerging['categoria_estandar'].nunique()
        return 0
    
    def _calculate_daily_average(self, df):
        """Calcular promedio diario de consultas"""
        if df.empty:
            return 0.0
        
        days_count = (df['fecha_creacion'].max() - df['fecha_creacion'].min()).days + 1
        return len(df) / days_count if days_count > 0 else len(df)
    
    def _calculate_team_efficiency(self, df):
        """Calcular eficiencia del equipo"""
        if df.empty or 'tiempo_respuesta_horas' not in df.columns:
            return 100.0
        
        # Eficiencia basada en tiempo de respuesta
        avg_time = df['tiempo_respuesta_horas'].mean()
        if avg_time <= 24:  # Meta: menos de 24 horas
            return 100.0
        elif avg_time <= 48:
            return 80.0
        else:
            return 60.0
    
    def _get_empty_kpis(self):
        """Retornar KPIs vacíos"""
        return {
            'total_consultas': 0,
            'resolucion_primer_contacto': 0.0,
            'tiempo_promedio_respuesta': 0.0,
            'temas_emergentes': 0,
            'consultas_resueltas': 0,
            'tasa_resolucion': 0.0,
            'consultas_derivadas': 0,
            'tasa_derivacion': 0.0,
            'promedio_diario': 0.0,
            'eficiencia_equipo': 100.0
        }
    
    def get_top_topics(self, limit=10, fecha_desde=None, fecha_hasta=None):
        """Obtener temas más recurrentes"""
        df_filtrado = self._filter_by_date(fecha_desde, fecha_hasta)
        
        if df_filtrado.empty or 'categoria_estandar' not in df_filtrado.columns:
            return pd.DataFrame({'Tema': [], 'Cantidad': []})
        
        top_topics = df_filtrado['categoria_estandar'].value_counts().head(limit)
        return top_topics.reset_index().rename(columns={'index': 'Tema', 'categoria_estandar': 'Cantidad'})
    
    def get_trends_data(self):
        """Obtener datos para análisis de tendencias"""
        df = self.df.copy()
        
        if df.empty:
            return pd.DataFrame()
        
        # Agrupar por mes y categoría
        df['mes'] = df['fecha_creacion'].dt.to_period('M')
        trends = df.groupby(['mes', 'categoria_estandar']).size().reset_index(name='cantidad')
        trends['mes'] = trends['mes'].astype(str)
        
        return trends
    
    def get_department_metrics(self):
        """Obtener métricas por departamento"""
        df = self.df.copy()
        
        if df.empty or 'departamento' not in df.columns:
            return pd.DataFrame()
        
        dept_metrics = df.groupby('departamento').agg({
            'fecha_creacion': 'count',
            'tiempo_respuesta_horas': 'mean',
            'resolucion_primer_contacto': 'mean'
        }).rename(columns={
            'fecha_creacion': 'total_consultas',
            'tiempo_respuesta_horas': 'tiempo_promedio_horas',
            'resolucion_primer_contacto': 'tasa_resolucion_primer_contacto'
        }).round(2)
        
        return dept_metrics.reset_index()