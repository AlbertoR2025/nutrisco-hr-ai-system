# Crear database.py corregido
@"
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

class ChatDatabase:
    def __init__(self):
        # EN RENDER: Usar /tmp para persistencia entre reinicios
        if os.getenv('RENDER'):
            self.db_path = \"/tmp/nutrisco_hr.db\"
        else:
            self.db_path = \"data/nutrisco_hr.db\"
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        \"\"\"Inicializar base de datos con datos de ejemplo si está vacía\"\"\"
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Crear tablas si no existen
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS consultas_rrhh (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                consulta TEXT,
                respuesta TEXT,
                categoria TEXT,
                derivado BOOLEAN DEFAULT FALSE,
                satisfaccion INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_conversaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                consulta TEXT,
                respuesta TEXT,
                categoria TEXT,
                derivado BOOLEAN DEFAULT FALSE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS base_conocimiento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pregunta TEXT,
                respuesta TEXT,
                categoria TEXT,
                frecuencia INTEGER DEFAULT 0
            )
        ''')
        
        # VERIFICAR SI LA BASE ESTÁ VACÍA Y AGREGAR DATOS DE EJEMPLO
        cursor.execute(\"SELECT COUNT(*) as count FROM consultas_rrhh\")
        count = cursor.fetchone()['count']
        
        if count == 0:
            print(\"🔧 Inicializando base de datos con datos de ejemplo...\")
            self._insertar_datos_ejemplo(conn)
        
        conn.commit()
        conn.close()
    
    def _insertar_datos_ejemplo(self, conn):
        \"\"\"Insertar datos de ejemplo para pruebas\"\"\"
        cursor = conn.cursor()
        
        # Datos de ejemplo para consultas_rrhh
        consultas_ejemplo = [
            (\"¿Cómo solicito mis vacaciones?\", \"Puedes solicitar vacaciones through el portal de empleados...\", \"Vacaciones\", False, 5),
            (\"Necesito ayuda con mi certificado laboral\", \"Los certificados laborales se generan automaticamente...\", \"Documentación\", False, 4),
            (\"Problema con mi pago\", \"Por favor contacta a nóminas con tu número de empleado...\", \"Nómina\", True, 3),
            (\"¿Cuáles son los beneficios de salud?\", \"Tenemos cobertura de salud con la aseguradora XYZ...\", \"Beneficios\", False, 5),
            (\"Quiero actualizar mis datos personales\", \"Puedes actualizar tus datos en el portal del empleado...\", \"Datos Personales\", False, 4)
        ]
        
        for consulta, respuesta, categoria, derivado, satisfaccion in consultas_ejemplo:
            cursor.execute('''
                INSERT INTO consultas_rrhh (consulta, respuesta, categoria, derivado, satisfaccion)
                VALUES (?, ?, ?, ?, ?)
            ''', (consulta, respuesta, categoria, derivado, satisfaccion))
        
        # Datos de ejemplo para base_conocimiento
        conocimiento_ejemplo = [
            (\"vacaciones\", \"Las vacaciones se solicitan through el portal con 15 días de anticipación\", \"Vacaciones\"),
            (\"certificado laboral\", \"Los certificados se generan automáticamente cada mes\", \"Documentación\"),
            (\"pago nómina\", \"La nómina se paga los últimos 5 días hábiles del mes\", \"Nómina\"),
            (\"beneficios salud\", \"Cobertura médica completa para empleado y familia directa\", \"Beneficios\"),
            (\"actualizar datos\", \"Los datos personales se actualizan en el portal del empleado\", \"Datos Personales\")
        ]
        
        for pregunta, respuesta, categoria in conocimiento_ejemplo:
            cursor.execute('''
                INSERT INTO base_conocimiento (pregunta, respuesta, categoria)
                VALUES (?, ?, ?)
            ''', (pregunta, respuesta, categoria))
        
        conn.commit()

    # ... (MANTÉN EL RESTO DE TUS MÉTODOS EXISTENTES AQUÍ)
    # [PEGA AQUÍ EL RESTO DE TUS MÉTODOS ORIGINALES]
\"\"@ | Out-File -FilePath \"utils/database.py\" -Encoding utf8