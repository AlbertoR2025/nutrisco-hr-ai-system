"""
Búsqueda de Historial - Back-end para Equipo RRHH
Herramienta de búsqueda rápida y contextualizada
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from utils.database import ChatDatabase

# Configuración de página
st.set_page_config(
    page_title="Búsqueda Historial - Nutrisco",
    page_icon="🔍",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
header, footer, [data-testid="stToolbar"], [data-testid="stDeployButton"],
[data-testid="stDecoration"] {
    display: none !important;
}

.stApp {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}

.search-header {
    background: linear-gradient(135deg, #ea580c 0%, #dc2626 100%);
    padding: 2rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 2rem;
    text-align: center;
}

.result-card {
    background: #1e293b;
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 4px solid #f97316;
    margin-bottom: 1rem;
}

.result-card h4 {
    color: #f97316;
    margin: 0 0 0.5rem 0;
}

.result-card p {
    color: #cbd5e1;
    margin: 0.3rem 0;
}

.result-card .meta {
    color: #64748b;
    font-size: 0.85rem;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="search-header">
    <h1>🔍 Búsqueda de Historial</h1>
    <p>Herramienta de búsqueda rápida para el equipo RRHH</p>
</div>
""", unsafe_allow_html=True)

# Inicializar base de datos
db = ChatDatabase()

# Identificación del usuario buscador
if "usuario_buscador" not in st.session_state:
    with st.form("form_buscador"):
        st.markdown("### 👤 Identificación del Usuario")
        usuario = st.text_input("Nombre o Email", placeholder="tu.nombre@nutrisco.com")
        
        if st.form_submit_button("Continuar"):
            if usuario:
                st.session_state.usuario_buscador = usuario
                st.rerun()
            else:
                st.error("Por favor ingresa tu nombre o email")
    st.stop()

# Inicializar filtros en session_state
if "fecha_desde_busqueda" not in st.session_state:
    st.session_state.fecha_desde_busqueda = datetime.now() - timedelta(days=60)
if "fecha_hasta_busqueda" not in st.session_state:
    st.session_state.fecha_hasta_busqueda = datetime.now() + timedelta(days=1)

# Panel de búsqueda
st.markdown("### 🔎 Filtros de Búsqueda")

col1, col2, col3 = st.columns(3)

with col1:
    query_texto = st.text_input(
        "🔍 Buscar por texto",
        placeholder="Ej: licencia médica, BUK, liquidación...",
        help="Busca en consultas y respuestas"
    )

with col2:
    fecha_desde = st.date_input(
        "📅 Desde",
        value=st.session_state.fecha_desde_busqueda,
        key="fecha_desde_input_busqueda"
    )

with col3:
    fecha_hasta = st.date_input(
        "📅 Hasta",
        value=st.session_state.fecha_hasta_busqueda,
        key="fecha_hasta_input_busqueda"
    )

col4, col5, col6 = st.columns(3)

with col4:
    df_temp = db.obtener_conversaciones(limite=1000)
    categorias = ["Todas"] + sorted(df_temp['categoria'].dropna().unique().tolist()) if not df_temp.empty else ["Todas"]
    categoria_filtro = st.selectbox("📂 Categoría", categorias)

with col5:
    if not df_temp.empty:
        # Limpiar valores raros en área
        areas_validas = (
            df_temp['area']
            .fillna('Sin Área')
            .replace('#REF!', 'Sin Área')
            .unique()
            .tolist()
        )
        areas = ["Todas"] + sorted(areas_validas)
    else:
        areas = ["Todas"]

    area_filtro = st.selectbox("🏢 Área", areas)
with col6:
    derivado_filtro = st.selectbox("📧 Estado", ["Todos", "Solo Derivados", "Solo No Derivados"])

# Botón de búsqueda
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

with col_btn1:
    buscar = st.button("🔍 Buscar", use_container_width=True, type="primary")

with col_btn2:
    if st.button("🔄 Limpiar Filtros", use_container_width=True):
        st.session_state.fecha_desde_busqueda = datetime.now() - timedelta(days=60)
        st.session_state.fecha_hasta_busqueda = datetime.now() + timedelta(days=1)
        st.rerun()

# Realizar búsqueda
if buscar or query_texto:
    fecha_desde_str = fecha_desde.strftime("%Y-%m-%d")
    fecha_hasta_str = fecha_hasta.strftime("%Y-%m-%d")
    
    categoria_busqueda = None if categoria_filtro == "Todas" else categoria_filtro
    area_busqueda = None if area_filtro == "Todas" else area_filtro
    
    derivado_busqueda = None
    if derivado_filtro == "Solo Derivados":
        derivado_busqueda = True
    elif derivado_filtro == "Solo No Derivados":
        derivado_busqueda = False
    
    resultados = db.buscar_conversaciones(
        query_texto=query_texto if query_texto else None,
        fecha_desde=fecha_desde_str,
        fecha_hasta=fecha_hasta_str,
        categoria=categoria_busqueda,
        area=area_busqueda,
        derivado=derivado_busqueda
    )
    
    filtros_aplicados = {
        'texto': query_texto,
        'fecha_desde': fecha_desde_str,
        'fecha_hasta': fecha_hasta_str,
        'categoria': categoria_filtro,
        'area': area_filtro,
        'derivado': derivado_filtro
    }
    
    db.registrar_busqueda(
        usuario_buscador=st.session_state.usuario_buscador,
        query_busqueda=query_texto if query_texto else "Búsqueda con filtros",
        filtros=filtros_aplicados,
        resultado_encontrado=len(resultados) > 0
    )
    
    st.markdown("---")
    st.markdown(f"### 📊 Resultados: {len(resultados)} conversaciones encontradas")
    
    if len(resultados) > 0:
        col_exp1, col_exp2 = st.columns([1, 4])
        
        with col_exp1:
            csv = resultados.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exportar a Excel",
                data=csv,
                file_name=f"busqueda_historial_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        for idx, row in resultados.head(50).iterrows():
            with st.container():
                col_r1, col_r2 = st.columns([3, 1])
                
                with col_r1:
                    usuario_badge = f'<span style="background: #f97316; color: white; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-size: 0.9rem;">👤 {row["usuario"]}</span>'
                    
                    st.markdown(f"""
                    <div class="result-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                            <h4 style="margin: 0;">💬 {row['categoria']}</h4>
                            {usuario_badge}
                        </div>
                        <p><strong>Consulta:</strong> {row['consulta'][:200]}{'...' if len(row['consulta']) > 200 else ''}</p>
                        <p><strong>Respuesta:</strong> {row['respuesta'][:200]}{'...' if len(row['respuesta']) > 200 else ''}</p>
                        <p class="meta">
                            📅 {row['fecha']} | 
                            🏢 {row['area'] if pd.notna(row['area']) else 'Sin área'} |
                            {'📧 Derivado' if row['derivado'] else '✅ Resuelto'}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_r2:
                    with st.expander("Ver completo"):
                        st.markdown(f"**Usuario:** {row['usuario']}")
                        st.markdown(f"**Área:** {row['area'] if pd.notna(row['area']) else 'No especificada'}")
                        st.markdown(f"**Consulta completa:**\n{row['consulta']}")
                        st.markdown(f"**Respuesta completa:**\n{row['respuesta']}")
                        st.markdown(f"**Tiempo respuesta:** {row['tiempo_respuesta_mins']:.1f} min" if pd.notna(row['tiempo_respuesta_mins']) else "No disponible")
        
        if len(resultados) > 50:
            st.info(f"Mostrando las primeras 50 de {len(resultados)} conversaciones. Usa 'Exportar a Excel' para ver todas.")
    
    else:
        st.info("No se encontraron resultados con los filtros aplicados. Intenta con otros criterios.")

else:
    st.info("👆 Usa los filtros de arriba para buscar conversaciones en el historial")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #64748b;'>Búsqueda de Historial • Nutrisco © 2025</p>", unsafe_allow_html=True)
