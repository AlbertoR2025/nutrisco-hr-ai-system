"""
Generador de Resúmenes IA para Sistema RRHH Chatbot
Usa OpenAI GPT-4o para análisis de conversaciones
"""

import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class AISummarizer:
    def __init__(self):
        # Cliente OpenAI usando la variable de entorno OPENAI_API_KEY
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"

    def generar_analisis_temas_emergentes(self, df_conversaciones, dias=7):
        """
        Analiza conversaciones y detecta temas emergentes con IA
        """
        if df_conversaciones.empty:
            return "No hay conversaciones disponibles para analizar."

        # Filtrar últimos N días
        df_reciente = df_conversaciones.copy()
        df_reciente["fecha"] = pd.to_datetime(df_reciente["fecha"])
        fecha_limite = pd.Timestamp.now() - pd.Timedelta(days=dias)
        df_reciente = df_reciente[df_reciente["fecha"] >= fecha_limite]

        if df_reciente.empty:
            return f"No hay conversaciones en los últimos {dias} días."

        # Preparar contexto
        contexto = self._crear_contexto_conversaciones(df_reciente)

        prompt = f"""
Actúa como un consultor senior de RRHH especializado en análisis de datos de atención a colaboradores.

Tienes una base de consultas de los últimos {dias} días. A partir de los datos siguientes:

{contexto}

Genera un informe ejecutivo que incluya:

1) Temas más frecuentes (Top 3), explicando brevemente qué los caracteriza.
2) Temas emergentes que estén creciendo en volumen o criticidad.
3) Riesgos o alertas que el equipo de RRHH debería monitorear.
4) Recomendaciones concretas (máximo 5) para mejorar la atención y la experiencia del colaborador.

Formato:
- Estilo profesional, claro y enfocado en decisiones.
- Usa subtítulos y viñetas donde ayuden a la lectura.
- Máximo 400 palabras.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Eres un analista experto en RRHH que proporciona "
                            "insights claros y accionables."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error al generar análisis: {str(e)}"

    def generar_resumen_ejecutivo(self, df_conversaciones):
        """
        Genera resumen ejecutivo del estado actual
        """
        if df_conversaciones.empty:
            return "No hay datos disponibles."

        contexto = self._crear_contexto_general(df_conversaciones)

        prompt = f"""
Eres un consultor estratégico de RRHH que prepara informes para gerencia.

Con los siguientes datos del sistema de atención RRHH:

{contexto}

Redacta un RESUMEN EJECUTIVO que incluya:

1) Estado general del servicio (breve diagnóstico).
2) Principales tipos de consultas y qué indican sobre las necesidades de los colaboradores.
3) Problemas o fricciones detectadas en el proceso de atención.
4) Entre 2 y 3 recomendaciones estratégicas priorizadas (con foco en impacto y rapidez de implementación).

Formato:
- Tono profesional, orientado a decisiones.
- Texto corrido con párrafos claros (no más de 5).
- Máximo 300 palabras.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un consultor estratégico de RRHH.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=600,
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error: {str(e)}"

    def generar_recomendaciones(self, df_conversaciones):
        """
        Genera recomendaciones específicas basadas en los datos
        """
        if df_conversaciones.empty:
            return "No hay datos suficientes."

        # Calcular métricas clave
        total = len(df_conversaciones)
        derivados = (
            df_conversaciones["derivado"].sum()
            if "derivado" in df_conversaciones.columns
            else 0
        )
        tasa_derivacion = (derivados / total * 100) if total > 0 else 0

        categorias_top = (
            df_conversaciones["categoria"]
            .value_counts()
            .head(5)
            .to_dict()
            if "categoria" in df_conversaciones.columns
            else {}
        )

        prompt = f"""
Actúas como experto en mejora de procesos RRHH.

Con base en estas métricas:

- Total consultas: {total}
- Tasa de derivación: {tasa_derivacion:.1f}%
- Top categorías: {categorias_top}

Diseña un listado de 5 RECOMENDACIONES ACCIONABLES para mejorar:

- La eficiencia del chatbot y del equipo RRHH.
- La experiencia del colaborador.
- La reducción de derivaciones innecesarias.

Formato:
1. Título de la recomendación
   - Descripción breve
   - Acción concreta a ejecutar (qué, quién, cuándo)

Lenguaje claro, orientado a gestión. Máximo 250 palabras.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en optimización de procesos RRHH.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error: {str(e)}"

    def _crear_contexto_conversaciones(self, df):
        """Crea contexto resumido de conversaciones"""
        total = len(df)
        categorias = (
            df["categoria"].value_counts().to_dict()
            if "categoria" in df.columns
            else {}
        )
        areas = (
            df["area"].value_counts().to_dict() if "area" in df.columns else {}
        )
        derivados = df["derivado"].sum() if "derivado" in df.columns else 0

        # Ejemplos de consultas (primeras 5)
        ejemplos = "\n".join(
            [
                f"- {row.get('categoria', 'Sin categoría')}: "
                f"{str(row.get('consulta', ''))[:100]}..."
                for _, row in df.head(5).iterrows()
            ]
        )

        contexto = f"""
Total de consultas: {total}
Categorías: {categorias}
Áreas: {areas}
Consultas derivadas: {derivados}

Ejemplos de consultas recientes:
{ejemplos}
"""
        return contexto

    def _crear_contexto_general(self, df):
        """Crea contexto general del sistema"""
        total = len(df)
        if "derivado" in df.columns:
            resueltos = (~df["derivado"]).sum()
        else:
            resueltos = 0
        tasa_resolucion = (resueltos / total * 100) if total > 0 else 0

        categorias = (
            df["categoria"].value_counts().head(5).to_dict()
            if "categoria" in df.columns
            else {}
        )

        contexto = f"""
Total conversaciones: {total}
Tasa de resolución: {tasa_resolucion:.1f}%
Top 5 categorías: {categorias}
"""
        return contexto
