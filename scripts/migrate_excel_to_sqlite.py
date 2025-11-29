"""
Script de migración de Excel a SQLite - VERSIÓN FINAL
Migra datos del archivo de consultas de atención a personas
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

# Base del proyecto (carpeta raíz)
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from utils.database import ChatDatabase  # CLAVE

def migrar_excel_a_sqlite(
    excel_path=BASE_DIR / "data" / "Consultas-Atencion-Personas.xlsx"
):
    """
    Migrar datos de Excel a SQLite
    """
    print("🚀 Iniciando migración de Excel a SQLite...")
    print(f"📂 Archivo: {excel_path}")

    if not Path(excel_path).exists():
        print(f"❌ ERROR: No se encontró el archivo {excel_path}")
        return False

    # Leer Excel
    try:
        print("📖 Leyendo archivo Excel (hoja por defecto)...")
        df = pd.read_excel(excel_path)
        print(f"✅ Leído correctamente: {len(df)} registros encontrados")
    except Exception as e:
        print(f"❌ ERROR al leer Excel: {e}")
        return False

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
            # Columnas reales del Excel:
            # Fecha, Canal, Consulta, Observación, Respuesta, Estado, Nombre, Nombre Área
            fecha = row.get("Fecha", datetime.now())

            # Priorizar Observación como detalle de la pregunta; si está vacío, usar Consulta
            consulta = row.get("Observación", "")
            if not consulta or str(consulta).lower() in ["nan", "none"]:
                consulta = row.get("Consulta", "")

            respuesta = row.get("Respuesta", "")
            usuario = row.get("Nombre", "Anónimo")
            area = row.get("Nombre Área", None)
            estado = row.get("Estado", "")

            # Usar la columna Consulta como categoría general
            categoria = row.get("Consulta", "General")

            # Convertir a string y limpiar
            consulta = str(consulta).strip()
            respuesta = str(respuesta).strip()

            # Validar datos mínimos: al menos debe haber una consulta
            if consulta.lower() in ["nan", "none", ""]:
                registros_fallidos += 1
                continue

            # Determinar si fue derivado usando Estado (opcional)
            tipo_resolucion = str(estado).lower() if estado is not None else ""
            derivado = "derivado" in tipo_resolucion
            # Si no hay info, asumimos resuelto en primer contacto si no está derivado
            resuelto_primer_contacto = not derivado

            # Guardar en base de datos
            db.guardar_conversacion(
                usuario=str(usuario) if usuario and str(usuario) != "nan" else "Anónimo",
                area=str(area) if area and str(area) != "nan" else None,
                consulta=consulta,
                respuesta=respuesta if respuesta.lower() not in ["nan", "none", ""] else "(sin respuesta registrada)",
                categoria=str(categoria) if categoria and str(categoria) != "nan" else "General",
                tiempo_respuesta_mins=None,  # no disponible en este Excel
                derivado=derivado,
            )

            registros_exitosos += 1

            if (idx + 1) % 50 == 0:
                print(f"   ✅ Procesados: {idx + 1}/{len(df)}")

        except Exception as e:
            registros_fallidos += 1
            if idx < 5:
                print(f"   ⚠️  Registro {idx+1}: {e}")
            continue

    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE MIGRACIÓN")
    print("=" * 60)
    print(f"✅ Registros migrados exitosamente: {registros_exitosos}")
    print(f"❌ Registros omitidos: {registros_fallidos}")
    if len(df) > 0:
        print(f"📈 Tasa de éxito: {(registros_exitosos / len(df) * 100):.1f}%")
    print("\n🎉 ¡Migración completada!")
    print(f"💾 Base de datos guardada en: data/conversaciones.db")

    # Verificar datos migrados
    print("\n🔍 Verificando datos migrados...")
    df_verificacion = db.obtener_conversaciones(limite=5)

    if not df_verificacion.empty:
        print("✅ Primeros 5 registros en BD:")
        print(df_verificacion[["fecha", "usuario", "categoria", "area"]].head())

        print("\n📊 Estadísticas de la BD:")
        kpis = db.calcular_kpis()
        print(f"  - Total consultas: {kpis['total_consultas']}")
        print(f"  - Resolución 1er contacto: {kpis['tasa_resolucion_primer_contacto']}%")
        print(f"  - Derivadas: {kpis['consultas_derivadas']}")
    else:
        print("⚠️  No se pudieron verificar los datos")

    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🏢 NUTRISCO - SISTEMA RRHH")
    print("📦 Script de Migración Excel → SQLite")
    print("=" * 60 + "\n")

    exito = migrar_excel_a_sqlite()

    if exito:
        print("\n" + "=" * 60)
        print("✅ MIGRACIÓN COMPLETADA CON ÉXITO")
        print("=" * 60)
        print("\n🚀 Próximo paso: streamlit run app.py")
    else:
        print("\n❌ Migración falló. Revisa los errores arriba.")

    input("\nPresiona ENTER para cerrar...")
