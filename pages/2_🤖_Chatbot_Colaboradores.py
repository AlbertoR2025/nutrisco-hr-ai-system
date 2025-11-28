"""
Chatbot para Colaboradores - Front-end
Interfaz de chat para empleados con IA
"""

import streamlit as st
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import sys
from pathlib import Path

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from utils.database import ChatDatabase

load_dotenv()

# Configuración de página
st.set_page_config(
    page_title="Chatbot Colaboradores - Nutrisco",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS personalizado
st.markdown("""
<style>
header, footer, [data-testid="stToolbar"], [data-testid="stDeployButton"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"] {
    display: none !important;
}

.stApp {background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);}
.block-container {max-width: 800px !important; margin: 0 auto !important; padding: 2rem 1rem 100px 1rem !important;}

.header {
    background: linear-gradient(135deg, #ea580c 0%, #dc2626 100%);
    padding: 2.8rem 2rem;
    border-radius: 24px;
    text-align: center;
    color: white;
    margin-bottom: 2.5rem;
    box-shadow: 0 20px 50px rgba(234, 88, 12, 0.35);
}
.header h1 {font-size: 2.2rem; font-weight: 700; margin: 0;}
.header h2 {font-size: 1.25rem; font-weight: 400; margin: 0.8rem 0 0 0; opacity: 0.95;}
.header p {margin: 0.8rem 0 0 0; opacity: 0.9; font-size: 1rem;}

.user {
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 12px 18px;
    margin: 10px 0 10px auto;
    max-width: 70%;
    box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
    font-size: 0.95rem;
    line-height: 1.5;
}

.bot {
    background: linear-gradient(135deg, #ea580c, #f97316);
    color: white;
    border-radius: 18px 18px 18px 4px;
    padding: 12px 18px;
    margin: 10px auto 10px 0;
    max-width: 70%;
    box-shadow: 0 2px 8px rgba(234, 88, 12, 0.3);
    font-size: 0.95rem;
    line-height: 1.5;
}

.footer {text-align: center; margin-top: 3rem; color: #94a3b8; font-size: 0.85rem; opacity: 0.7;}

.info-box {
    background: rgba(249, 115, 22, 0.1);
    border-left: 4px solid #f97316;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    color: #cbd5e1;
}

@media (max-width: 768px) {
    .block-container {padding: 1rem 0.8rem 100px 0.8rem !important;}
    .header {padding: 2rem 1.5rem;}
    .header h1 {font-size: 1.8rem;}
    .user, .bot {max-width: 85%; padding: 11px 16px; font-size: 0.9rem;}
}
</style>
""", unsafe_allow_html=True)

# Inicializar base de datos
db = ChatDatabase()

# API Key de OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    st.error("⚠️ Falta configurar OPENAI_API_KEY en el archivo .env")
    st.stop()

# Header
st.markdown("""
<div class="header">
    <h1>🤖 Chatbot Colaboradores</h1>
    <h2>Nutrisco – Atención a Personas</h2>
    <p>Escribe tu duda y te respondo al instante</p>
</div>
""", unsafe_allow_html=True)

# Información para el usuario
with st.expander("ℹ️ ¿Cómo usar el chatbot?"):
    st.markdown("""
    **Puedes preguntarme sobre:**
    - 📋 Licencias médicas y permisos
    - 💰 Beneficios y liquidaciones
    - 📝 Contratos y documentos
    - 👔 Código de vestimenta
    - 🐟 Bono Fisherman
    - 🎯 Políticas internas
    - ⚙️ Sistema BUK
    
    **Si tu consulta es compleja o sensible:**
    - Usa el botón "Derivar a RRHH" para contactar directamente al equipo
    - Te responderán en menos de 24 horas
    """)

# Inicializar mensajes
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "¡Hola! Soy parte del equipo de **Atención a Personas** de Nutrisco.\n\nPuedes preguntarme sobre: licencias, beneficios, BUK, finiquitos, vestimenta, bono Fisherman y más.\n\n¡Estoy aquí para ayudarte!"
    }]

if "inicio_consulta" not in st.session_state:
    st.session_state.inicio_consulta = None

if "derivar" not in st.session_state:
    st.session_state.derivar = False

if "usuario_actual" not in st.session_state:
    st.session_state.usuario_actual = None

# Identificación del usuario (opcional, solo primera vez)
if st.session_state.usuario_actual is None:
    with st.form("form_usuario"):
        st.markdown("### 👤 Identificación (Opcional)")
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input("Email (opcional)", placeholder="tu.nombre@nutrisco.com")
        
        with col2:
            area = st.selectbox("Área", [
                "Seleccionar...",
                "Producción",
                "Administración",
                "Logística",
                "Calidad",
                "Mantenimiento",
                "Recursos Humanos",
                "Ventas",
                "Otro"
            ])
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.form_submit_button("✅ Continuar con mi nombre", use_container_width=True):
                st.session_state.usuario_actual = email if email else "Anónimo"
                st.session_state.area_actual = area if area != "Seleccionar..." else None
                st.rerun()
        
        with col_btn2:
            if st.form_submit_button("🕶️ Continuar anónimamente", use_container_width=True):
                st.session_state.usuario_actual = "Anónimo"
                st.session_state.area_actual = None
                st.rerun()

# Mostrar conversación
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot">{msg["content"]}</div>', unsafe_allow_html=True)

# Input del chat
if st.session_state.usuario_actual:
    if prompt := st.chat_input("Escribe tu consulta aquí..."):
        # Registrar inicio de consulta
        st.session_state.inicio_consulta = datetime.now()
        
        # Agregar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Llamar a OpenAI
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "model": "gpt-4o-mini",
                    "temperature": 0.7,
                    "max_tokens": 600,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Eres un asistente virtual del equipo de Recursos Humanos de Nutrisco Chile. "
                                "Tu nombre es 'Asistente RRHH Nutrisco'. "
                                "Hablas español chileno de forma cercana, empática y profesional. "
                                "Ayudas a los empleados con consultas sobre: licencias, beneficios, contratos, "
                                "liquidaciones, BUK, código de vestimenta, bono Fisherman, políticas internas. "
                                "Si la consulta es muy específica, personal o sensible (ej: problemas laborales, "
                                "despidos, conflictos), sugiere amablemente que contacten directamente a Belén Bastías "
                                "del equipo RRHH (belen.bastias@nutrisco.com). "
                                "Mantén respuestas concisas (máximo 4 párrafos). "
                                "Si no sabes algo, admítelo y sugiere contactar a RRHH."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                },
                timeout=30,
            )
            
            answer = resp.json()["choices"][0]["message"]["content"]
            
        except Exception as e:
            answer = (
                "⚠️ Lo siento, tuve un problema de conexión. "
                "Por favor, intenta nuevamente o contacta directamente a Belén Bastías: "
                "belen.bastias@nutrisco.com"
            )
        
        # Agregar respuesta
        st.session_state.messages.append({"role": "assistant", "content": answer})
        
        # Calcular tiempo de respuesta
        tiempo_respuesta_mins = (datetime.now() - st.session_state.inicio_consulta).total_seconds() / 60
        
        # Guardar en base de datos
        try:
            db.guardar_conversacion(
                usuario=st.session_state.usuario_actual,
                area=st.session_state.get('area_actual'),
                consulta=prompt,
                respuesta=answer,
                categoria="General",  # Podría categorizarse con IA después
                tiempo_respuesta_mins=tiempo_respuesta_mins,
                derivado=False
            )
        except Exception as e:
            st.error(f"Error al guardar conversación: {e}")
        
        st.rerun()

    # Botones de acción
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    
    with col_btn1:
        if st.button("🔄 Nueva Consulta", use_container_width=True):
            st.session_state.messages = [{
                "role": "assistant",
                "content": "¡Hola de nuevo! ¿En qué más puedo ayudarte?"
            }]
            st.session_state.derivar = False
            st.rerun()
    
    with col_btn2:
        if st.button("📧 Derivar a RRHH", use_container_width=True):
            st.session_state.derivar = True
    
    with col_btn3:
        if st.button("👤 Cambiar Usuario", use_container_width=True):
            st.session_state.usuario_actual = None
            st.session_state.messages = [{
                "role": "assistant",
                "content": "¡Hola! Soy parte del equipo de **Atención a Personas** de Nutrisco."
            }]
            st.rerun()

    # Modal de derivación
    if st.session_state.derivar:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### 📧 Derivar Consulta a Equipo RRHH")
        st.markdown("""
        Tu consulta será enviada directamente a **Belén Bastías** y el equipo de RRHH.
        
        Te responderán en un plazo máximo de **24 horas hábiles**.
        
        **Contacto directo:**
        - Email: belen.bastias@nutrisco.com
        - Teléfono interno: [Agregar extensión]
        """)
        
        if st.button("✅ Confirmar Derivación", use_container_width=True):
            # Guardar última consulta como derivada
            if len(st.session_state.messages) >= 2:
                ultima_consulta = st.session_state.messages[-2]['content']
                ultima_respuesta = st.session_state.messages[-1]['content']
                
                db.guardar_conversacion(
                    usuario=st.session_state.usuario_actual,
                    area=st.session_state.get('area_actual'),
                    consulta=ultima_consulta,
                    respuesta=ultima_respuesta + "\n\n[DERIVADO A RRHH]",
                    categoria="Derivado",
                    tiempo_respuesta_mins=0,
                    derivado=True
                )
                
                st.success("✅ Consulta derivada exitosamente. El equipo RRHH te contactará pronto.")
                st.session_state.derivar = False
                st.balloons()
        
        st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown('<div class="footer">Inteligencia Artificial al servicio de las personas – Nutrisco © 2025</div>', unsafe_allow_html=True)
