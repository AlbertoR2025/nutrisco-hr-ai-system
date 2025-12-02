import streamlit as st
import sqlite3
import os
from datetime import datetime
import pandas as pd
import qrcode
from io import BytesIO
import base64

# Configuración de página
st.set_page_config(
    page_title="Chatbot RRHH Nutrisco",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado
st.markdown("""
<style>
    .stChatInput { position: fixed; bottom: 20px; width: 70%; left: 15%; }
    .main { padding-bottom: 100px; }
    .nutrisco-header { 
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Header personalizado
st.markdown("""
<div class="nutrisco-header">
    <h1>🤖 Chatbot RRHH Nutrisco</h1>
    <p>Consulta sobre políticas, beneficios y trámites de recursos humanos</p>
</div>
""", unsafe_allow_html=True)

# Inicializar base de datos SQLite
@st.cache_resource
def init_db():
    conn = sqlite3.connect('data/chatbot.db', check_same_thread=False)
    c = conn.cursor()
    
    # Tabla de usuarios
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE,
            name TEXT,
            department TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de conversaciones
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            user_query TEXT,
            bot_response TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de preguntas frecuentes
    c.execute('''
        CREATE TABLE IF NOT EXISTS faq (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            question TEXT,
            answer TEXT
        )
    ''')
    
    # Insertar FAQs si no existen
    faqs = [
        ('Vacaciones', '¿Cómo solicito vacaciones?', 'Las vacaciones se solicitan a través del portal empleados.nutrisco.cl con al menos 15 días de anticipación.'),
        ('Bonos', '¿Cuándo se pagan los bonos?', 'Los bonos de productividad se pagan al final de cada trimestre. El bono navideño se paga el 15 de diciembre.'),
        ('Licencia', '¿Qué hacer en caso de licencia médica?', '1. Notificar a tu jefe inmediato\n2. Enviar certificado a RRHH\n3. Completar formulario L-01 en el portal'),
        ('Seguro', '¿Cómo funciona el seguro de salud?', 'Contamos con Seguro Consalud. Teléfono: 600 400 2000\nPortal: consalud.cl/nutrisco\nCobertura familiar disponible.'),
        ('Horario', '¿Cuál es el horario de trabajo?', 'Lunes a Viernes: 9:00 - 18:00\nHorario flexible: Entrada entre 8:00-9:30\nAlmuerzo: 13:00-14:00'),
        ('Home Office', '¿Cuál es la política de teletrabajo?', 'Máximo 3 días por semana de teletrabajo previa autorización del jefe. Requiere conexión estable y cumplimiento de metas.')
    ]
    
    c.execute("SELECT COUNT(*) FROM faq")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO faq (category, question, answer) VALUES (?, ?, ?)", faqs)
    
    conn.commit()
    return conn

# Inicializar DB
conn = init_db()

# Sistema de login simple
def login_system():
    st.sidebar.title("🔐 Acceso Empleado")
    
    # Opción 1: ID de empleado
    employee_id = st.sidebar.text_input("ID de Empleado", placeholder="Ej: NUT-00123")
    
    # Opción 2: Email corporativo
    email = st.sidebar.text_input("Email Nutrisco", placeholder="nombre@nutrisco.cl")
    
    if st.sidebar.button("Ingresar", type="primary"):
        if employee_id or email:
            # Guardar en sesión
            st.session_state.logged_in = True
            st.session_state.user_id = employee_id or email.split('@')[0]
            st.session_state.user_email = email if '@nutrisco.cl' in email else f"{employee_id}@nutrisco.cl"
            st.rerun()
        else:
            st.sidebar.error("Ingresa tu ID o email")

# Función para buscar respuesta
def get_answer(query):
    query_lower = query.lower()
    
    # Buscar en FAQs
    c = conn.cursor()
    c.execute("SELECT answer FROM faq WHERE question LIKE ? OR answer LIKE ?", 
              (f'%{query}%', f'%{query}%'))
    result = c.fetchone()
    
    if result:
        return result[0]
    
    # Respuestas predefinidas
    responses = {
        'vacaciones': """**🏖️ POLÍTICA DE VACACIONES NUTRISCO**
        
- **1-5 años de antigüedad:** 15 días hábiles
- **5-10 años de antigüedad:** 20 días hábiles  
- **+10 años de antigüedad:** 30 días hábiles

📅 **Cómo solicitar:**
1. Portal: empleados.nutrisco.cl
2. Mínimo 15 días de anticipación
3. Aprobación del jefe directo

ℹ️ Más info: beneficios@nutrisco.com""",
        
        'bono': """**💰 SISTEMA DE BONOS**
        
- **Bono Productividad:** Fin de cada trimestre (Mar, Jun, Sep, Dic)
- **Bono Navidad:** 15 de Diciembre
- **Bono Resultados:** Evaluación anual (Enero)

📊 **Cálculo:** Basado en metas individuales y de equipo

💼 **Consulta específica:** Contactar a tu jefe directo""",
        
        'licencia': """**🏥 LICENCIA MÉDICA - PROCEDIMIENTO**
        
1. **Notificación Inmediata:** Informar a tu jefe
2. **Certificado Médico:** Enviar a RRHH en 48 horas
3. **Formulario L-01:** Completar en portal empleados
4. **Seguimiento:** Coordinación con Consalud

📞 **Contacto RRHH:** +56 2 2345 6789
📧 **Email:** licencias@nutrisco.cl""",
        
        'seguro': """**🏥 SEGURO DE SALUD CONSALUD**
        
- **Teléfono Emergencias:** 600 400 2000
- **Portal:** consalud.cl/nutrisco
- **Usuario:** Tu RUT (sin puntos ni guión)
- **Clave:** Primeras 4 letras nombre + últimos 4 RUT

🏥 **Cobertura Familiar:** Cónyuge e hijos menores de 25 años

💊 **Farmacias:** Red cerrada con 30% descuento""",
        
        'salario': """**💰 INFORMACIÓN DE REMUNERACIONES**
        
- **Día de pago:** Último día hábil del mes
- **Método:** Transferencia bancaria
- **Desglose:** Disponible en portal empleados

📋 **Liquidaciones:** Acceso histórico completo
📊 **Bonos:** Aparecen como ítems separados

❓ **Consultas:** contabilidad@nutrisco.cl"""
    }
    
    # Buscar palabras clave
    for keyword, answer in responses.items():
        if keyword in query_lower:
            return answer
    
    # Respuesta por defecto
    return """Hola, soy el chatbot de RRHH de Nutrisco. 

Puedo ayudarte con información sobre:
• Vacaciones y días libres
• Bonos y remuneraciones  
• Licencias médicas
• Seguro de salud
• Políticas de teletrabajo
• Beneficios para empleados

¿En qué tema específico necesitas ayuda?"""

# Guardar conversación
def save_conversation(employee_id, query, response):
    c = conn.cursor()
    c.execute(
        "INSERT INTO conversations (employee_id, user_query, bot_response) VALUES (?, ?, ?)",
        (employee_id, query, response)
    )
    conn.commit()

# Generar código QR
def generate_qr():
    url = "https://nutrisco-chatbot.streamlit.app"
    qr = qrcode.make(url)
    
    # Convertir a base64 para mostrar en Streamlit
    buffered = BytesIO()
    qr.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str, url

# Main app
def main():
    # Inicializar sesión
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Sidebar con login
    with st.sidebar:
        if not st.session_state.logged_in:
            login_system()
        else:
            st.success(f"✅ Conectado como: {st.session_state.user_id}")
            if st.button("Cerrar sesión"):
                st.session_state.logged_in = False
                st.session_state.chat_history = []
                st.rerun()
            
            st.divider()
            
            # Generar QR
            st.subheader("📱 Acceso Rápido")
            qr_img, url = generate_qr()
            st.image(f"data:image/png;base64,{qr_img}", width=200)
            st.caption(f"URL: {url}")
            
            if st.button("📥 Descargar QR"):
                st.download_button(
                    label="Descargar QR",
                    data=BytesIO(base64.b64decode(qr_img)),
                    file_name="nutrisco_chatbot_qr.png",
                    mime="image/png"
                )
            
            st.divider()
            
            # Estadísticas
            st.subheader("📊 Estadísticas")
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM conversations WHERE employee_id = ?", 
                     (st.session_state.user_id,))
            total_chats = c.fetchone()[0]
            st.metric("Consultas realizadas", total_chats)
    
    # Contenido principal
    if not st.session_state.logged_in:
        st.info("👈 Por favor, ingresa tus credenciales en la barra lateral para comenzar")
        
        # Mostrar información general
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**🏖️ Vacaciones**\nConsulta días disponibles y solicitudes")
        with col2:
            st.info("**💰 Bonos**\nInformación sobre pagos y beneficios")
        with col3:
            st.info("**🏥 Salud**\nSeguro médico y licencias")
        
        return
    
    # Chat principal
    st.subheader("💬 Chat de Consultas")
    
    # Mostrar historial
    for chat in st.session_state.chat_history:
        if chat['role'] == 'user':
            with st.chat_message("user"):
                st.markdown(chat['content'])
        else:
            with st.chat_message("assistant"):
                st.markdown(chat['content'])
    
    # Input de chat
    if prompt := st.chat_input("Escribe tu pregunta sobre RRHH..."):
        # Agregar al historial
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Mostrar mensaje usuario
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Obtener respuesta
        with st.spinner("Buscando en la base de conocimiento..."):
            response = get_answer(prompt)
            
            # Guardar en DB
            save_conversation(st.session_state.user_id, prompt, response)
            
            # Mostrar respuesta
            with st.chat_message("assistant"):
                st.markdown(response)
            
            # Agregar al historial
            st.session_state.chat_history.append({"role": "assistant", "content": response})
    
    # Sección de ayuda
    with st.expander("💡 Temas frecuentes"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🏖️ Vacaciones", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": "vacaciones"})
                st.rerun()
            if st.button("💰 Bonos", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": "bonos"})
                st.rerun()
            if st.button("🏥 Licencia", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": "licencia médica"})
                st.rerun()
        
        with col2:
            if st.button("💼 Seguro", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": "seguro de salud"})
                st.rerun()
            if st.button("🏠 Home Office", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": "teletrabajo"})
                st.rerun()
            if st.button("📅 Horarios", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": "horario de trabajo"})
                st.rerun()

if __name__ == "__main__":
    main()