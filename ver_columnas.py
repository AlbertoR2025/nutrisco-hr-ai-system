import pandas as pd

# Leer el Excel GRANDE
df = pd.read_excel("data/Consultas-Atencion-Personas-Enriquecido.xlsx")

# Ver las primeras filas y columnas
print("="*60)
print("COLUMNAS DEL EXCEL ENRIQUECIDO:")
print("="*60)
for i, col in enumerate(df.columns.tolist(), 1):
    print(f"{i}. {col}")

print("\n" + "="*60)
print("PRIMERAS 3 FILAS (solo algunas columnas clave):")
print("="*60)

# Intentar mostrar las columnas que parecen importantes
columnas_mostrar = []
for col in df.columns:
    col_lower = col.lower()
    if any(keyword in col_lower for keyword in ['fecha', 'consulta', 'pregunta', 'respuesta', 'categoria', 'tema', 'usuario', 'email']):
        columnas_mostrar.append(col)

if columnas_mostrar:
    print(df[columnas_mostrar].head(3))
else:
    print("No se encontraron columnas obvias de consultas")
    print("\nMostrando todas las columnas:")
    print(df.head(3))

print("\n" + "="*60)
print(f"TOTAL DE FILAS: {len(df)}")
