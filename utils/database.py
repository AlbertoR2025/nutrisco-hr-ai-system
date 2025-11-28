"""
Gestor de Base de Datos SQLite para Sistema RRHH Nutrisco
Maneja conversaciones, búsquedas y temas emergentes
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

DATA_EXCEL = Path("data") / "Consultas-Atencion-Personas-Enriquecido.xlsx"


class ChatDatabase:
    def __init__(self, db_path="data/conversaciones.db"):
        self.db_path = db_path
        Path("data").mkdir(exist_ok=True)
        self.init_db()
        self.seed_from_excel()  # cargar datos iniciales si está vacío

    def init_db(self):
        """Crear tablas si no existen"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabla principal de conversaciones
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fecha_resolucion TIMESTAMP,
                usuario TEXT,
                area TEXT,
                consulta TEXT NOT NULL,
                respuesta TEXT NOT NULL,
                categoria TEXT DEFAULT 'General',
                resuelto_primer_contacto BOOLEAN DEFAULT 1,
                tiempo_respuesta_mins INTEGER,
                derivado BOOLEAN DEFAULT 0,
                tema_emergente BOOLEAN DEFAULT 0,
                satisfaccion INTEGER DEFAULT NULL
            )
        """
        )

        # Tabla de temas emergentes detectados
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS temas_emergentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_deteccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tema TEXT NOT NULL,
                frecuencia INTEGER DEFAULT 1,
                descripcion TEXT,
                estado TEXT DEFAULT 'Pendiente'
            )
        """
        )

        # Log de búsquedas del equipo RRHH
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS busqueda_historial (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_buscador TEXT,
                query_busqueda TEXT,
                filtros TEXT,
                resultado_encontrado BOOLEAN DEFAULT 1
            )
        """
        )

        conn.commit()
        conn.close()

    def seed_from_excel(self):
        """Si la tabla está vacía, cargar datos desde el Excel del repo"""
        if not DATA_EXCEL.exists():
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        total = cursor.execute(
            "SELECT COUNT(*) FROM conversaciones"
        ).fetchone()[0]

        if total == 0:
            df = pd.read_excel(DATA_EXCEL)

            # Ajusta estos mapeos según las columnas reales de tu Excel
            # Ejemplo de mapeo típico:
            columnas_map = {
                "Fecha": "fecha",
                "Usuario": "usuario",
                "Área": "area",
                "Consulta": "consulta",
                "Respuesta": "respuesta",
                "Categoría": "categoria",
                "Derivado": "derivado",
                "Tiempo_Respuesta_min": "tiempo_respuesta_mins",
            }
            df = df.rename(columns=columnas_map)

            # Asegurar columnas mínimas
            for col in [
                "fecha",
                "usuario",
                "area",
                "consulta",
                "respuesta",
                "categoria",
                "derivado",
                "tiempo_respuesta_mins",
            ]:
                if col not in df.columns:
                    df[col] = None

            df.to_sql(
                "conversaciones",
                conn,
                if_exists="append",
                index=False,
            )

        conn.close()

    def guardar_conversacion(
        self,
        usuario,
        consulta,
        respuesta,
        categoria="General",
        area=None,
        tiempo_respuesta_mins=None,
        derivado=False,
    ):
        """Guardar nueva conversación"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        fecha_resolucion = datetime.now()

        cursor.execute(
            """
            INSERT INTO conversaciones 
            (usuario, area, consulta, respuesta, categoria, 
             fecha_resolucion, tiempo_respuesta_mins, derivado, 
             resuelto_primer_contacto)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                usuario,
                area,
                consulta,
                respuesta,
                categoria,
                fecha_resolucion,
                tiempo_respuesta_mins,
                derivado,
                not derivado,
            ),
        )

        conn.commit()
        conn.close()
        return cursor.lastrowid

    def obtener_conversaciones(self, limite=500, offset=0):
        """Obtener conversaciones con paginación"""
        conn = sqlite3.connect(self.db_path)
        query = f"""
            SELECT * FROM conversaciones 
            ORDER BY fecha DESC 
            LIMIT {limite} OFFSET {offset}
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def buscar_conversaciones(
        self,
        query_texto=None,
        fecha_desde=None,
        fecha_hasta=None,
        categoria=None,
        area=None,
        derivado=None,
    ):
        """Búsqueda avanzada de conversaciones"""
        conn = sqlite3.connect(self.db_path)

        conditions = []
        params = []

        if query_texto:
            conditions.append("(consulta LIKE ? OR respuesta LIKE ?)")
            params.extend([f"%{query_texto}%", f"%{query_texto}%"])

        if fecha_desde:
            conditions.append("DATE(fecha) >= ?")
            params.append(fecha_desde)

        if fecha_hasta:
            conditions.append("DATE(fecha) <= ?")
            params.append(fecha_hasta)

        if categoria and categoria != "Todas":
            conditions.append("categoria = ?")
            params.append(categoria)

        if area and area != "Todas":
            conditions.append("area = ?")
            params.append(area)

        if derivado is not None:
            conditions.append("derivado = ?")
            params.append(1 if derivado else 0)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        query = f"""
            SELECT * FROM conversaciones 
            WHERE {where_clause}
            ORDER BY fecha DESC
        """

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    def registrar_busqueda(
        self,
        usuario_buscador,
        query_busqueda,
        filtros=None,
        resultado_encontrado=True,
    ):
        """Registrar búsqueda del equipo RRHH"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO busqueda_historial 
            (usuario_buscador, query_busqueda, filtros, resultado_encontrado)
            VALUES (?, ?, ?, ?)
        """,
            (usuario_buscador, query_busqueda, str(filtros), resultado_encontrado),
        )

        conn.commit()
        conn.close()

    def calcular_kpis(self, fecha_desde=None, fecha_hasta=None):
        """Calcular KPIs principales"""
        conn = sqlite3.connect(self.db_path)

        conditions = "1=1"
        params = []

        if fecha_desde:
            conditions += " AND DATE(fecha) >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            conditions += " AND DATE(fecha) <= ?"
            params.append(fecha_hasta)

        # Total consultas
        query_total = (
            f"SELECT COUNT(*) as total FROM conversaciones WHERE {conditions}"
        )
        total = pd.read_sql_query(query_total, conn, params=params)["total"].iloc[0]
        total = int(total)

        # Consultas derivadas
        query_derivados = f"""
            SELECT COUNT(*) as derivados
            FROM conversaciones 
            WHERE {conditions} AND derivado = 1
        """
        derivados = pd.read_sql_query(
            query_derivados, conn, params=params
        )["derivados"].iloc[0]
        derivados = int(derivados)

        # Consultas resueltas en primer contacto
        resueltas_primer_contacto = total - derivados

        if total > 0:
            tasa_derivacion = (derivados / total) * 100
            tasa_resolucion = (resueltas_primer_contacto / total) * 100
        else:
            tasa_derivacion = 0.0
            tasa_resolucion = 0.0

        # Limitar a 0–100 por seguridad
        tasa_derivacion = max(0.0, min(100.0, tasa_derivacion))
        tasa_resolucion = max(0.0, min(100.0, tasa_resolucion))

        # Tiempo promedio de respuesta
        query_tiempo = f"""
            SELECT AVG(tiempo_respuesta_mins) as tiempo_promedio
            FROM conversaciones 
            WHERE {conditions} AND tiempo_respuesta_mins IS NOT NULL
        """
        tiempo_prom = pd.read_sql_query(
            query_tiempo, conn, params=params
        )["tiempo_promedio"].iloc[0]
        tiempo_prom = float(tiempo_prom) if pd.notna(tiempo_prom) else 0.0

        # Temas emergentes (últimos 7 días)
        fecha_7dias = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        query_emergentes = """
            SELECT COUNT(DISTINCT categoria) as temas_nuevos
            FROM conversaciones
            WHERE DATE(fecha) >= ? AND tema_emergente = 1
        """
        temas_nuevos = pd.read_sql_query(
            query_emergentes, conn, params=[fecha_7dias]
        )["temas_nuevos"].iloc[0]
        temas_nuevos = int(temas_nuevos)

        conn.close()

        return {
            "total_consultas": total,
            "tasa_resolucion_primer_contacto": round(tasa_resolucion, 1),
            "tiempo_promedio_respuesta_mins": round(tiempo_prom, 1),
            "temas_emergentes_nuevos": temas_nuevos,
            "tasa_derivacion": round(tasa_derivacion, 1),
            "consultas_resueltas": resueltas_primer_contacto,
            "consultas_derivadas": derivados,
        }

    def obtener_top_temas(
        self, limite=10, fecha_desde=None, fecha_hasta=None
    ):
        """Top temas más recurrentes"""
        conn = sqlite3.connect(self.db_path)

        conditions = "1=1"
        params = []

        if fecha_desde:
            conditions += " AND DATE(fecha) >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            conditions += " AND DATE(fecha) <= ?"
            params.append(fecha_hasta)

        query = f"""
            SELECT 
                categoria,
                COUNT(*) as frecuencia
            FROM conversaciones
            WHERE {conditions}
            GROUP BY categoria
            ORDER BY frecuencia DESC
            LIMIT {limite}
        """

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    def obtener_evolucion_temporal(
        self, periodo="dia", fecha_desde=None, fecha_hasta=None
    ):
        """Evolución temporal de consultas"""
        conn = sqlite3.connect(self.db_path)

        if periodo == "dia":
            formato = "%Y-%m-%d"
            label = "Día"
        elif periodo == "semana":
            formato = "%Y-W%W"
            label = "Semana"
        elif periodo == "mes":
            formato = "%Y-%m"
            label = "Mes"
        else:
            formato = "%Y-%m-%d"
            label = "Fecha"

        conditions = "1=1"
        params = []

        if fecha_desde:
            conditions += " AND DATE(fecha) >= ?"
            params.append(fecha_desde)

        if fecha_hasta:
            conditions += " AND DATE(fecha) <= ?"
            params.append(fecha_hasta)

        query = f"""
            SELECT 
                strftime('{formato}', fecha) as periodo,
                COUNT(*) as total
            FROM conversaciones
            WHERE {conditions}
            GROUP BY periodo
            ORDER BY periodo
        """

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        df.columns = [label, "Total"]
        return df

    def obtener_distribucion_areas(self):
        """Distribución por área"""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT 
                COALESCE(area, 'Sin Área') as area,
                COUNT(*) as total
            FROM conversaciones
            GROUP BY area
            ORDER BY total DESC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def detectar_temas_emergentes(
        self, umbral_frecuencia=5, dias_recientes=7
    ):
        """Detectar temas que aumentaron su frecuencia recientemente"""
        conn = sqlite3.connect(self.db_path)

        fecha_limite = (datetime.now() - timedelta(days=dias_recientes)).strftime(
            "%Y-%m-%d"
        )

        query = f"""
            SELECT 
                categoria,
                COUNT(*) as frecuencia_reciente
            FROM conversaciones
            WHERE DATE(fecha) >= '{fecha_limite}'
            GROUP BY categoria
            HAVING frecuencia_reciente >= {umbral_frecuencia}
            ORDER BY frecuencia_reciente DESC
        """

        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
