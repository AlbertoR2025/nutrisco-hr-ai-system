"""
Script para cargar TODOS los datos del Excel de Belén a la BD
Lee la pestaña "Atención 2025"
"""

import pandas as pd
import sqlite3
from datetime import datetime
import os
import sys

# Agregar path del proyecto
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def limpiar_y_cargar_datos():
    """Carga todos los datos del Excel a la BD"""
    
    print("=" * 60)
    print("🚀 CARGANDO DATOS COMPLETOS DEL EXCEL")
    print("=" * 60)
    
    # 1. Leer Excel - PESTAÑA ESPECÍFICA
    print("\n📂 Leyendo archivo Excel...")
    excel_file = "data/Consultas Atención Personas.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ ERROR: No se encuentra el archivo {excel_file}")
        return
    
    # Leer pestaña "Atención 2025"
    df = pd.read_excel(excel_file, sheet_name="Atención 2025")
    print(f"✅ Archivo leído (pestaña 'Atención 2025'): {len(df)} filas")
    
    # 2. Limpiar datos
    print("\n🧹 Limpiando datos...")
    
    # Eliminar filas sin consulta
    df_limpio = df[df['Consulta'].notna()].copy()
    print(f"   - Filas con consulta válida: {len(df_limpio)}")
    
    # NO eliminar duplicados (mantener todas las conversaciones)
    print(f"   - Manteniendo todas las conversaciones: {len(df_limpio)}")
    
    # 3. Categorizar automáticamente
    print("\n🏷️  Categorizando conversaciones...")
    
    def categorizar(row):
        """Categoriza basándose en la consulta y observación"""
        consulta = str(row.get('Consulta', '')).lower()
        observacion = str(row.get('Observación', '')).lower()
        texto = consulta + " " + observacion
        
        if any(word in texto for word in ['beneficio', 'buk', 'aguinaldo', 'bono']):
            return 'Beneficios'
        elif any(word in texto for word in ['asistencia', 'licencia', 'permiso', 'ausencia', 'marcar']):
            return 'Asistencia'
        elif any(word in texto for word in ['contrato', 'finiquito', 'anexo']):
            return 'Contrato'
        elif any(word in texto for word in ['documento', 'certificado', 'liquidación']):
            return 'Documentos'
        elif any(word in texto for word in ['vestimenta', 'epp', 'uniforme', 'talla']):
            return 'Vestimenta y EPP'
        elif any(word in texto for word in ['asignación familiar', 'carga']):
            return 'Asignación Familiar'
        elif any(word in texto for word in ['remuneración', 'sueldo', 'pago', 'banco']):
            return 'Remuneraciones'
        elif any(word in texto for word in ['reclutamiento', 'selección', 'postulante']):
            return 'Reclutamiento y Selección'
        elif any(word in texto for word in ['seguro', 'salud', 'isapre']):
            return 'Seguro de Salud'
        elif any(word in texto for word in ['credencial', 'tarjeta']):
            return 'Credencial'
        else:
            return 'Otro'
    
    df_limpio['Categoría'] = df_limpio.apply(categorizar, axis=1)
    
    # Mostrar distribución de categorías
    print("\n📊 Distribución de categorías:")
    cat_counts = df_limpio['Categoría'].value_counts()
    for cat, count in cat_counts.items():
        print(f"   - {cat}: {count} ({count/len(df_limpio)*100:.1f}%)")
    
    # 4. Detectar derivaciones
    if 'Estado' in df_limpio.columns:
        df_limpio['Derivado'] = df_limpio['Estado'].apply(
            lambda x: x in ['Abierto', 'Pendiente', 'Derivado a SST'] if pd.notna(x) else False
        )
    else:
        df_limpio['Derivado'] = False
    
    # 5. Conectar a BD
    print("\n💾 Conectando a base de datos...")
    db_path = "data/conversaciones.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 6. Insertar datos
    print(f"\n📥 Insertando {len(df_limpio)} conversaciones...")
    
    insertados = 0
    errores = 0
    
    for idx, row in df_limpio.iterrows():
        try:
            # Preparar fecha
            if 'Fecha' in row and pd.notna(row['Fecha']):
                try:
                    fecha = pd.to_datetime(row['Fecha']).strftime('%Y-%m-%d %H:%M:%S')
                except:
                    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            else:
                fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Obtener valores de forma segura
            canal = row.get('Canal', 'Sin Canal') if pd.notna(row.get('Canal')) else 'Sin Canal'
            respuesta = row.get('Respuesta', 'Pendiente') if pd.notna(row.get('Respuesta')) else 'Pendiente'
            
            # Obtener usuario (Nombre)
            usuario = row.get('Nombre', 'Anónimo') if pd.notna(row.get('Nombre')) else 'Anónimo'
            
            # Obtener área
            area = row.get('Área', canal) if pd.notna(row.get('Área')) else canal
            
            # Insertar CON usuario y area
            cursor.execute("""
                INSERT INTO conversaciones (
                    fecha, usuario, area, categoria, consulta, respuesta, derivado
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                fecha,
                str(usuario)[:100],
                str(area)[:100],
                row['Categoría'],
                str(row['Consulta'])[:500],
                str(respuesta)[:500],
                row['Derivado']
            ))
            
            insertados += 1
            
            # Progress bar
            if insertados % 50 == 0:
                print(f"   ✅ {insertados} conversaciones insertadas...")
        
        except Exception as e:
            errores += 1
            if errores <= 5:
                print(f"   ⚠️  Error en fila {idx}: {str(e)[:100]}")
    
    # 7. Commit y cerrar
    conn.commit()
    conn.close()
    
    # 8. Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE CARGA")
    print("=" * 60)
    print(f"✅ Conversaciones insertadas: {insertados}")
    print(f"⚠️  Errores encontrados: {errores}")
    if insertados + errores > 0:
        print(f"📈 Tasa de éxito: {(insertados/(insertados+errores)*100):.1f}%")
    print("=" * 60)
    
    # 9. Verificar BD
    conn = sqlite3.connect(db_path)
    total_bd = pd.read_sql_query("SELECT COUNT(*) as total FROM conversaciones", conn)['total'][0]
    conn.close()
    
    print(f"\n💾 Total de conversaciones en BD: {total_bd}")
    print("✅ ¡Carga completada exitosamente!")

if __name__ == "__main__":
    limpiar_y_cargar_datos()
