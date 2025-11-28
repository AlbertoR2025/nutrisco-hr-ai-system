"""
Script de migración de Excel a SQLite - VERSIÓN FINAL
Migra datos del archivo enriquecido con 340 consultas
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Agregar ruta del proyecto al path
sys.path.append(str(Path(__file__).parent.parent))

from utils.database import ChatDatabase

def migrar_excel_a_sqlite(excel_path="data/Consultas-Atencion-Personas-Enriquecido.xlsx"):
    """
    Migrar datos de Excel enriquecido a SQLite
    """
    print("🚀 Iniciando migración de Excel ENRIQUECIDO a SQLite...")
    print(f"📂 Archivo: {excel_path}")
    
    # Verificar que existe el Excel
    if not Path(excel_path).exists():
        print(f"❌ ERROR: No se encontró el archivo {excel_path}")
        return False
    
    # Leer Excel - Hoja 'Atención_Completa'
    try:
        print("📖 Leyendo archivo Excel (Hoja: Atención_Completa)...")
        df = pd.read_excel(excel_path, sheet_name='Atención_Completa')
        print(f"✅ Leído correctamente: {len(df)} registros encontrados")
    except Exception as e:
        print(f"❌ ERROR al leer Excel: {e}")
        print("\n💡 Probando con hoja por defecto...")
        try:
            df = pd.read_excel(excel_path)
            print(f"✅ Leído correctamente: {len(df)} registros encontrados")
        except Exception as e2:
            print(f"❌ ERROR: {e2}")
            return False
    
    # Mostrar columnas disponibles
    print(f"\n📋 Total de columnas: {len(df.columns)}")
    
    # Inicializar base de datos
    print("\n💾 Inicializando base de datos SQLite...")
    db = ChatDatabase()
    
    # Migrar datos
    print(f"\n🔄 Migrando {len(df)} registros...")
    registros_exitosos = 0
    registros_fallidos = 0
    
    for idx, row in df.iterrows():
        try:
            # Extraer datos del Excel enriquecido
            fecha = row.get('Fecha_Consulta', row.get('Fecha ', datetime.now()))
            consulta = row.get('Consulta', '')
            respuesta = row.get('Respuesta', '')
            usuario = row.get('Nombre Completo', row.get('Nombre ', 'Anónimo'))
            area = row.get('Nombre Área', row.get('Área', None))
            categoria = row.get('Categoria_Consulta', 'General')
            tipo_resolucion = row.get('Tipo_Resolucion', '')
            
            # Convertir a string y limpiar
            consulta = str(consulta).strip()
            respuesta = str(respuesta).strip()
            
            # Validar datos mínimos
            if consulta.lower() in ['nan', 'none', ''] or respuesta.lower() in ['nan', 'none', '']:
                registros_fallidos += 1
                continue
            
            # Determinar si fue derivado
            derivado = 'derivado' in tipo_resolucion.lower() if tipo_resolucion else False
            resuelto_primer_contacto = 'primer contacto' in tipo_resolucion.lower() if tipo_resolucion else not derivado
            
            # Guardar en base de datos
            db.guardar_conversacion(
                usuario=str(usuario) if usuario and str(usuario) != 'nan' else 'Anónimo',
                area=str(area) if area and str(area) != 'nan' else None,
                consulta=consulta,
                respuesta=respuesta,
                categoria=str(categoria) if categoria and str(categoria) != 'nan' else 'General',
                tiempo_respuesta_mins=None,  # No tenemos este dato
                derivado=derivado
            )
            
            registros_exitosos += 1
            
            # Progreso cada 50 registros
            if (idx + 1) % 50 == 0:
                print(f"   ✅ Procesados: {idx + 1}/{len(df)}")
        
        except Exception as e:
            registros_fallidos += 1
            if idx < 5:  # Solo mostrar primeros errores
                print(f"   ⚠️  Registro {idx+1}: {e}")
            continue
    
    # Resumen final
    print("\n" + "="*60)
    print("📊 RESUMEN DE MIGRACIÓN")
    print("="*60)
    print(f"✅ Registros migrados exitosamente: {registros_exitosos}")
    print(f"❌ Registros omitidos: {registros_fallidos}")
    print(f"📈 Tasa de éxito: {(registros_exitosos/len(df)*100):.1f}%")
    print("\n🎉 ¡Migración completada!")
    print(f"💾 Base de datos guardada en: data/conversaciones.db")
    
    # Verificar datos migrados
    print("\n🔍 Verificando datos migrados...")
    df_verificacion = db.obtener_conversaciones(limite=5)
    
    if not df_verificacion.empty:
        print(f"✅ Primeros 5 registros en BD:")
        print(df_verificacion[['fecha', 'usuario', 'categoria', 'area']].head())
        
        # Mostrar estadísticas
        print("\n📊 Estadísticas de la BD:")
        kpis = db.calcular_kpis()
        print(f"  - Total consultas: {kpis['total_consultas']}")
        print(f"  - Resolución 1er contacto: {kpis['tasa_resolucion_primer_contacto']}%")
        print(f"  - Derivadas: {kpis['consultas_derivadas']}")
    else:
        print("⚠️  No se pudieron verificar los datos")
    
    return True

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🏢 NUTRISCO - SISTEMA RRHH")
    print("📦 Script de Migración Excel → SQLite")
    print("="*60 + "\n")
    
    # Ejecutar migración
    exito = migrar_excel_a_sqlite()
    
    if exito:
        print("\n" + "="*60)
        print("✅ MIGRACIÓN COMPLETADA CON ÉXITO")
        print("="*60)
        print("\n🚀 Próximo paso: streamlit run app.py")
    else:
        print("\n❌ Migración falló. Revisa los errores arriba.")
    
    input("\nPresiona ENTER para cerrar...")
