"""
Agregar columnas usuario y area a la BD
"""

import sqlite3

db_path = "data/conversaciones.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Agregar columna usuario
try:
    cursor.execute("ALTER TABLE conversaciones ADD COLUMN usuario TEXT")
    print("✅ Columna 'usuario' agregada")
except:
    print("⚠️  Columna 'usuario' ya existe")

# Agregar columna area (si no existe)
try:
    cursor.execute("ALTER TABLE conversaciones ADD COLUMN area TEXT")
    print("✅ Columna 'area' agregada")
except:
    print("⚠️  Columna 'area' ya existe")

conn.commit()
conn.close()

print("\n✅ BD actualizada correctamente")
