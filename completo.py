import streamlit as st
import google.generativeai as genai
import mercadopago
import requests
import json
import os
import math

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Usamos la versión 1.5 que es la estándar actual
    client = genai.GenerativeModel('gemini-3-pro-image-preview')
except Exception as e:
    st.error(f"Error al configurar Gemini: {e}")
    client = None
import pandas as pd
import io
import plotly.express as px
import urllib.parse
import base64
from io import BytesIO
from supabase import create_client
from streamlit_folium import folium_static
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from datetime import datetime, timedelta
import secrets
import string
# Al inicio de completo.py, junto con los demás imports
import ee

def inicializar_ee():
    try:
        # 1. Convertimos el secreto en un diccionario de Python
        gee_dict = dict(st.secrets["gee"])
        
        # 2. Limpieza crítica de la private_key (reemplaza \\n por \n real)
        if "private_key" in gee_dict:
            gee_dict["private_key"] = gee_dict["private_key"].replace("\\n", "\n")
        
        # 3. Autenticación
        credentials = ee.ServiceAccountCredentials(
            gee_dict["client_email"], 
            key_data=gee_dict["private_key"]
        )
        ee.Initialize(credentials)
        return True
    except Exception as e:
        st.error(f"Error al conectar con Earth Engine: {e}")
        return False

# Llamada a la función
if inicializar_ee():
    st.success("¡Sistemas listos!")

def generar_password_temporal():
    
    caracteres = string.ascii_letters + string.digits
    
    return ''.join(secrets.choice(caracteres) for _ in range(10))
    
# ==========================================================
# 1. CONFIGURACIÓN DE PÁGINA (debe ser lo primero)
# ==========================================================
st.set_page_config(page_title="AgroGuardian", page_icon="🌿", layout="wide")
st.markdown("""
<style>

/* Botón cerrar sesión */
div.stButton > button {
    background-color: #0066ff;
    color: #ff9900;
    border-radius: 8px;
    border: none;
    font-weight: bold;
}

div.stButton > button:hover {
    background-color: #0052cc;
    color: #ff9900;
}

</style>
""", unsafe_allow_html=True)
# ==========================================================
# 2. SUPABASE
# ==========================================================
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("🚨 Error de conexión con Supabase.")
    st.stop()
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"🚨 Error de conexión con Supabase: {e}")
    st.stop()
# ==========================================================
# 3. SESSION STATE — inicializar siempre primero
# ==========================================================
if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "cerrando_sesion" not in st.session_state:
    st.session_state.cerrando_sesion = False
if "forzar_cambio_password" not in st.session_state:
    st.session_state.forzar_cambio_password = False

# ==========================================================
# 4. LIMPIAR localStorage si se está cerrando sesión
#    (debe ir ANTES de leer localStorage)
# ==========================================================
if st.session_state.cerrando_sesion:
    st.session_state.cerrando_sesion = False
    streamlit_js_eval(
        js_expressions='localStorage.clear();',
        key="ls_clear_cerrar"
    )
    import time
    time.sleep(1)
    st.rerun()
# ==========================================================
# 5. RESTAURAR SESIÓN DESDE localStorage
#===========================================================
if st.session_state.usuario is None and not st.session_state.cerrando_sesion:
    ls_usuario = streamlit_js_eval(
        js_expressions='localStorage.getItem("ag_usuario")',
        key="ls_get_usuario"
    )
    ls_user_id = streamlit_js_eval(
        js_expressions='localStorage.getItem("ag_user_id")',
        key="ls_get_user_id"
    )
    if ls_usuario and ls_user_id:
        st.session_state.usuario = ls_usuario
        st.session_state.user_id = ls_user_id
        st.rerun()
# ==========================================================
# 6. FUNCIONES DE AUTH
# ==========================================================
def login(email, password):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        # guardar datos usuario
        st.session_state.usuario = res.user.email
        st.session_state.user_id = res.user.id

        # guardar sesión supabase
        st.session_state.supabase_session = res.session

        streamlit_js_eval(
            js_expressions=f'localStorage.setItem("ag_usuario", "{res.user.email}"); localStorage.setItem("ag_user_id", "{res.user.id}");',
            key="ls_set_sesion"
        )

        # verificar contraseña temporal
        perfil = supabase.table("perfiles").select("password_temporal").eq("id", res.user.id).execute()

        if perfil.data and perfil.data[0]["password_temporal"]:
            st.session_state.forzar_cambio_password = True

        return True
    except Exception as e:
       st.error(f"❌ Error al registrarse: {e}")
       return False   
def registrar(email, password, nombre, campo, localidad):
    try:
        res = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        if res.user:
            
            supabase.table("perfiles").insert({
                "id": res.user.id,
                "nombre": nombre,
                "campo": campo,
                "localidad": localidad,
                "password_temporal": False
                
            }).execute()
            return True
        return False
    except Exception as e:
        st.error(f"❌ Error al registrarse: {e}")
        return False   
# ==========================================================
# CAMBIO OBLIGATORIO DE CONTRASEÑA
# ==========================================================
# ==========================================================
# ==========================================================
# 7. PANTALLA DE LOGIN
# ==========================================================
if st.session_state.usuario is None:

    st.markdown("""
        <style>
            .stApp { background-color: #0d1117 !important; }
            section[data-testid="stSidebar"] { display: none !important; }
            header[data-testid="stHeader"] { background: #0d1117 !important; }
            h1, h2, h3, p, label { color: #00ffc3 !important; font-family: 'Courier New', monospace !important; }
            .stTextInput > div > div > input {
                background-color: #161b22 !important;
                color: #00ffc3 !important;
                border: 1px solid #30363d !important;
                border-radius: 6px !important;
                padding: 4px 8px !important;
                font-size: 12px !important;
                height: 32px !important;
                min-height: 32px !important;
                max-height: 32px !important;
            }
            .stTextInput {
                margin-bottom: 4px !important;
            }
            .stTextInput label p {
                font-size: 11px !important;
                margin-bottom: 2px !important;
            }
            .stButton > button {
                background-color: #161b22 !important;
                color: #00ffc3 !important;
                border: 1px solid #00ffc3 !important;
                border-radius: 6px !important;
                font-weight: bold !important;
                padding: 4px 12px !important;
                font-size: 12px !important;
                height: 32px !important;
                min-height: 32px !important;
                line-height: 1 !important;
             }               
             .stButton > button {
                background-color: #161b22 !important;
                color: #00ffc3 !important;
                border: 1px solid #00ffc3 !important;
                border-radius: 8px !important;
                font-weight: bold;
            }
            .stButton > button:hover {
                background-color: #00ffc3 !important;
                color: #0d1117 !important;
            }
            .stTabs [data-baseweb="tab"] {
                color: #00ffc3 !important;
                font-family: monospace !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style='text-align:center; padding:40px;'>
            <div style='display:flex; align-items:center; justify-content:center; gap:12px;'>
                <img src='https://raw.githubusercontent.com/ecotrufas1000/agroguardian-app/main/logo1.png' width='50px'>
                <h1 style='color:#00ffc3; font-family:monospace; margin:0; font-size:22px;'>AgroGuardian</h1>
            </div>
            <p style='color:#888; font-family:monospace; font-size:15px;'>Precision Lab v2.6</p>
        </div>
    """, unsafe_allow_html=True)

    #tab1, tab2 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
    tab_activo = st.session_state.get("tab_activo", 0)
    tab1, tab2, tab3 = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse", "🔑 Recuperar Contraseña"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Email", key="login_email")
        with col2:
            password = st.text_input("Contraseña", type="password", key="login_pass")
        if st.button("INGRESAR", use_container_width=True):
            if login(email, password):
                st.rerun()

    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre completo", key="reg_nombre")
            campo = st.text_input("Nombre del campo", key="reg_campo")
            localidad = st.text_input("Localidad", key="reg_localidad")
        with col2:
            email_r = st.text_input("Email", key="reg_email")
            pass_r = st.text_input("Contraseña", type="password", key="reg_pass")
            pass_r2 = st.text_input("Confirmar contraseña", type="password", key="reg_pass2")
        if st.button("CREAR CUENTA", use_container_width=True):
            if pass_r != pass_r2:
                st.error("❌ Las contraseñas no coinciden")
            elif len(pass_r) < 6:
                st.error("❌ La contraseña debe tener al menos 6 caracteres")
            else:
                if registrar(email_r, pass_r, nombre, campo, localidad):
                    st.success("✅ Cuenta creada. Ya podés iniciar sesión.")
                    import time
                    time.sleep(1.5)
                    st.session_state.tab_activo = 0
                    st.rerun()

    with tab3:

        st.markdown(
            "<p style='color:#888; font-family:monospace;'>Ingresá tu email y generaremos una contraseña temporal.</p>",
            unsafe_allow_html=True
        )

        email_rec = st.text_input("Email registrado", key="rec_email")

        if st.button("GENERAR CONTRASEÑA TEMPORAL", use_container_width=True):

            if not email_rec:
                st.error("Ingresá tu email")

            else:

                try:

                    password_temp = generar_password_temporal()

                    users = supabase.auth.admin.list_users()

                    user_id = None

                    for u in users:
                        if u.email == email_rec:
                            user_id = u.id
                            break

                    if user_id is None:

                        st.error("Usuario no encontrado")

                    else:

                        supabase.auth.admin.update_user_by_id(
                            user_id,
                            {"password": password_temp}
                        )

                        supabase.table("perfiles").update({
                            "password_temporal": True
                        }).eq("id", user_id).execute()

                        st.success("Se generó una contraseña temporal")
                        st.info(f"Tu contraseña temporal es: {password_temp}")

                except Exception as e:
                    st.error(f"Error: {e}")
# ==========================================================
# ==========================================================
# CAMBIO OBLIGATORIO DE CONTRASEÑA
# ==========================================================
if st.session_state.get("forzar_cambio_password", False):

    st.title("🔐 Cambio obligatorio de contraseña")

    nueva = st.text_input("Nueva contraseña", type="password")
    confirmar = st.text_input("Confirmar contraseña", type="password")

    if st.button("ACTUALIZAR CONTRASEÑA", key="btn_cambio_password"):

        if not nueva or not confirmar:
            st.error("Completá ambos campos")

        elif nueva != confirmar:
            st.error("Las contraseñas no coinciden")

        elif len(nueva) < 6:
            st.error("La contraseña debe tener al menos 6 caracteres")

        else:

            try:

                supabase.auth.set_session(
                    st.session_state.supabase_session.access_token,
                    st.session_state.supabase_session.refresh_token
                )

                supabase.auth.update_user({
                    "password": nueva
                })

                supabase.table("perfiles").update({
                    "password_temporal": False
                }).eq("id", st.session_state.user_id).execute()

                st.success("✅ Contraseña actualizada correctamente")

                st.session_state.forzar_cambio_password = False

                st.rerun()

            except Exception as e:
                st.error(f"Error al actualizar contraseña: {e}")

    
def cerrar_sesion():
    st.session_state.usuario = None
    st.session_state.user_id = None
    st.session_state.cerrando_sesion = True
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.rerun()
#==========================================================
# 8. APP PRINCIPAL — solo llega acá si está logueado
# ==========================================================
with st.sidebar:
    try:
        perfil = supabase.table("perfiles").select("nombre, campo, localidad").eq("id", st.session_state.user_id).execute()
        if perfil.data:
            p = perfil.data[0]
            st.markdown(f"""
            <div style='background:#161b22; border:1px solid #30363d; border-radius:10px; padding:12px; margin-bottom:8px;'>
                <div style='color:#00ffc3; font-family:monospace; font-size:13px; font-weight:bold;'>👤 {p.get('nombre', 'Productor')}</div>
                <div style='color:#888; font-family:monospace; font-size:11px; margin-top:4px;'>🌾 {p.get('campo', '')}</div>
                <div style='color:#888; font-family:monospace; font-size:11px;'>📍 {p.get('localidad', '')}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"👤 **{st.session_state.get('usuario', '')}**")
    except:
        st.markdown(f"👤 **{st.session_state.get('usuario', '')}**")

    if st.button("🚪 Cerrar sesión"):
        cerrar_sesion()
        streamlit_js_eval(
            js_expressions='localStorage.clear(); window.location.reload();',
            key="ls_cerrar_y_recargar"
        )

# Ejecutar el JS de localStorage fuera del botón
if st.session_state.get("cerrar"):
    st.session_state.cerrar = False
    st.session_state.usuario = None
    st.session_state.user_id = None
    streamlit_js_eval(
        js_expressions='localStorage.removeItem("ag_usuario"); localStorage.removeItem("ag_user_id");',
        key="ls_remove_sesion"
    )
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.rerun()
if st.session_state.usuario is None:
    st.stop()
# ==========================================================
# PWA / META TAGS
# ==========================================================
st.markdown("""
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="AgroGuardian">
    <meta name="theme-color" content="#2d6a2d">
    <link rel="apple-touch-icon" href="https://raw.githubusercontent.com/ecotrufas1000/agroguardian-app/main/logo1.png">
    <script>
        if ('serviceWorker' in navigator) {
            const manifest = {
                name: 'AgroGuardian',
                short_name: 'AgroGuardian',
                description: 'Diagnóstico agrícola inteligente',
                start_url: '/',
                display: 'standalone',
                background_color: '#0d2b0d',
                theme_color: '#2d6a2d',
                icons: [{
                    src: 'https://raw.githubusercontent.com/ecotrufas1000/agroguardian-app/main/logo1.png',
                    sizes: '192x192',
                    type: 'image/png'
                },
                {
                    src: 'https://raw.githubusercontent.com/ecotrufas1000/agroguardian-app/main/logo1.png',
                    sizes: '512x512',
                    type: 'image/png'
                }]
            };
            const blob = new Blob([JSON.stringify(manifest)], {type: 'application/json'});
            const manifestURL = URL.createObjectURL(blob);
            document.querySelector('link[rel="manifest"]') 
                ? document.querySelector('link[rel="manifest"]').href = manifestURL
                : (() => { const l = document.createElement('link'); l.rel='manifest'; l.href=manifestURL; document.head.appendChild(l); })();
        }
    </script>
""", unsafe_allow_html=True)

# ==========================================================
# FUNCIÓN PDF
# ==========================================================
def generar_pdf(texto_analisis, nombre_imagen="muestra"):
    if not texto_analisis:
        texto_analisis = "Sin contenido."

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    styles = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle('Titulo', parent=styles['Title'], fontSize=22, textColor=colors.HexColor('#2d6a2d'), spaceAfter=6)
    estilo_subtitulo = ParagraphStyle('Subtitulo', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#555555'), spaceAfter=4)
    estilo_cuerpo = ParagraphStyle('Cuerpo', parent=styles['Normal'], fontSize=11, leading=16, spaceAfter=8)
    estilo_footer = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.grey, alignment=1)

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    story = []

    from reportlab.platypus import Image as RLImage, Table, TableStyle
    import urllib.request
    import io as io_module

    try:
        logo_url = "https://raw.githubusercontent.com/ecotrufas1000/agroguardian-app/main/logo1.png"
        logo_bytes = urllib.request.urlopen(logo_url).read()
        logo_buffer = io_module.BytesIO(logo_bytes)
        logo = RLImage(logo_buffer, width=40, height=40)
        titulo_texto = Paragraph("AgroGuardian", estilo_titulo)
        tabla_header = Table([[logo, titulo_texto]], colWidths=[50, 400])
        tabla_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('LEFTPADDING', (0,0), (-1,-1), 0)]))
        story.append(tabla_header)
    except:
        story.append(Paragraph("AgroGuardian", estilo_titulo))

    story.append(Paragraph("Informe de Diagnóstico Agronómico", estilo_subtitulo))
    story.append(Paragraph(f"Fecha: {fecha}", estilo_subtitulo))
    story.append(Paragraph(f"Muestra: {nombre_imagen}", estilo_subtitulo))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2d6a2d')))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Resultado del Análisis", styles['Heading2']))
    story.append(Spacer(1, 0.2*cm))

    for parrafo in texto_analisis.split('\n'):
        if parrafo.strip():
            parrafo_limpio = parrafo.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(parrafo_limpio, estilo_cuerpo))

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Generado por AgroGuardian · Diagnóstico asistido por IA · Solo orientativo", estilo_footer))
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==========================================================
# CLIENTE GOOGLE GENAI
# ==========================================================
# CONFIGURACIÓN GOOGLE GENAI (GEMINI) - CORREGIDO
# ==========================================================
client = None  # Inicializamos la variable para evitar el NameError

try:
    if "GOOGLE_API_KEY" in st.secrets:
        # 1. Configuramos el módulo
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        
        # 2. Asignamos el modelo a la variable 'client' 
        # (Así el resto de tu código que usa 'client' sigue funcionando)
        client = genai.GenerativeModel('gemini-3-pro-image-preview')
        
    else:
        st.error("No se encontró GOOGLE_API_KEY en los secrets.")
except Exception as e:
    st.error(f"Error al configurar la IA: {e}")
# ==========================================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================================
st.set_page_config(page_title="AgroGuardian", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #0d1117 !important; color: #00ffc3 !important; }
        [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
        h1, h2, h3, p, label { color: #00ffc3 !important; font-family: 'Courier New', monospace !important; }
        [data-testid="stMetric"] { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
        iframe[title="streamlit_js_eval.streamlit_js_eval"] { display: none; }
        .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; padding-left: 0rem !important; padding-right: 0rem !important; }
        iframe { width: 100% !important; height: 85vh !important; border: none !important; }
        .leaflet-control-attribution { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================================
# FUNCIONES DE APOYO
# ==========================================================
def grados_a_direccion(grados):
    try:
        val = int((grados / 22.5) + 0.5)
        direcciones = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
        return direcciones[(val % 16)]
    except:
        return "N/A"

def generar_link_whatsapp(tarea, lote, temp, viento, nota):
    texto = f"📝 *Reporte AgroGuardian Pro*\n\n✅ *Tarea:* {tarea}\n📍 *Lote:* {lote}\n🌡️ *Condiciones:* {temp}°C | 💨 {viento} km/h\n"
    if nota:
        texto += f"📋 *Notas:* {nota}\n"
    return f"https://wa.me/?text={urllib.parse.quote(texto)}"

def obtener_clima_completo(lat, lon):
    if not lat or not lon:
        return None
    try:
        API_KEY = st.secrets["OPENWEATHER_API_KEY"]
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
        r = requests.get(url).json()
        if r.get("main"):
            t, h = r["main"]["temp"], r["main"]["humidity"]
            st_termica = r["main"].get("feels_like", t)
            a, b = 17.27, 237.7
            alpha = ((a * t) / (b + t)) + math.log(h/100.0)
            rocio = (b * alpha) / (a - alpha)
            return {
                "temp": t, "hum": h,"sensacion": st_termica, "v_vel": round(r["wind"]["speed"], 1),
                "v_dir": r["wind"].get("deg", 0), "rocio": round(rocio, 1),
                "presion": r["main"]["pressure"], "localidad": r.get("name", "Zona Rural"),
                "nubes": r.get("clouds", {}).get("all", 0),
            }
    except:
        return None

def get_sentinel_token():
    try:
        cid = st.secrets.get("SENTINEL_CLIENT_ID")
        csec = st.secrets.get("SENTINEL_CLIENT_SECRET")
        url = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
        r = requests.post(url, data={"grant_type": "client_credentials"}, auth=(cid, csec))
        if r.status_code == 200:
            return r.json()["access_token"]
        return None
    except Exception as e:
        st.error(f"Error interno: {e}")
        return None

# ==========================================================
# CONEXIÓN BASE DE DATOS
# ==========================================================
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("🚨 Error de conexión con Supabase.")
    st.stop()

# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:
    try:
        st.image("logo1.png", use_container_width=True)
    except:
        st.markdown("<h2 style='text-align:center;'>AGROGUARDIAN</h2>", unsafe_allow_html=True)

    st.markdown("<p style='text-align:center; font-size:10px; opacity:0.7;'>CASSANDRA AGRIS - PRECISION LAB v3.6</p>", unsafe_allow_html=True)
    st.divider()

    menu = st.radio(
        "MENÚ DE CONTROL",
        ["📊 Monitoreo Total", "🌧️ Pluviómetro", "💧 Balance Hídrico", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora", "🛰️ Índices Satelitales", "🔍 Diagnóstico IA", "💳 Suscripción PRO"],
        key="menu_principal"
    )

    import streamlit.components.v1 as components_sidebar
    components_sidebar.html("""
        <a href="https://wa.me/5491127923471?text=Hola%20AgroGuardian%2C%20necesito%20soporte%20tecnico" target="_blank" style="text-decoration:none;">
            <div style="
                background-color: #25D366;
                color: white;
                padding: 10px;
                border-radius: 12px;
                text-align: center;
                font-weight: bold;
                font-family: 'Courier New', monospace;
                font-size: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                box-shadow: 0px 4px 12px rgba(0,0,0,0.4);
                margin-top: 8px;
            ">
                <img src="https://cdn-icons-png.flaticon.com/512/733/733585.png" width="20px">
                SOPORTE TÉCNICO
            </div>
        </a>
    """, height=70)
    

    st.divider()
st.divider()

# ==========================================================
# GPS - INICIALIZACIÓN (corre siempre, en silencio)
# ==========================================================
if 'lat' not in st.session_state:
    st.session_state.lat = -34.59
if 'lon' not in st.session_state:
    st.session_state.lon = -58.50
if 'modo_gps' not in st.session_state:
    st.session_state.modo_gps = True

loc = streamlit_js_eval(js_expressions="""
new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
        (pos) => resolve({latitude: pos.coords.latitude, longitude: pos.coords.longitude}),
        (err) => resolve({error: err.message}),
        {enableHighAccuracy: true, timeout: 5000}
    )
})
""", key='get_loc_auto')

gps_disponible = False
if loc and isinstance(loc, dict) and 'latitude' in loc:
    lat_auto, lon_auto = loc['latitude'], loc['longitude']
    gps_disponible = True
else:
    lat_auto, lon_auto = None, None

if st.session_state.modo_gps and gps_disponible:
    st.session_state.lat = lat_auto
    st.session_state.lon = lon_auto
    gps_color, man_color = "#00ffc3", "#222"
    g_text, m_text = "#000", "#666"
else:
    gps_color, man_color = "#222", "#00ffc3"
    g_text, m_text = "#666", "#000"

# ==========================================================
# DATOS GLOBALES (corre siempre)
# ==========================================================
LAT = st.session_state.get('lat')
LON = st.session_state.get('lon')
clima = obtener_clima_completo(LAT, LON)

if clima:
    st.session_state.clima_data = clima

# ==========================================================
# MENÚ: MONITOREO TOTAL
# ==========================================================
if menu == "📊 Monitoreo Total":
    st.header("📊 Tablero de Control")

    # Pastillas GPS (solo aquí)
    st.markdown(f"""
    <div style='display:flex; gap:12px; margin-bottom:12px;'>
        <div style='padding:10px; border-radius:14px; font-weight:bold; background:{gps_color}; color:{g_text}; flex:1; text-align:center;'>
            🛰️ GPS Automático<br>{"Activo" if gps_disponible else "Buscando..."}
        </div>
        <div style='padding:10px; border-radius:14px; font-weight:bold; background:{man_color}; color:{m_text}; flex:1; text-align:center;'>
            📍 Ubicación Manual<br>{st.session_state.lat:.4f} | {st.session_state.lon:.4f}
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("⚙️ Configurar Ubicación del Lote"):
        c1, c2 = st.columns(2)
        new_lat = c1.number_input("Latitud", value=st.session_state.lat, format="%.6f")
        new_lon = c2.number_input("Longitud", value=st.session_state.lon, format="%.6f")
        col_btn1, col_btn2 = st.columns(2)
        if col_btn1.button("📍 USAR ESTA UBICACIÓN MANUAL", use_container_width=True):
            st.session_state.modo_gps = False
            st.session_state.lat = new_lat
            st.session_state.lon = new_lon
            st.success("Prioridad cambiada a Manual")
            st.rerun()
        if col_btn2.button("🛰️ VOLVER A GPS AUTO", use_container_width=True):
            st.session_state.modo_gps = True
            st.rerun()

    st.divider()
    # ==========================================================
    # 🚨 ALERTAS AUTOMÁTICAS
    # ==========================================================
    if clima:
        alertas = []
        temp = clima['temp']
        hum = clima['hum']
        viento = clima['v_vel']
        presion = clima['presion']
        rocio = clima['rocio']
        nubes = clima.get('nubes', 0)
        delta_t = round(temp - rocio, 1)

        # Helada
        if temp <= 0:
            alertas.append(("🔴", "HELADA EN CURSO", f"Temperatura {temp}°C — activar protección inmediatamente"))
        elif temp <= 4:
            alertas.append(("🟠", "RIESGO DE HELADA", f"Temperatura {temp}°C con viento {viento} km/h"))

        # Lluvia fuerte
        try:
            url_fc = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&daily=precipitation_sum&forecast_days=1&timezone=America%2FArgentina%2FBuenos_Aires"
            r_fc = requests.get(url_fc).json()
            lluvia_hoy = r_fc['daily']['precipitation_sum'][0] or 0
            if lluvia_hoy > 30:
                alertas.append(("🌧️", "LLUVIA INTENSA PREVISTA", f"{lluvia_hoy:.0f} mm esperados hoy"))
            elif lluvia_hoy > 15:
                alertas.append(("🟡", "LLUVIA MODERADA PREVISTA", f"{lluvia_hoy:.0f} mm esperados hoy"))
        except:
            pass

        # Tormenta
        if hum > 80 and temp > 25 and presion < 1005:
            alertas.append(("⛈️", "RIESGO DE TORMENTA", f"Humedad {hum}% | Presión {presion} hPa"))

        # Pulverización
        if delta_t < 2 or delta_t > 8:
            alertas.append(("💨", "NO PULVERIZAR", f"Delta T fuera de rango: {delta_t}°C"))

        # Estrés hídrico
        try:
            url_hum = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=soil_moisture_28_to_100cm&models=ecmwf_ifs&forecast_days=1"
            r_hum = requests.get(url_hum).json()
            hum_suelo = r_hum['hourly']['soil_moisture_28_to_100cm'][0] * 720
            if hum_suelo < 40:
                alertas.append(("💧", "ESTRÉS HÍDRICO", f"Humedad del suelo: {hum_suelo:.0f} mm — considerar riego"))
        except:
            pass

        # Mostrar alertas
        if alertas:
            st.markdown("### 🚨 Alertas Activas")
            for emoji, titulo, detalle in alertas:
                msg = f"{emoji} **{titulo}** — {detalle}"
                if emoji in ["🔴", "⛈️"]:
                    st.error(msg)
                elif emoji in ["🟠", "💨"]:
                    st.warning(msg)
                else:
                    st.info(msg)

            # Botón WhatsApp con todas las alertas
            texto_wa = "*ALERTAS AGROGUARDIAN*\n\n"
            for emoji, titulo, detalle in alertas:
                texto_wa += f"{emoji} *{titulo}*\n{detalle}\n\n"
            texto_wa += f"Ubicación: {LAT:.4f} | {LON:.4f}\n"
            texto_wa += f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
            wa_url = f"https://wa.me/?text={urllib.parse.quote(texto_wa)}"
            st.markdown(f"""
                <a href="{wa_url}" target="_blank" style="text-decoration:none;">
                    <div style="background-color:#25D366; color:white; padding:12px; border-radius:10px; text-align:center; font-weight:bold; font-family:monospace; margin-top:8px;">
                        📲 COMPARTIR ALERTAS POR WHATSAPP
                    </div>
                </a>
            """, unsafe_allow_html=True)
            st.divider()
        else:
            st.success("✅ Sin alertas activas — condiciones normales")
            st.divider()
    if clima:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Temperatura", f"{clima['temp']:.1f} °C")
            st_valor = f"{clima.get('sensacion', clima['temp']):.1f}°C"
            st.markdown(f"""
                <div style='
                    color: #00ffc3;
                    font-size: 0.85rem;
                    margin-top: -15px;
                    padding-left: 14px;
                '>
                    Sensación Térmica: {st_valor}
                </div>
            """, unsafe_allow_html=True)
        with col2: st.metric("Humedad Relativa", f"{clima['hum']} %")
        with col3: st.metric("Punto de Rocío", f"{clima['rocio']} °C")
        with col4: st.metric("Viento", f"{clima['v_vel']} km/h")
        with col5: st.metric("Presion", f"{clima['presion']} hPa")
        st.divider()
        c_a1, c_a2 = st.columns(2)
        with c_a1:
            delta_t = round(clima['temp'] - clima['rocio'], 1)
            st.markdown(f"**Delta T (Pulverización):** `{delta_t}`")
            if 2 <= delta_t <= 8:
                st.success("✅ CONDICIONES ÓPTIMAS")
            else:
                st.warning("⚠️ PRECAUCIÓN: Delta T fuera de rango")
        with c_a2:
            dir_texto = grados_a_direccion(clima['v_dir'])
            st.markdown(f"**Dirección:** `{dir_texto}` ({clima['v_dir']}°)")
            if 315 <= clima['v_dir'] or clima['v_dir'] <= 45: st.info("⬆️ Viento Norte")
            elif 135 <= clima['v_dir'] <= 225: st.info("⬇️ Viento Sur")
            else: st.info("➡️ Viento Lateral")
    else:
        st.info("📍 Vinculá el GPS para activar el monitoreo en tiempo real.")
# ==========================================================
# 💧 ESTADO HÍDRICO DEL LOTE (NUEVO)
# ==========================================================

# 👇 TODO ESTO VA ADENTRO
# ==========================================================
# 💧 ESTADO HÍDRICO DEL LOTE (NUEVO)
# ==========================================================

    st.divider()
    st.markdown("### 💧 Estado Hídrico del Lote")

    try:
        lat = st.session_state.lat
        lon = st.session_state.lon

        temp_media = clima['temp'] if clima else 25.0

        doy = datetime.now().timetuple().tm_yday
        delta = 0.409 * math.sin((2 * math.pi * doy / 365) - 1.39)
        ws = math.acos(max(-1, min(1, -math.tan(math.radians(lat)) * math.tan(delta))))
        eto_diaria = ((24/math.pi)*ws / 4380) * 100 * (0.46 * temp_media + 8)

        try:
            url_cop = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=soil_moisture_28_to_100cm&models=ecmwf_ifs&forecast_days=1"
            res_cop = requests.get(url_cop).json()
            hum_profunda = res_cop['hourly']['soil_moisture_28_to_100cm'][0]
        except:
            hum_profunda = 0.0

        hum_perfil_mm = hum_profunda * 720

        c_h1, c_h2 = st.columns(2)

        with c_h1:
            st.metric("💧 Humedad del suelo", f"{hum_perfil_mm:.0f} mm")

        with c_h2:
            st.metric("🌱 Demanda (ETo)", f"{eto_diaria:.1f} mm")

        st.markdown("###  Diagnóstico")

        if hum_perfil_mm < 40:
            st.error("🔴 Estrés hídrico — considerar riego urgente")
        elif hum_perfil_mm < 80:
            st.warning("🟡 Humedad media — monitorear evolución")
        else:
            st.success("🟢 Buen estado hídrico")

        st.caption("📡 Estimación basada en Open-Meteo + Blaney-Criddle")

    except Exception as e:
        st.error(f"Error en balance hídrico: {e}")    
# ==========================================================
    # ==========================================================
    # ==========================================================
# 🌤️ PRONÓSTICO EXTENDIDO (NUEVO)
# ==========================================================
    st.divider()
    st.markdown("### 🌤️ Pronóstico a 3 Días")
    
    try:
        # Sustituye 'TU_API_KEY_AQUÍ' por tu clave de OpenWeather
        API_KEY = "2762051ad62d06f1d0fe146033c1c7c8" 
        lat, lon = st.session_state.lat, st.session_state.lon
        
        # Usamos el endpoint de forecast (5 días / cada 3 horas)
        url_forecast = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
        res_fc = requests.get(url_forecast).json()
    
        if res_fc.get("list"):
            # Filtramos para obtener un reporte por día (aprox a mediodía)
            # La API devuelve cada 3hs, saltamos de a 8 para tener 24hs de diferencia
            pronosticos = res_fc["list"][8:32:8] 
    
            cols_fc = st.columns(3)
            
            for i, dia in enumerate(pronosticos):
                fecha_dt = datetime.fromtimestamp(dia['dt'])
                nombre_dia = fecha_dt.strftime('%A').capitalize() # Ejemplo: Lunes
                # Traducción rápida si es necesario
                dias_es = {"Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles", 
                           "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"}
                nombre_dia = dias_es.get(fecha_dt.strftime('%A'), nombre_dia)
                
                temp_max = dia['main']['temp_max']
                hum_fc = dia['main']['humidity']
                
                # Datos de viento
                v_ms = dia['wind']['speed']
                v_kmh = v_ms * 3.6
                v_deg = dia['wind']['deg']
                
                # Convertir grados a dirección cardinal
                direcciones = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
                dir_txt = direcciones[int(((v_deg + 22.5) % 360) / 45)]
                
                desc = dia['weather'][0]['description'].capitalize()
                icon = dia['weather'][0]['icon']
                
                with cols_fc[i]:
                    st.markdown(f"""
                    <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1); text-align: center;'>
                        <p style='margin-bottom: 2px; font-weight: bold; color: #4facfe;'>{nombre_dia}</p>
                        <img src="http://openweathermap.org/img/wn/{icon}@2x.png" style="width:45px;">
                        <h3 style='margin: 0; font-size: 1.2rem;'>{temp_max:.1f}°C</h3>
                        <p style='font-size: 0.8rem; opacity: 0.8; margin: 4px 0;'>{desc}</p>
                        <hr style='margin: 8px 0; opacity: 0.2;'>
                        <p style='font-size: 0.75rem; color: #00d2ff; margin:0;'>💧 Hum: {hum_fc}%</p>
                        <p style='font-size: 0.75rem; color: #ff9f43; margin:2px 0 0 0;'>
                            💨 {v_kmh:.1f} km/h <span style='color:#ccc;'>({dir_txt})</span>
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No se pudo obtener la lista de pronósticos.")

    except Exception as e:
        st.error(f"Error al obtener pronóstico: {e}")
elif menu == "🌧️ Pluviómetro":
    st.header("🌧️ Pluviómetro Digital")
    # Ocultar elementos específicos pero MANTENER la barra de navegación
    st.markdown("""
    <style>
        /* Bloqueamos el widget de estado y el botón de gestión, pero dejamos el Header */
        [data-testid="stStatusWidget"],
        button[title="Manage app"] {
            display: none !important;
            visibility: hidden !important;
        }

        /* Ajustamos el padding superior para que no tape las flechas pero se vea limpio */
        .main .block-container {
            padding-top: 3rem !important; 
            padding-bottom: 12rem !important; 
        }

        /* Elimina el banner de "Made with Streamlit" */
        footer {
            visibility: hidden !important;
        }
    </style>
""", unsafe_allow_html=True)
    import pandas as pd
    import requests
    from datetime import datetime, timedelta, timezone
    import io

    # ==========================================================
    # 🤖 AUTO REGISTRO (UNA VEZ POR DÍA)
    # ==========================================================
    if "auto_last_run" not in st.session_state:
        st.session_state.auto_last_run = None
    
    hoy_str = datetime.now().strftime("%Y-%m-%d")

    if st.session_state.auto_last_run != hoy_str:
        try:
            lat_auto = LAT if LAT else -38.29
            lon_auto = LON if LON else -57.55

            url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat_auto}&longitude={lon_auto}"
                f"&hourly=precipitation"
                f"&timezone=America/Argentina/Buenos_Aires"
                f"&past_days=1"
            )

            r = requests.get(url).json()

            if "hourly" in r:
                df_auto = pd.DataFrame({
                    "time": pd.to_datetime(r["hourly"]["time"]),
                    "mm": r["hourly"]["precipitation"]
                })

                ahora = datetime.now()
                df_auto = df_auto[df_auto["time"] <= ahora]
                mm_total = df_auto["mm"].max()

                existe = supabase.table("registros_lluvia")\
                    .select("id")\
                    .eq("fecha", hoy_str)\
                    .eq("productor_id", st.session_state.user_id)\
                    .execute()

                if not existe.data:
                    supabase.table("registros_lluvia").insert({
                        "fecha": hoy_str,
                        "mm": float(mm_total),
                        "lote": "🤖 Auto diario",
                        "productor_id": st.session_state.user_id
                    }).execute()

            st.session_state.auto_last_run = hoy_str
        except:
            pass

    # ==========================================================
    # 📥 CARGAR DATOS
    # ==========================================================
    try:
        lat_auto = LAT if LAT else -38.29   # ← definir acá también para el bloque satelital
        lon_auto = LON if LON else -57.55

        res = supabase.table("registros_lluvia")\
            .select("*")\
            .eq("productor_id", st.session_state.user_id)\
            .execute()

        df = pd.DataFrame(res.data) if res.data else pd.DataFrame()

        # ==========================================================
        # 📊 MÉTRICAS
        # ==========================================================
        if not df.empty:

            df['fecha'] = pd.to_datetime(df['fecha'], utc=True, errors='coerce')
            df['mm'] = pd.to_numeric(df['mm'], errors='coerce').fillna(0)

            hoy = datetime.now(timezone.utc)

            df_mes = df[(df['fecha'].dt.month == hoy.month) & (df['fecha'].dt.year == hoy.year)]
            df_año = df[df['fecha'].dt.year == hoy.year]

            df_mes_dia = df_mes.groupby(df_mes['fecha'].dt.date)['mm'].sum()
            max_dia = df_mes_dia.max() if not df_mes_dia.empty else 0
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💧 Este Mes", f"{df_mes['mm'].sum():.1f} mm")
            c2.metric("📆 Acum. Anual", f"{df_año['mm'].sum():.1f} mm")
            c3.metric("⚡ Máx. Día", f"{max_dia:.1f} mm")
            c4.metric("📊 Registros", f"{len(df)} eventos")

            df_mes['dia'] = df_mes['fecha'].dt.day
            df_dia = df_mes.groupby('dia')['mm'].sum().reindex(range(1, 32), fill_value=0).reset_index()
            df_dia.columns = ['Día', 'mm']

            import plotly.express as px

            fig = px.bar(df_dia, x='Día', y='mm', template="plotly_dark",
                labels={'Día': 'Día del mes', 'mm': 'Precipitación (mm)'},
                title="Lluvias del mes")
            fig.update_layout(
                xaxis=dict(tickmode='array', tickvals=[1, 10, 20, 30],
                    ticktext=['1', '10', '20', '30'], tickangle=0, range=[0.5, 31.5]),
                yaxis=dict(range=[0, 200], title="mm"),
                bargap=0.2,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#00ffc3"),
                height=300
            )
            fig.update_traces(marker_color='#00ffc3')
            st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

            meses_nombres = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
            mensual = df_año.groupby(df_año['fecha'].dt.month)['mm'].sum().reindex(range(1, 13), fill_value=0)
            df_anual = pd.DataFrame({'Mes': meses_nombres, 'mm': mensual.values})
            fig2 = px.bar(df_anual, x='Mes', y='mm', template="plotly_dark",
                text_auto='.1f', title="Lluvias anuales por mes")
            fig2.update_layout(
                bargap=0.2,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#00ffc3"),
                height=300
            )
            fig2.update_traces(marker_color='#1f77b4', textposition="outside")
            st.plotly_chart(fig2, use_container_width=True, config={'staticPlot': True})

            st.divider()
            df_excel = df.copy().sort_values('fecha', ascending=False)
            df_excel['fecha'] = df_excel['fecha'].dt.tz_localize(None)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_excel[['fecha', 'lote', 'mm']].to_excel(writer, index=False)

            st.download_button(
                "📥 Descargar Excel",
                data=output.getvalue(),
                file_name="lluvias.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        else:
            st.warning("⚠️ No hay datos todavía")

        # ==========================================================
        # 🛰️ REGISTRO MANUAL
        # ==========================================================
        st.divider()
        st.subheader("➕ Registro Manual")

        with st.form("manual"):
            fecha = st.date_input("Fecha")
            mm = st.number_input("mm", 0.0)
            lote = st.text_input("Lote", "Manual")

            if st.form_submit_button("Guardar"):
                supabase.table("registros_lluvia").insert({
                    "fecha": fecha.isoformat(),
                    "mm": mm,
                    "lote": lote,
                    "productor_id": st.session_state.user_id
                }).execute()
                st.success("Guardado")
                st.rerun()

        # BORRAR REGISTRO
        st.divider()
        st.subheader("🗑️ Borrar Registro")

        if not df.empty:
            opciones = {}
            for _, row in df.sort_values('fecha', ascending=False).iterrows():
                try:
                    fecha_str = pd.Timestamp(row['fecha']).strftime('%d/%m/%Y')
                except:
                    fecha_str = "Sin fecha"
                key = f"{fecha_str} — {row['lote']} — {row['mm']:.1f} mm"
                opciones[key] = row['id']

            fila_sel = st.selectbox("Seleccioná el registro a eliminar:", list(opciones.keys()))

            if st.button("🗑️ ELIMINAR", type="primary", use_container_width=True):
                try:
                    supabase.table("registros_lluvia").delete().eq("id", opciones[fila_sel]).execute()
                    st.success("✅ Registro eliminado")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.info("No hay registros para eliminar.")

        # ==========================================================
        # ==========================================================
        # 📡 DESCARGA SATELITAL
        # ==========================================================
        st.divider()
        st.subheader("📡 Datos Satelitales")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📡 Hoy"):
                # Mantenemos el endpoint hourly para ver el detalle si hubo lluvia
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat_auto}&longitude={lon_auto}&hourly=precipitation&past_days=1&timezone=America/Argentina/Buenos_Aires"
                r = requests.get(url).json()
                
                df_sat = pd.DataFrame({
                    "fecha": pd.to_datetime(r["hourly"]["time"]),
                    "mm": r["hourly"]["precipitation"]
                })
                
                # 1. Calculamos el total acumulado del día (Hoy)
                # Filtramos por la fecha de hoy para evitar mezclar con las horas de ayer que trae 'past_days=1'
                hoy_str = pd.Timestamp.now().strftime("%Y-%m-%d")
                total_hoy = df_sat[df_sat["fecha"].dt.strftime("%Y-%m-%d") == hoy_str]["mm"].sum()
                
                # 2. Mostramos el total bien grande
                st.metric(label="Total Lluvia Satelital (Hoy)", value=f"{total_hoy:.1f} mm")

                # Filtramos el DF para mostrar solo las horas con lluvia en la tabla
                df_sat_lluvia = df_sat[df_sat["mm"] > 0].copy()
                
                # Guardar en Supabase (usamos la fecha sin hora para el registro diario)
                guardados = 0
                if total_hoy > 0:
                    existe = supabase.table("registros_lluvia")\
                        .select("id")\
                        .eq("fecha", hoy_str)\
                        .eq("lote", "📡 Satelital")\
                        .eq("productor_id", st.session_state.user_id)\
                        .execute()
                    
                    if not existe.data:
                        supabase.table("registros_lluvia").insert({
                            "fecha": hoy_str,
                            "mm": float(total_hoy),
                            "lote": "📡 Satelital",
                            "productor_id": st.session_state.user_id
                        }).execute()
                        guardados += 1

                # Mostramos la tabla horaria por si quieres ver CUÁNDO llovió
                if not df_sat_lluvia.empty:
                    st.write("Detalle horario de hoy:")
                    st.dataframe(df_sat_lluvia)
                
                if guardados > 0:
                    st.success(f"✅ Registro de {total_hoy:.1f} mm guardado")
                    st.rerun()
                elif total_hoy > 0:
                    st.info("ℹ️ El total de hoy ya estaba guardado")
                else:
                    st.warning("⚠️ No se detectó lluvia hoy por satélite")
        with col2:
            if st.button("📡 7 días"):
                # Usamos past_days=7 para que la API maneje internamente el historial
                # Esto es más seguro que calcular fechas isoformat manualmente
                url = (
                    f"https://api.open-meteo.com/v1/forecast"
                    f"?latitude={lat_auto}&longitude={lon_auto}"
                    f"&daily=precipitation_sum"
                    f"&past_days=7"  # Trae los últimos 7 días terminando ayer
                    f"&forecast_days=0" # Le decimos que NO traiga días de pronóstico
                    f"&timezone=America/Argentina/Buenos_Aires"
                )
                
                r = requests.get(url).json()
                
                # Armamos el DataFrame
                df_sat = pd.DataFrame({
                    "fecha": r["daily"]["time"],
                    "mm": r["daily"]["precipitation_sum"]
                })
                
                # Filtramos solo los días que tuvieron lluvia
                df_sat = df_sat[df_sat["mm"] > 0]
                
                # Guardar en Supabase si no existe
                guardados = 0
                for _, row in df_sat.iterrows():
                    # r["daily"]["time"] ya viene en formato "YYYY-MM-DD"
                    existe = supabase.table("registros_lluvia")\
                        .select("id")\
                        .eq("fecha", row["fecha"])\
                        .eq("lote", "📡 Satelital")\
                        .eq("productor_id", st.session_state.user_id)\
                        .execute()
                        
                    if not existe.data:
                        supabase.table("registros_lluvia").insert({
                            "fecha": row["fecha"],
                            "mm": float(row["mm"]),
                            "lote": "📡 Satelital",
                            "productor_id": st.session_state.user_id
                        }).execute()
                        guardados += 1

                st.write(df_sat)
                if guardados > 0:
                    st.success(f"✅ {guardados} registros guardados")
                    st.rerun()
                else:
                    st.info("ℹ️ No se encontraron nuevas lluvias en los últimos 7 días")               
    except Exception as e:
        st.error(f"Error en la descarga satelital: {e}")
                    
# MENÚ: BALANCE HÍDRICO
# ==========================================================
# ==========================================================
# MENÚ: BALANCE HÍDRICO — ERA5 vía Open-Meteo
# ==========================================================
# MENÚ: BALANCE HÍDRICO — ERA5 vía Open-Meteo
# ==========================================================
elif menu == "💧 Balance Hídrico":

    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from matplotlib.colors import LinearSegmentedColormap
    from scipy.interpolate import griddata, RegularGridInterpolator
    import io as _io
    import base64 as _b64
    import math as _math
    import gzip as _gzip
    import json as _json

    CMAP_BAL = LinearSegmentedColormap.from_list("balance", [
        "#8B0000", "#c0392b", "#e74c3c", "#f39c12",
        "#f1c40f", "#ffffff",
        "#27ae60", "#2980b9", "#1a5276", "#0d2b4e"
    ])

    _BASE_URL   = "https://historical-forecast-api.open-meteo.com/v1/forecast"
    _VARS_DAILY = "daily=precipitation_sum&daily=et0_fao_evapotranspiration_sum"
    _RADIO_KM   = 150

    _PROV_B64 = "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"

    @st.cache_data
    def _get_provincias_geojson():
        raw = _gzip.decompress(_b64.b64decode(_PROV_B64))
        return _json.loads(raw)

    def _test_un_punto(lat, lon, fecha_ini, fecha_fin):
        url = (f"{_BASE_URL}?latitude={lat}&longitude={lon}"
               f"&start_date={fecha_ini}&end_date={fecha_fin}"
               f"&{_VARS_DAILY}&models=era5"
               f"&timezone=America%2FArgentina%2FBuenos_Aires")
        try:
            r = requests.get(url, timeout=20)
            return r.status_code, r.json(), url
        except Exception as e:
            return None, str(e), url

    @st.cache_data(ttl=3600, show_spinner=False)
    def _descargar_grilla(lat_c, lon_c, radio_deg, fecha_ini, fecha_fin):
        paso = 0.25
        lats = np.arange(lat_c - radio_deg, lat_c + radio_deg + paso, paso)
        lons = np.arange(lon_c - radio_deg, lon_c + radio_deg + paso, paso)
        lat_grid, lon_grid = np.meshgrid(lats, lons)
        lat_flat = lat_grid.flatten()
        lon_flat = lon_grid.flatten()
        registros, errores = [], []
        for i in range(0, len(lat_flat), 20):
            lats_b  = lat_flat[i:i+20]
            lons_b  = lon_flat[i:i+20]
            lat_str = ",".join(f"{v:.4f}" for v in lats_b)
            lon_str = ",".join(f"{v:.4f}" for v in lons_b)
            url = (f"{_BASE_URL}?latitude={lat_str}&longitude={lon_str}"
                   f"&start_date={fecha_ini}&end_date={fecha_fin}"
                   f"&{_VARS_DAILY}&models=era5"
                   f"&timezone=America%2FArgentina%2FBuenos_Aires")
            try:
                r    = requests.get(url, timeout=30)
                data = r.json()
                if r.status_code != 200:
                    errores.append(f"HTTP {r.status_code}: {str(data)[:200]}")
                    continue
                if isinstance(data, dict):
                    data = [data]
                for pt in data:
                    try:
                        d   = pt["daily"]
                        pp  = np.nan_to_num(np.array(d["precipitation_sum"], dtype=float))
                        et0 = np.nan_to_num(np.array(d["et0_fao_evapotranspiration_sum"], dtype=float))
                        registros.append({
                            "lat":      pt["latitude"],
                            "lon":      pt["longitude"],
                            "bal_d":    pp[-1] - et0[-1],
                            "pp_dia":   pp[-1],
                            "et0_dia":  et0[-1],
                            "bal_a":    float(np.sum(pp - et0)),
                            "pp_acum":  float(np.sum(pp)),
                            "et0_acum": float(np.sum(et0)),
                        })
                    except Exception as e:
                        errores.append(f"Parse: {e}")
            except Exception as e:
                errores.append(f"Request: {e}")
        import pandas as pd
        return (pd.DataFrame(registros) if registros else None), errores

    @st.cache_data(ttl=86400, show_spinner=False)
    def _obtener_mascara_agua(lat_min, lat_max, lon_min, lon_max, resolucion):
        try:
            grid_lon = np.linspace(lon_min, lon_max, resolucion)
            grid_lat = np.linspace(lat_min, lat_max, resolucion)
            glon, glat = np.meshgrid(grid_lon, grid_lat)
            paso = 10
            lats_q = glat[::paso, ::paso].flatten()
            lons_q = glon[::paso, ::paso].flatten()
            elev_grid = np.zeros(lats_q.shape)
            for i in range(0, len(lats_q), 50):
                lb  = lats_q[i:i+50]
                lob = lons_q[i:i+50]
                url = (f"https://api.open-meteo.com/v1/elevation"
                       f"?latitude={','.join(f'{v:.4f}' for v in lb)}"
                       f"&longitude={','.join(f'{v:.4f}' for v in lob)}")
                try:
                    r = requests.get(url, timeout=15)
                    elev_grid[i:i+len(lb)] = r.json().get("elevation", [0]*len(lb))
                except:
                    pass
            nrows_r = glat[::paso, ::paso].shape[0]
            ncols_r = glat[::paso, ::paso].shape[1]
            elev_r  = elev_grid[:nrows_r*ncols_r].reshape(nrows_r, ncols_r)
            lat_r   = grid_lat[::paso][:nrows_r]
            lon_r   = grid_lon[::paso][:ncols_r]
            interp  = RegularGridInterpolator(
                (lat_r, lon_r), elev_r, method="nearest",
                bounds_error=False, fill_value=0)
            pts       = np.column_stack([glat.flatten(), glon.flatten()])
            elev_full = interp(pts).reshape(resolucion, resolucion)
            return elev_full <= -2
        except:
            return np.zeros((resolucion, resolucion), dtype=bool)

    def _crear_raster_png(df, col_valor, lat_c, lon_c, radio_deg, vmin, vmax, resolucion=500):
        cos_lat       = _math.cos(_math.radians(lat_c))
        radio_deg_lon = radio_deg / cos_lat
        lat_min, lat_max = lat_c - radio_deg, lat_c + radio_deg
        lon_min, lon_max = lon_c - radio_deg_lon, lon_c + radio_deg_lon

        grid_lon = np.linspace(lon_min, lon_max, resolucion)
        grid_lat = np.linspace(lat_min, lat_max, resolucion)
        glon, glat = np.meshgrid(grid_lon, grid_lat)

        puntos  = df[["lon", "lat"]].values
        valores = df[col_valor].values
        grid_vals = griddata(puntos, valores, (glon, glat), method="cubic")
        grid_nn   = griddata(puntos, valores, (glon, glat), method="nearest")
        grid_vals[np.isnan(grid_vals)] = grid_nn[np.isnan(grid_vals)]

        dlat    = (glat - lat_c) * 111.0
        dlon    = (glon - lon_c) * 111.0 * cos_lat
        dist_km = np.sqrt(dlat**2 + dlon**2)

        borde_km   = _RADIO_KM * 0.18
        alpha_circ = np.where(
            dist_km >= _RADIO_KM, 0.0,
            np.where(dist_km <= _RADIO_KM - borde_km, 1.0,
                     (_RADIO_KM - dist_km) / borde_km)
        )

        mascara_agua = _obtener_mascara_agua(lat_min, lat_max, lon_min, lon_max, resolucion)

        norm  = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
        rgba  = CMAP_BAL(norm(grid_vals))
        alpha = alpha_circ * 0.82
        alpha[mascara_agua] = 0.0
        rgba[..., 3] = alpha

        fig, ax = plt.subplots(figsize=(resolucion/100, resolucion/100), dpi=100)
        ax.imshow(rgba, origin="lower",
                  extent=[lon_min, lon_max, lat_min, lat_max], aspect="auto")
        ax.axis("off")
        plt.subplots_adjust(0, 0, 1, 1)
        buf = _io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0,
                    transparent=True, dpi=100)
        plt.close(fig)
        buf.seek(0)
        return _b64.b64encode(buf.read()).decode(), [[lat_min, lon_min], [lat_max, lon_max]]

    # ── Leyenda HORIZONTAL pequeña ────────────────────────────
    def _crear_leyenda_horizontal(vmin, vmax):
        fig, ax = plt.subplots(figsize=(5, 0.45))
        norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
        cb = matplotlib.colorbar.ColorbarBase(
            ax, cmap=CMAP_BAL, norm=norm, orientation="horizontal")
        cb.set_label("Balance hídrico (mm)", fontsize=8, labelpad=2)
        cb.ax.tick_params(labelsize=7)
        plt.tight_layout(pad=0.2)
        buf = _io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight",
                    facecolor="white", dpi=130)
        plt.close(fig)
        buf.seek(0)
        return buf

    # ── Serie temporal — fechas cortas en eje X ───────────────
    def _construir_serie_temporal(lat, lon, fecha_fin_str, n_dias):
        fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
        fecha_ini = fecha_fin - timedelta(days=n_dias - 1)
        url = (f"{_BASE_URL}?latitude={lat}&longitude={lon}"
               f"&start_date={fecha_ini}&end_date={fecha_fin_str}"
               f"&{_VARS_DAILY}&models=era5"
               f"&timezone=America%2FArgentina%2FBuenos_Aires")
        try:
            import pandas as pd
            r = requests.get(url, timeout=20)
            d = r.json()["daily"]
            fechas   = pd.to_datetime(d["time"])
            pp       = np.nan_to_num(np.array(d["precipitation_sum"], dtype=float))
            et0      = np.nan_to_num(np.array(d["et0_fao_evapotranspiration_sum"], dtype=float))
            bal_acum = np.cumsum(pp - et0)

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 4), sharex=True)
            ax1.bar(fechas, pp,   color="#2166ac", alpha=0.75, label="Precipitación (mm)")
            ax1.bar(fechas, -et0, color="#b2182b", alpha=0.75, label="ET0 FAO (mm, negativa)")
            ax1.axhline(0, color="black", linewidth=0.8)
            ax1.set_ylabel("mm/día")
            ax1.legend(fontsize=7, loc="upper left")
            ax1.set_title(f"Balance hídrico diario — {lat:.2f} | {lon:.2f}")

            colores = ["#2166ac" if v >= 0 else "#b2182b" for v in bal_acum]
            ax2.bar(fechas, bal_acum, color=colores, alpha=0.75)
            ax2.axhline(0, color="black", linewidth=0.8, linestyle="--")
            ax2.set_ylabel("Balance acum. (mm)")
            ax2.set_xlabel("Fecha")

            # ── Fechas cortas: YY-MM-DD ───────────────────────
            ax2.xaxis.set_major_formatter(
                matplotlib.dates.DateFormatter("%y-%m-%d")
            )
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right", fontsize=7)

            plt.tight_layout()
            return fig
        except:
            return None

    def _construir_mapa(df, lat_c, lon_c, col_valor, titulo_capa, fecha_str, valor_punto):
        radio_deg = _RADIO_KM / 111.0
        vals      = df[col_valor].values
        abs_max   = max(abs(np.percentile(vals, 2)), abs(np.percentile(vals, 98)), 1)
        vmin, vmax = -abs_max, abs_max

        with st.spinner("🌊 Calculando máscara de agua..."):
            img_b64, bbox = _crear_raster_png(df, col_valor, lat_c, lon_c, radio_deg, vmin, vmax)

        m = folium.Map(location=[lat_c, lon_c], zoom_start=7, control_scale=True)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri", name="Satelital", overlay=False,
        ).add_to(m)
        folium.TileLayer("CartoDB positron", name="Mapa base", overlay=False).add_to(m)

        folium.raster_layers.ImageOverlay(
            image=f"data:image/png;base64,{img_b64}",
            bounds=bbox, opacity=1.0,
            name=f"Balance {titulo_capa}", interactive=False,
        ).add_to(m)

        prov_geojson = _get_provincias_geojson()
        folium.GeoJson(
            prov_geojson,
            name="Provincias",
            style_function=lambda f: {
                "color": "#ffffff", "weight": 1.5,
                "fillOpacity": 0, "dashArray": "4 3"
            },
        ).add_to(m)

        signo = "+" if valor_punto >= 0 else ""
        folium.Marker(
            [lat_c, lon_c],
            popup=folium.Popup(
                f"<b>📍 {titulo_capa}</b><br>"
                f"<b style='font-size:15px'>{signo}{valor_punto:.1f} mm</b><br>"
                f"<small>{fecha_str}</small>", max_width=220),
            tooltip=f"{signo}{valor_punto:.1f} mm",
            icon=folium.Icon(color="orange", icon="star", prefix="fa"),
        ).add_to(m)

        folium.Circle([lat_c, lon_c], radius=_RADIO_KM*1000,
                      color="#333333", weight=1.2, fill=False, dash_array="6").add_to(m)
        folium.LayerControl(collapsed=False).add_to(m)
        return m, vmin, vmax

    # ══════════════════════════════════════════════════════════
    # UI PRINCIPAL
    # ══════════════════════════════════════════════════════════
    st.header("💧 Balance Hídrico ERA5")

    lat = LAT if LAT else -35.45
    lon = LON if LON else -60.88

    MAX_FECHA = datetime.today().date() - timedelta(days=6)

    col_d, col_e = st.columns(2)
    with col_d:
        fecha_sel = st.date_input(
            "📅 Fecha puntual",
            value=MAX_FECHA - timedelta(days=1),
            max_value=MAX_FECHA,
            help="ERA5 tiene un retraso de ~6 días.",
            key="bh_fecha"
        )
        if fecha_sel > MAX_FECHA:
            st.warning(f"⚠️ Fecha ajustada a {MAX_FECHA}.")
            fecha_sel = MAX_FECHA
    with col_e:
        acum_dias = st.slider("📆 Días acumulados", 7, 90, 30, step=7, key="bh_acum")

    if st.button("🌍 Generar balance hídrico", type="primary", use_container_width=True, key="bh_generar"):

        fecha_fin_str = fecha_sel.strftime("%Y-%m-%d")
        fecha_ini_str = (fecha_sel - timedelta(days=acum_dias - 1)).strftime("%Y-%m-%d")
        radio_deg     = _RADIO_KM / 111.0

        with st.expander("🔍 Diagnóstico API", expanded=False):
            status_api, resp_api, url_debug = _test_un_punto(lat, lon, fecha_ini_str, fecha_fin_str)
            st.caption(f"URL: `{url_debug}`")
            st.write(f"**Status HTTP:** {status_api}")
            if isinstance(resp_api, dict):
                d_prev = resp_api.get("daily", {})
                st.json({k: (v[:3] if isinstance(v, list) else v) for k, v in d_prev.items()})
            else:
                st.text(str(resp_api)[:500])

        if status_api != 200:
            st.error(f"❌ Open-Meteo devolvió error {status_api}.")
            st.stop()

        with st.spinner("⏳ Descargando grilla ERA5..."):
            df_bh, errores_bh = _descargar_grilla(lat, lon, radio_deg, fecha_ini_str, fecha_fin_str)

        if errores_bh:
            with st.expander(f"⚠️ {len(errores_bh)} advertencias"):
                for e in errores_bh[:10]:
                    st.text(e)

        if df_bh is None or df_bh.empty:
            st.error("❌ No se obtuvieron datos.")
            st.stop()

        idx_c = np.argmin((df_bh.lat - lat)**2 + (df_bh.lon - lon)**2)
        row_c = df_bh.iloc[idx_c]

        st.subheader(f"📍 {lat:.4f} | {lon:.4f}  —  ET0 FAO")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("🌧️ PP día",            f"{row_c.pp_dia:.1f} mm")
        c2.metric("🌿 ET0 día",           f"{row_c.et0_dia:.1f} mm")
        c3.metric("⚖️ Balance día",       f"{row_c.bal_d:+.1f} mm",
                  delta_color="normal" if row_c.bal_d >= 0 else "inverse")
        c4.metric(f"🌧️ PP {acum_dias}d",   f"{row_c.pp_acum:.1f} mm")
        c5.metric(f"🌿 ET0 {acum_dias}d",  f"{row_c.et0_acum:.1f} mm")
        c6.metric(f"⚖️ Bal. {acum_dias}d", f"{row_c.bal_a:+.1f} mm",
                  delta_color="normal" if row_c.bal_a >= 0 else "inverse")
        st.divider()

        with st.spinner("📈 Generando serie temporal..."):
            fig_serie = _construir_serie_temporal(lat, lon, fecha_fin_str, acum_dias)
        if fig_serie:
            st.pyplot(fig_serie)
            plt.close()
        st.divider()

        # ── Tabs uno debajo del otro en móvil ─────────────────
        st.markdown("#### 📅 Balance diario")
        st.caption(f"PP − ET0 FAO · {fecha_fin_str} · Rojo = déficit | Azul = exceso")
        with st.spinner("🗺️ Generando mapa diario..."):
            res1 = _construir_mapa(df_bh, lat, lon, "bal_d",
                                   "Bal. diario ET0", fecha_fin_str, row_c.bal_d)
        m1, vmin1, vmax1 = res1
        folium_static(m1, width=None, height=480)
        st.image(_crear_leyenda_horizontal(vmin1, vmax1), use_container_width=True)

        st.divider()

        st.markdown(f"#### 📆 Balance acumulado ({acum_dias} días)")
        st.caption(f"PP − ET0 acumulado · {fecha_ini_str} → {fecha_fin_str}")
        with st.spinner("🗺️ Generando mapa acumulado..."):
            res2 = _construir_mapa(df_bh, lat, lon, "bal_a",
                                   f"Bal. acum. {acum_dias}d ET0",
                                   f"{fecha_ini_str}→{fecha_fin_str}", row_c.bal_a)
        m2, vmin2, vmax2 = res2
        folium_static(m2, width=None, height=480)
        st.image(_crear_leyenda_horizontal(vmin2, vmax2), use_container_width=True)

    else:
        st.info("👆 Seleccioná fecha y días acumulados, luego hacé clic en **Generar balance hídrico**.")
        st.markdown("""
        > **Balance = Precipitación − ET0 FAO**
        - ✅ **Positivo (azul)** → exceso de agua
        - ❌ **Negativo (rojo)** → déficit hídrico

        **Fuente:** ERA5 (ECMWF) vía Open-Meteo · Sin API key · Retraso ~6 días.
        """)
# ==========================================================
# MENÚ: RADAR GRANIZO
# ==========================================================
elif menu == "⛈️ Radar Granizo":
    st.header("⛈️ Monitor de Tormentas y Granizo")
    
    if LAT and LON and clima:
        c1, c2, c3 = st.columns(3)
        
        # Extraer variables
        hum = clima.get('hum', 0)
        temp = clima.get('temp', 0)
        presion = clima.get('presion', 1013)
        rocio = clima.get('rocio', 0)
        # Asumo que 'desc' es el estado del cielo (ej: "Rain", "Clouds", "Clear")
        estado_cielo = clima.get('desc', '').lower() 

        # --- LÓGICA DE ÍNDICE DE INESTABILIDAD (CONVECTIVA) ---
        idx = 0
        
        # 1. Energía Térmica
        if temp > 30: idx += 2
        elif temp > 25: idx += 1
        
        # 2. Humedad (Combustible principal)
        if hum > 85: idx += 3
        elif hum > 70: idx += 2
        elif hum > 55: idx += 1
        
        # 3. Presión (Divergencia)
        if presion < 1005: idx += 3
        elif presion < 1010: idx += 2
        elif presion < 1014: idx += 1
        
        # 4. Punto de Rocío (Proximidad a la saturación)
        dif_rocio = temp - rocio
        if dif_rocio < 2: idx += 3
        elif dif_rocio < 4: idx += 2
        elif dif_rocio < 8: idx += 1

        # --- FILTRO DE REALIDAD (VERIFICACIÓN DE TORMENTA) ---
        # Definimos si hay "acción" en el cielo según la API
        hay_tormenta = any(word in estado_cielo for word in ["thunder", "storm", "lightning"])
        hay_lluvia = "rain" in estado_cielo or "drizzle" in estado_cielo
        hay_nubes_pesadas = "cloud" in estado_cielo and hum > 75

        # --- DETERMINACIÓN DEL RIESGO FINAL ---
        if hay_tormenta:
            if idx >= 8: riesgo = "🔴 SEVERO"; delta_txt = "Granizo inminente / Tormenta fuerte"
            else: riesgo = "🟠 ALTO"; delta_txt = "Tormenta eléctrica activa"
        elif hay_lluvia:
            if idx >= 7: riesgo = "🟠 ALTO"; delta_txt = "Lluvia con riesgo convectivo"
            else: riesgo = "🟡 MODERADO"; delta_txt = "Lluvias aisladas"
        elif hay_nubes_pesadas:
            if idx >= 8: riesgo = "🟡 MODERADO"; delta_txt = "Cielo cubierto, aire inestable"
            else: riesgo = "🟢 BAJO"; delta_txt = "Nubosidad sin desarrollo"
        else:
            # Si el cielo está despejado o hay pocas nubes
            if idx >= 9: riesgo = "🟡 MODERADO"; delta_txt = "Inestabilidad extrema (Peligro de formación)"
            elif idx >= 6: riesgo = "🟢 BAJO"; delta_txt = "Humedad alta, sin nubes de tormenta"
            else: riesgo = "✅ NULO"; delta_txt = "Condiciones estables"

        with c1:
            st.metric("Inestabilidad Atmosférica", riesgo, delta=delta_txt)
        with c2:
            st.metric("Presión Atmosférica", f"{presion} hPa")
        with c3:
            st.metric("Punto de Rocío", f"{rocio} °C", help="A mayor punto de rocío, más combustible para la tormenta")

        st.divider()

        # --- SELECTOR DE CAPAS Y RADAR ---
        capa = st.radio("Seleccionar Capa del Sensor:", ["Radar", "T. Electricas", "Nubes"], index=0, horizontal=True)
        vistas = {"Radar": "radar", "T. Electricas": "thunder", "Nubes": "satellite"}
        
        st.markdown(f"### 🛰️ Sensor Activo: {capa}")

        # CSS para limpiar el iframe
        st.markdown("""
            <style>
                .element-container iframe { margin-bottom: -40px !important; }
                div[data-testid="stVerticalBlock"] > div:has(iframe) { margin-bottom: -50px !important; }
            </style>
        """, unsafe_allow_html=True)

        url_windy = f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&overlay={vistas[capa]}&product=radar&menu=&message=false&marker=true&calendar=now&pressure=true&type=map&location=coordinates&detail=false&metricWind=km%2Fh&metricTemp=%C2%B0C&radarRange=-1"
        
        st.components.v1.iframe(url_windy, height=450, scrolling=False)

        # Expansores de ayuda
        with st.expander("ℹ️ ¿Cómo leer el radar?"):
            st.write("""
            - **Colores Verdes/Azules:** Lluvia ligera o moderada.
            - **Colores Rojos/Amarillos:** Tormentas fuertes, posible granizo pequeño.
            - **Colores Púrpura/Blanco:** Celdas de granizo pesado o tormentas severas.
            - **Capa de Rayos:** Las cruces brillantes indican actividad eléctrica en tiempo real.
            """)

        with st.expander("📊 Detalle del cálculo de inestabilidad"):
            st.markdown(f"""
         
             
            
            | Factor | Valor | Estado |
            |--------|-------|--------|
            | Temperatura | {temp}°C | {"🔥 Calor extremo" if temp > 30 else "Normal"} |
            | Humedad | {hum}% | {"💧 Saturado" if hum > 80 else "Normal"} |
            | Presión | {presion} hPa | {"📉 Baja (Inestable)" if presion < 1010 else "Estable"} |
            | Cielo (API) | {estado_cielo.capitalize()} | {"⚡ Tormenta detectada" if hay_tormenta else "Sin actividad eléctrica"} |
            
            **Puntos de Inestabilidad acumulados: {idx}/11**
            """)

    else:
        st.warning("📍 Se requiere vincular el GPS en el panel lateral para centrar el radar en tu lote.")
# ==========================================================
elif menu == "❄️ Análisis de Heladas":
    st.markdown("<h2 style='font-size: 24px;'>❄️ Heladas Agrometeorológicas</h2>", unsafe_allow_html=True)

    if clima:
        c1, c2 = st.columns(2)
        with c1: st.metric("Temp. Actual", f"{clima['temp']}°C")
        with c2:
            if clima['temp'] < 3: st.error("⚠️ Riesgo de Helada")
            else: st.success("✅ Sin riesgo")

        st.markdown("<h3 style='font-size: 20px;'>🌡️ Análisis de Riesgo Actual</h3>", unsafe_allow_html=True)
        temp = clima['temp']
        # SIMULADOR — sacar después de testear
        simular = st.checkbox("🧪 Simular Condiciones")
        if simular:
            st.warning("⚠️ Modo simulación activo — los datos no son reales")
            temp = st.slider("Temp simulada", -10.0, 15.0, 2.0)
            hum = st.slider("Humedad simulada", 0, 100, 85)
            viento = st.slider("Viento simulado", 0.0, 30.0, 3.0)
            nubes = st.slider("Nubosidad simulada", 0, 100, 10)
        else:
            temp = clima['temp']
            rocio = clima['rocio']
            viento = clima['v_vel']
            hum = clima['hum']
            nubes = clima.get('nubes', 0)
        rocio = clima['rocio']
        viento = clima['v_vel']
        hum = clima['hum']
        diferencia_rocio = temp - rocio
        puntos = 0
        factores = [] 
        
        # Agregar ANTES de toda la lógica de puntos
        if temp > 10:
            nivel = "✅ SIN RIESGO"
            color = "success"
            consejo = "Sin condiciones de helada."
            puntos = 0
            factores = ["🟢 Temperatura por encima del umbral crítico"]
        else:
            if temp <= 0: puntos += 4; factores.append("🔴 Temperatura bajo cero — helada en curso")
            elif temp <= 2: puntos += 3; factores.append("🟠 Temperatura crítica (0-2°C) — riesgo muy alto")
            elif temp <= 4: puntos += 2; factores.append("🟡 Temperatura de alerta (2-4°C) — riesgo moderado")
            elif temp <= 7: puntos += 1; factores.append("🟢 Temperatura baja (4-7°C) — riesgo leve")

            if diferencia_rocio < 2: puntos += 3; factores.append("🔴 Punto de rocío muy cercano — inversión térmica probable")
            elif diferencia_rocio < 4: puntos += 2; factores.append("🟡 Diferencia temp-rocío baja — condensación posible")
            elif diferencia_rocio < 6: puntos += 1; factores.append("🟢 Diferencia temp-rocío moderada")
    
            if viento < 5: puntos += 2; factores.append("🔴 Viento calmo — favorece inversión térmica y helada radiativa")
            elif viento < 10: puntos += 1; factores.append("🟡 Viento leve — mezcla de aire insuficiente")
            else: factores.append("🟢 Viento suficiente — reduce riesgo de helada radiativa")
    
            if hum > 85 and temp < 5: puntos += 2; factores.append("🔴 Alta humedad con temperatura baja — riesgo de escarcha")
            elif hum > 70 and temp < 7: puntos += 1; factores.append("🟡 Humedad elevada con temperatura baja")
            # Nubosidad — las noches despejadas favorecen helada radiativa
            nubes = clima.get('nubes', 0)
            if nubes < 20: 
                puntos += 2
                factores.append("🔴 Cielo despejado — máximo riesgo de helada radiativa nocturna")
            elif nubes < 50: 
                puntos += 1
                factores.append("🟡 Nubosidad parcial — riesgo moderado de helada radiativa")
            else: 
                factores.append("🟢 Cielo nublado — las nubes reducen la pérdida de calor nocturna")

            # Inversión térmica — presión alta + viento calmo + cielo despejado
            if clima['presion'] > 1020 and viento < 5 and nubes < 30:
                puntos += 2
                factores.append("🔴 Condiciones de inversión térmica — aire frío acumulado cerca del suelo")
            elif clima['presion'] > 1015 and viento < 10:
                puntos += 1
                factores.append("🟡 Posible inversión térmica débil — monitorear temperatura al amanecer")

            # Ajustar máximo de puntos en caption
            if puntos >= 7: nivel = "🚨 RIESGO EXTREMO"; color = "error"; consejo = "Activar sistemas de protección inmediatamente. Helada inminente o en curso."
            elif puntos >= 5: nivel = "🔴 RIESGO ALTO"; color = "error"; consejo = "Preparar sistemas de protección. Alta probabilidad de helada esta noche."
            elif puntos >= 3: nivel = "🟡 RIESGO MODERADO"; color = "warning"; consejo = "Monitorear cada 30 minutos. Posibilidad de helada en horas nocturnas."
            elif puntos >= 1: nivel = "🟢 RIESGO BAJO"; color = "success"; consejo = "Condiciones desfavorables para helada. Mantener vigilancia."
            else: nivel = "✅ SIN RIESGO"; color = "success"; consejo = "Sin condiciones de helada en las próximas horas."
    
            if color == "error": st.error(f"**{nivel}** — {consejo}")
            elif color == "warning": st.warning(f"**{nivel}** — {consejo}")
            else: st.success(f"**{nivel}** — {consejo}")

        with st.expander("🔍 Ver análisis detallado de factores"):
            for f in factores:
                st.markdown(f"- {f}")
            st.caption(f"Puntaje de riesgo: {puntos}/15 | Temp: {temp}°C | Rocío: {rocio}°C | Viento: {viento} km/h | Humedad: {hum}%")

    st.divider()

    try:
        # FILTRAR POR USUARIO LOGUEADO
        res_h = supabase.table("registros_heladas").select("*").eq("productor_id", st.session_state.user_id).execute()
        df_h = pd.DataFrame(columns=['id', 'Fecha', 'Intensidad', 'Duracion'])

        if res_h.data:
            df_temp = pd.DataFrame(res_h.data)
            if 'Fecha' in df_temp.columns:
                df_temp['Fecha'] = pd.to_datetime(df_temp['Fecha'], errors='coerce')
                df_temp = df_temp.dropna(subset=['Fecha'])
                if not df_temp.empty:
                    df_h = df_temp

        from datetime import datetime, timezone
        hoy = datetime.now(timezone.utc)
        if not df_h.empty and pd.api.types.is_datetime64_any_dtype(df_h['Fecha']):
            df_h_anio = df_h[df_h['Fecha'].dt.year == hoy.year].copy()
            if not df_h_anio.empty:
                df_h_anio = df_h_anio.sort_values('Fecha')
                primera = df_h_anio.iloc[0]['Fecha']
                ultima = df_h_anio.iloc[-1]['Fecha']
                m1, m2, m3 = st.columns(3)
                m1.metric("🧊 1° Helada", primera.strftime('%d/%m'))
                m2.metric("🔥 Últ. Helada", ultima.strftime('%d/%m'))
                m3.metric("📅 Días Críticos", (ultima - primera).days)
                st.markdown("<h3 style='font-size: 20px;'>📊 Resumen del Ciclo</h3>", unsafe_allow_html=True)
                fuerte = df_h_anio.sort_values('Intensidad').iloc[0]
                st.info(f"❄️ **Más intensa:** {fuerte['Intensidad']}°C ({fuerte['Fecha'].strftime('%d/%m')}) | ⏳ **Total Horas Frío:** {df_h_anio['Duracion'].sum():.1f} hs")
            else:
                st.warning(f"No hay registros para el año {hoy.year}")
        else:
            st.info("A la espera de los primeros registros de heladas...")

        st.divider()
        with st.expander("➕ Registrar Nueva Helada", expanded=True):
            with st.form("form_helada", clear_on_submit=True):
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1: nueva_fecha = st.date_input("Fecha", value=datetime.now())
                with f_col2: nueva_int = st.text_input("Temp. (°C)", placeholder="-2.5")
                with f_col3: nueva_dur = st.number_input("Horas", min_value=0.0, step=0.5)
                submitted = st.form_submit_button("Añadir a Bitácora")

        if submitted:
            try:
                val_int = float(nueva_int.replace(',', '.'))
                supabase.table("registros_heladas").insert({
                    "Fecha": nueva_fecha.isoformat(),
                    "Intensidad": val_int,
                    "Duracion": nueva_dur,
                    "productor_id": st.session_state.user_id  # ← asociar al usuario
                }).execute()
                st.success("✅ ¡Registrada!")
                st.rerun()
            except ValueError:
                st.error("❌ Escribí la temperatura con números (ej: -3.5)")

        with st.expander("📋 Ver Historial de Registros", expanded=False):
            st.info("Para borrar: Seleccioná la fila y tocá la papelera 🗑️ arriba de la tabla.")
            df_display = df_h[['id', 'Fecha', 'Intensidad', 'Duracion']].sort_values('Fecha', ascending=False)
            edited_h = st.data_editor(df_display, key="visor_heladas", num_rows="dynamic", use_container_width=True,
                column_config={
                    "Fecha": st.column_config.DatetimeColumn("Fecha", format="DD/MM/YYYY"),
                    "Intensidad": st.column_config.NumberColumn("Temp °C", format="%.1f"),
                    "Duracion": None,
                    "id": None
                })
            if len(edited_h) < len(df_display):
                ids_originales = set(df_display['id'].dropna().tolist())
                ids_actuales = set(edited_h['id'].dropna().tolist())
                for id_b in ids_originales - ids_actuales:
                    supabase.table("registros_heladas").delete().eq("id", id_b).execute()
                st.rerun()

    except Exception as e:
        st.error(f"Error en el módulo: {e}")
# ==========================================================
elif menu == "📝 Bitácora":
    st.header("📝 Cuaderno de Campo Digital")

    with st.form("nueva_nota", clear_on_submit=False):
        st.subheader("Registrar Evento o Tarea")
        c1, c2 = st.columns(2)
        with c1:
            tarea = st.selectbox("Evento/Tarea", ["Fumigación", "Siembra", "Cosecha", "Fertilización", "Monitoreo", "❄️ Helada", "☄️ Granizo", "Otro"])
            lote = st.text_input("Lote", placeholder="Ej: Lote Norte")
        with c2:
            if tarea == "❄️ Helada":
                detalle_extra = st.selectbox("Intensidad de Helada", ["Leve (0° a -2°)", "Moderada (-2° a -4°)", "Fuerte (<-4°)"])
            elif tarea == "☄️ Granizo":
                detalle_extra = st.selectbox("Tamaño del Granizo", ["Pequeno (Arroz)", "Mediano (Uva)", "Grande (Huevo)"])
            else:
                detalle_extra = ""
            nota_adicional = st.text_area("Observaciones del evento", placeholder="Describa daños visibles o detalles...")
        btn_guardar = st.form_submit_button("💾 GUARDAR Y GENERAR REPORTE")

        if btn_guardar:
            if lote and tarea:
                try:
                    t_act = clima['temp'] if clima else 0
                    v_act = clima['v_vel'] if clima else 0
                    nota_final = f"[{detalle_extra}] {nota_adicional}" if detalle_extra else nota_adicional
                    datos = {
                        "tarea": tarea,
                        "lote": lote,
                        "nota": nota_final,
                        "clima_temp": t_act,
                        "clima_viento": v_act,
                        "productor_id": st.session_state.user_id  # ← asociar al usuario
                    }
                    supabase.table("bitacora").insert(datos).execute()
                    st.success(f"✅ ¡{tarea} registrada con éxito!")
                    link_wa = generar_link_whatsapp(tarea, lote, t_act, v_act, nota_final)
                    st.markdown(f"""
                        <a href="{link_wa}" target="_blank" style="text-decoration: none;">
                            <div style="background-color: #25D366; color: white; padding: 15px; text-align: center; border-radius: 10px; font-weight: bold; font-size: 18px; margin-top: 20px;">
                                📲 INFORMAR SINIESTRO/EVENTO POR WA
                            </div>
                        </a>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Completá Lote y Evento.")

    st.divider()

    with st.expander("📂 VER HISTORIAL COMPLETO DE ACTIVIDADES"):
        try:
            res = supabase.table("bitacora").select("*").eq("productor_id", st.session_state.user_id).order("fecha", desc=True).execute()
            if res.data:
                df_bit = pd.DataFrame(res.data)
                df_bit['fecha'] = pd.to_datetime(df_bit['fecha']).dt.strftime('%d/%m/%Y %H:%M')
                st.dataframe(df_bit[['fecha', 'tarea', 'lote', 'clima_temp', 'clima_viento', 'nota']], use_container_width=True,
                    column_config={
                        "clima_temp": st.column_config.NumberColumn("Temp (°C)", format="%.1f"),
                        "clima_viento": st.column_config.NumberColumn("Viento (km/h)", format="%.1f")
                    })

                st.divider()
                st.subheader("🗑️ Borrar Registro")
                opciones = {}
                for _, row in df_bit.iterrows():
                    key = f"{row['fecha']} — {row['tarea']} — {row['lote']}"
                    opciones[key] = res.data[_]['id']

                fila_sel = st.selectbox("Seleccioná el registro a eliminar:", list(opciones.keys()), key="sel_borrar_bitacora")

                if st.button("🗑️ ELIMINAR", type="primary", use_container_width=True, key="btn_borrar_bitacora"):
                    try:
                        supabase.table("bitacora").delete().eq("id", opciones[fila_sel]).execute()
                        st.success("✅ Registro eliminado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.info("No hay registros cargados.")
        except Exception as e:
            st.error(f"Error al cargar: {e}")
# ==========================================================
# MENÚ: ÍNDICES SATELITALES
# ==========================================================
# ==========================================================
# MENÚ: ÍNDICES SATELITALES — Google Earth Engine
# Reemplazá todo el bloque elif menu == "🛰️ Índices Satelitales":
# ==========================================================
elif menu == "🛰️ Índices Satelitales":
   
    import folium
    import geopandas as gpd
    import streamlit.components.v1 as components
    from datetime import datetime

    st.header("🛰️ Monitor Satelital — Google Earth Engine")

    # ── Configuración de índices disponibles ───────────────
    INDICES = {
        "NDVI":       {"desc": "Vigor Vegetal",        "emoji": "🍃"},
        "EVI":        {"desc": "Vegetación Mejorado",  "emoji": "🌱"},
        "NDWI":       {"desc": "Humedad Canopeo",      "emoji": "💧"},
        "NDRE":       {"desc": "Red Edge (Nitrógeno)", "emoji": "🌿"},
        "NDMI":       {"desc": "Humedad Cultivo",      "emoji": "💦"},
        "TRUE-COLOR": {"desc": "Foto Real",            "emoji": "📸"},
    }

   # ── Cargar límites administrativos ─────────────────────
    # ── Cargar límites administrativos ─────────────────────
    #import os
    # Esto mostrará en tu app la lista de archivos que hay en el servidor
    #st.write("Archivos detectados en el repositorio:", os.listdir())
    @st.cache_data
    def cargar_limites():
        import os
        import pandas as pd
        import geopandas as gpd

        # Forzamos las variables de entorno para las librerías geo
        #os.environ["PROJ_LIB"] = r"C:\Users\User\miniconda3\envs\geo_env\Library\share\proj"
        #os.environ["PROJ_DATA"] = r"C:\Users\User\miniconda3\envs\geo_env\Library\share\proj"

        gdfs = []

        # --- ARGENTINA ---
        if os.path.exists("gadm41_AGR_2.gpkg"):
            g = gpd.read_file("gadm41_AGR_2.gpkg", engine="pyogrio")
            g["PAIS"] = "Argentina"
            gdfs.append(g)

        # --- URUGUAY ---
        if os.path.exists("gadm41_URY.gpkg"):
            g = gpd.read_file("gadm41_URY.gpkg", layer="ADM_ADM_2", engine="pyogrio")
            g["PAIS"] = "Uruguay"
            gdfs.append(g)

        # --- PERU ---
        if os.path.exists("peru_25kb.json"):
            g = gpd.read_file("peru_25kb.json")
            g["PAIS"] = "Peru"
            if "NAME_2" not in g.columns: g["NAME_2"] = g["NAME_1"]
            gdfs.append(g)
        
        # --- PARAGUAY ---
        if os.path.exists("pry_25kb.json"):
            g = gpd.read_file("pry_25kb.json")
            g["PAIS"] = "Paraguay"
            if "NAME_2" not in g.columns: g["NAME_2"] = g["NAME_1"]
            gdfs.append(g)

        # --- BOLIVIA (REVISAR NOMBRE DE ARCHIVO) ---
        # Asegúrate que el archivo en GitHub se llame exactamente bolivia_25kb.json
        if os.path.exists("gadm41_BOL_2.json"):
            g = gpd.read_file("gadm41_BOL_2.json")
            g["PAIS"] = "Bolivia" # Asignación explícita
            
            # Limpieza de columnas para Bolivia
            if "NAME_1" not in g.columns and "name_1" in g.columns:
                g = g.rename(columns={"name_1": "NAME_1", "name_2": "NAME_2"})
            
            if "NAME_2" not in g.columns:
                g["NAME_2"] = g["NAME_1"]
            
            # Forzamos que no haya espacios raros
            g["NAME_1"] = g["NAME_1"].astype(str).str.strip()
            g["NAME_2"] = g["NAME_2"].astype(str).str.strip()
            
            gdfs.append(g)
        else:
            # Esto saldrá en la consola de Streamlit si el archivo no se encuentra
            print("ERROR: No se encontró bolivia_25kb.json")

        if gdfs:
            df_final = pd.concat(gdfs, ignore_index=True)
            # Homogeneizar tipos de datos para evitar el error de Arrow
            for col in ["NAME_1", "NAME_2", "PAIS"]:
                if col in df_final.columns:
                    df_final[col] = df_final[col].astype(str).replace("nan", "Desconocido")
            return gpd.GeoDataFrame(df_final)
        
        return None
    # --- Ejecución de la carga ---
    gdf_argentina = cargar_limites()
    #if gdf_argentina is not None:
    #    debug_bol = gdf_argentina[gdf_argentina["PAIS"] == "Bolivia"]
    #    st.write("Columnas detectadas en Bolivia:", debug_bol.columns.tolist())
    #    st.write("Primeras filas de Bolivia:", debug_bol[["PAIS", "NAME_1"]].head())
        # Comprobación silenciosa (no usamos st.write para evitar el error de Arrow)
    #if gdf_argentina is not None:
    #    bolivia_count = len(gdf_argentina[gdf_argentina["PAIS"] == "Bolivia"])
        # st.info(f"Carga exitosa: {bolivia_count} registros de Bolivia encontrados.") # Opcional para debug
    # ── Función principal GEE ──────────────────────────────
    @st.cache_data(ttl=3600)
    def obtener_capa_gee(lat, lon, indice, fecha_inicio, fecha_fin):
        try:
            punto = ee.Geometry.Point([lon, lat])
            region = punto.buffer(5000)  # 5km alrededor del centro

            s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterBounds(region)
                  .filterDate(fecha_inicio, fecha_fin)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                  .sort('CLOUDY_PIXEL_PERCENTAGE')
                  .first())

            if indice == "NDVI":
                capa = s2.normalizedDifference(['B8', 'B4']).rename('NDVI')
                vis = {"min": -0.1, "max": 0.8,
                       "palette": ['#d73027','#f46d43','#fee08b','#a6d96a','#1a9850']}

            elif indice == "EVI":
                capa = s2.expression(
                    '2.5 * ((NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1))',
                    {'NIR':  s2.select('B8').divide(10000),
                     'RED':  s2.select('B4').divide(10000),
                     'BLUE': s2.select('B2').divide(10000)}
                ).rename('EVI')
                vis = {"min": -0.1, "max": 0.8,
                       "palette": ['#d73027','#fee08b','#1a9850']}

            elif indice == "NDWI":
                capa = s2.normalizedDifference(['B3', 'B8']).rename('NDWI')
                vis = {"min": -0.5, "max": 0.5,
                       "palette": ['#d73027','#fee08b','#abd9e9','#2166ac']}

            elif indice == "NDRE":
                capa = s2.normalizedDifference(['B8A', 'B5']).rename('NDRE')
                vis = {"min": -0.1, "max": 0.5,
                       "palette": ['#d73027','#fee08b','#66bd63','#006837']}

            elif indice == "NDMI":
                capa = s2.normalizedDifference(['B8', 'B11']).rename('NDMI')
                vis = {"min": -0.5, "max": 0.3,
                       "palette": ['#d73027','#fee08b','#abd9e9','#2166ac']}

            elif indice == "TRUE-COLOR":
                capa = s2.select(['B4', 'B3', 'B2'])
                vis = {"min": 0, "max": 3000,
                       "bands": ['B4', 'B3', 'B2']}

            url = capa.visualize(**vis).getMapId()['tile_fetcher'].url_format

            # Fecha de la imagen
            fecha_img = ee.Date(s2.get('system:time_start')).format('dd/MM/yyyy').getInfo()
            nubes = s2.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()

            return url, fecha_img, round(nubes, 1)

        except Exception as e:
            return None, None, str(e)

    # ── Función para obtener valor puntual ─────────────────
    def obtener_valor_punto(lat, lon, indice, fecha_inicio, fecha_fin):
        try:
            punto = ee.Geometry.Point([lon, lat]).buffer(50)

            s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterBounds(punto)
                  .filterDate(fecha_inicio, fecha_fin)
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                  .sort('CLOUDY_PIXEL_PERCENTAGE')
                  .first())

            if indice == "NDVI":
                capa = s2.normalizedDifference(['B8', 'B4'])
            elif indice == "EVI":
                capa = s2.expression(
                    '2.5 * ((NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1))',
                    {'NIR': s2.select('B8').divide(10000),
                     'RED': s2.select('B4').divide(10000),
                     'BLUE': s2.select('B2').divide(10000)})
            elif indice == "NDWI":
                capa = s2.normalizedDifference(['B3', 'B8'])
            elif indice == "NDRE":
                capa = s2.normalizedDifference(['B8A', 'B5'])
            elif indice == "NDMI":
                capa = s2.normalizedDifference(['B8', 'B11'])
            else:
                return None

            val = capa.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=punto,
                scale=10
            ).getInfo()

            return list(val.values())[0]
        except:
            return None

    # ── UI — Selectores ────────────────────────────────────
    # ── UI — Selectores ────────────────────────────────────
    # ── UI — Selectores ────────────────────────────────────
    col_prov = "NAME_1"
    col_depto = "NAME_2"

    # Definimos las 4 columnas superiores
    c0, c1, c2, c3 = st.columns([1, 1, 1, 1])

    with c0:
        # AGREGAMOS BOLIVIA AQUÍ:
        pais_sel = st.selectbox("País:", ["Seleccionar...", "Argentina", "Bolivia", "Paraguay", "Peru", "Uruguay"])

    with c1:
        if pais_sel != "Seleccionar..." and gdf_argentina is not None:
            gdf_pais = gdf_argentina[gdf_argentina["PAIS"] == pais_sel]
            opciones_prov = sorted(gdf_pais[col_prov].unique())
            
            # AJUSTE DE ETIQUETAS:
            if pais_sel == "Argentina": label_prov = "Provincia:"
            elif pais_sel == "Peru": label_prov = "Departamento (Región):"
            elif pais_sel == "Bolivia": label_prov = "Departamento:" # <-- Nuevo
            elif pais_sel == "Paraguay": label_prov = "Departamento:"
            else: label_prov = "Departamento:"
            
            prov_sel = st.selectbox(label_prov, ["Seleccionar..."] + opciones_prov)
        else:
            prov_sel = st.selectbox("Provincia/Región:", ["Seleccionar..."], disabled=True)
            gdf_pais = None

    with c2:
        if pais_sel != "Seleccionar..." and prov_sel != "Seleccionar..." and gdf_pais is not None:
            deptos = sorted(gdf_pais[gdf_pais[col_prov] == prov_sel][col_depto].unique())
            
            # AJUSTE DE ETIQUETAS NIVEL 2:
            if pais_sel == "Argentina": label_depto = "Departamento (Cdad):"
            elif pais_sel == "Peru": label_depto = "Provincia:"
            elif pais_sel == "Bolivia": label_depto = "Provincia:" # <-- Nuevo
            elif pais_sel == "Paraguay": label_depto = "Distrito:"
            else: label_depto = "Sección:"
            
            depto_sel = st.selectbox(label_depto, ["Seleccionar..."] + deptos)
        else:
            depto_sel = st.selectbox("Zona/Distrito:", ["Esperando..."], disabled=True)

    with c3:
        indice_sel = st.selectbox(
            "Índice:",
            list(INDICES.keys()),
            format_func=lambda x: f"{INDICES[x]['emoji']} {x} — {INDICES[x]['desc']}"
        )
    # ── Rango de fechas (Debajo de los selectores) ──────────
    st.markdown("---") # Una línea divisoria para que se vea limpio
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        fecha_desde = st.date_input("Desde:", value=datetime(2025, 9, 1))
    with col_f2:
        fecha_hasta = st.date_input("Hasta:", value=datetime.now())

    # ── Renderizado del mapa (Ahora todas las variables existen) ──
    if (pais_sel != "Seleccionar..." and 
        prov_sel != "Seleccionar..." and 
        depto_sel not in ["Seleccionar...", "Esperando..."] and 
        gdf_pais is not None):
        
        # Aquí sigue el resto de tu código del mapa...
        gdf_loc = gdf_pais[
            (gdf_pais[col_prov] == prov_sel) &
            (gdf_pais[col_depto] == depto_sel)
        ]
        centro = gdf_loc.geometry.centroid.iloc[0]
        lat_c, lon_c = centro.y, centro.x

        with st.spinner(f"⏳ Cargando {indice_sel} desde GEE..."):
            url_capa, fecha_img, info_nubes = obtener_capa_gee(
                lat_c, lon_c, indice_sel,
                fecha_desde.strftime('%Y-%m-%d'),
                fecha_hasta.strftime('%Y-%m-%d')
            )

        if url_capa:
            # Métricas de la imagen
            mc1, mc2, mc3 = st.columns(3)
            mc1.metric("📅 Imagen del", fecha_img or "N/D")
            mc2.metric("☁️ Nubosidad", f"{info_nubes}%" if isinstance(info_nubes, float) else "N/D")

            # Valor puntual en el centro
            if indice_sel != "TRUE-COLOR":
                val_puntual = obtener_valor_punto(
                    lat_c, lon_c, indice_sel,
                    fecha_desde.strftime('%Y-%m-%d'),
                    fecha_hasta.strftime('%Y-%m-%d')
                )
                if val_puntual is not None:
                    mc3.metric(f"{indice_sel} zona", f"{val_puntual:.3f}")

            # ── Mapa Folium ────────────────────────────────
            m = folium.Map(
                location=[lat_c, lon_c],
                zoom_start=13,
                tiles=None
            )

            # Fondo satelital
            folium.TileLayer(
                tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attr="Esri",
                name="🛰️ Satélite",
                overlay=False,
                max_zoom=22
            ).add_to(m)

            # Capa GEE
            folium.TileLayer(
                tiles=url_capa,
                attr='Google Earth Engine',
                name=f'{INDICES[indice_sel]["emoji"]} {indice_sel}',
                overlay=True,
                opacity=0.8
            ).add_to(m)

            # Todos los deptos de la provincia en gris
            if gdf_pais is not None:
                gdf_prov = gdf_pais[gdf_pais[col_prov] == prov_sel]
                folium.GeoJson(
                    gdf_prov,
                    style_function=lambda x: {
                        'fillColor': '#333333',
                        'color': '#666666',
                        'weight': 1,
                        'fillOpacity': 0.2
                    }
                ).add_to(m)

            # Depto seleccionado resaltado
            folium.GeoJson(
                gdf_loc,
                style_function=lambda x: {
                    'fillColor': 'transparent',
                    'color': '#00ffcc',
                    'weight': 3,
                    'fillOpacity': 0,
                    'dashArray': '6 3'
                }
            ).add_to(m)

            # Marcador del centro
            folium.CircleMarker(
                location=[lat_c, lon_c],
                radius=6,
                color='#00ffcc',
                fill=True,
                fill_color='#00ffcc',
                fill_opacity=0.9,
                tooltip=f"{depto_sel}, {prov_sel}"
            ).add_to(m)

            folium.LayerControl(collapsed=False).add_to(m)
            m.fit_bounds(gdf_loc.total_bounds.tolist())

            # Render
            mapa_html = m.get_root().render()
            mapa_html = mapa_html.replace(
                '</head>',
                '<style>.leaflet-control-attribution{display:none!important;}</style></head>'
            )
            components.html(mapa_html, height=600)

            # ── Leyenda e interpretación ───────────────────
            st.markdown("---")

            interpretaciones = {
                "NDVI": {
                    "rangos": [
                        ("#d73027", "< 0.1", "Suelo desnudo / sin vegetación"),
                        ("#fee08b", "0.1 – 0.3", "Vegetación escasa o estresada"),
                        ("#a6d96a", "0.3 – 0.6", "Cultivo en desarrollo"),
                        ("#1a9850", "> 0.6", "Cultivo sano y denso"),
                    ],
                    "consejo": "Valores por debajo de 0.3 en plena temporada indican estrés hídrico o sanitario."
                },
                "EVI": {
                    "rangos": [
                        ("#d73027", "< 0.1", "Sin vegetación activa"),
                        ("#fee08b", "0.1 – 0.3", "Biomasa baja"),
                        ("#a6d96a", "0.3 – 0.5", "Cultivo en crecimiento"),
                        ("#1a9850", "> 0.5", "Alta biomasa — cultivo vigoroso"),
                    ],
                    "consejo": "EVI es más preciso que NDVI en zonas de alta densidad vegetal."
                },
                "NDWI": {
                    "rangos": [
                        ("#d73027", "< -0.2", "Suelo seco — estrés hídrico"),
                        ("#fee08b", "-0.2 – 0.0", "Humedad baja"),
                        ("#abd9e9", "0.0 – 0.3", "Humedad moderada"),
                        ("#2166ac", "> 0.3", "Alta humedad / agua"),
                    ],
                    "consejo": "Útil para detectar zonas anegadas o con déficit hídrico."
                },
                "NDRE": {
                    "rangos": [
                        ("#d73027", "< 0.1", "Deficiencia severa de clorofila"),
                        ("#fee08b", "0.1 – 0.2", "Bajo contenido de nitrógeno"),
                        ("#66bd63", "0.2 – 0.4", "Contenido normal"),
                        ("#006837", "> 0.4", "Alto contenido de clorofila"),
                    ],
                    "consejo": "NDRE es muy sensible al nitrógeno foliar — ideal para ajustar fertilización."
                },
                "NDMI": {
                    "rangos": [
                        ("#d73027", "< -0.2", "Estrés hídrico severo"),
                        ("#fee08b", "-0.2 – 0.0", "Humedad baja en canopeo"),
                        ("#abd9e9", "0.0 – 0.2", "Humedad normal"),
                        ("#2166ac", "> 0.2", "Canopeo bien hidratado"),
                    ],
                    "consejo": "NDMI detecta el agua dentro de las hojas — útil en pecanes y frutales."
                },
                "TRUE-COLOR": {
                    "rangos": [
                        ("#1a9850", "Verde", "Cultivo activo"),
                        ("#8B4513", "Marrón", "Suelo o rastrojo"),
                        ("#2166ac", "Azul oscuro", "Agua"),
                        ("#ffffff", "Blanco", "Nubes"),
                    ],
                    "consejo": "Foto real del satélite — útil para verificar estado general del lote."
                },
            }

            info = interpretaciones.get(indice_sel, {})
            rangos = info.get("rangos", [])
            consejo = info.get("consejo", "")
            emoji_idx = INDICES[indice_sel]['emoji'] if indice_sel in INDICES else "📊"

            # Construimos los cuadraditos de colores de forma ultra-simple
            html_rangos = ""
            for color, rango, desc in rangos:
                item_html = f"""
                <div style="display:inline-block; margin:5px; padding:8px; background:rgba(255,255,255,0.05); border-radius:5px; min-width:150px;">
                    <span style="display:inline-block; width:12px; height:12px; background:{color}; border-radius:2px; margin-right:5px;"></span>
                    <b style="color:white; font-size:12px;">{rango}</b>
                    <br><span style="color:#aaa; font-size:10px;">{desc}</span>
                </div>"""
                html_rangos += item_html

            # El contenedor principal sin saltos de línea extraños
            leyenda_html = f"""
            <div style="background:#050f0a; border:1px solid #00ffcc33; border-radius:10px; padding:15px;">
                <div style="color:#00ffcc; font-size:10px; margin-bottom:10px;">{emoji_idx} INTERPRETACIÓN — {indice_sel}</div>
                <div>{html_rangos}</div>
                <div style="color:#00ffcc; font-size:11px; margin-top:10px; border-top:1px solid #222; padding-top:5px;">💡 {consejo}</div>
            </div>
            """

            st.write(leyenda_html, unsafe_allow_html=True)
            # ── Descarga del reporte ───────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            fecha_rep = datetime.now().strftime('%d/%m/%Y %H:%M')
            texto_reporte = f"""INFORME DE MONITOREO SATELITAL — AGROGUARDIAN
=============================================
Ubicación : {depto_sel}, {prov_sel}
Índice    : {indice_sel} — {INDICES[indice_sel]['desc']}
Imagen del: {fecha_img or 'N/D'}
Nubosidad : {info_nubes}%
Generado  : {fecha_rep}
Fuente    : Google Earth Engine / Copernicus Sentinel-2
"""
            if indice_sel != "TRUE-COLOR" and val_puntual is not None:
                texto_reporte += f"Valor {indice_sel}: {val_puntual:.3f}\n"

            st.download_button(
                f"📥 Descargar reporte {depto_sel}",
                data=texto_reporte,
                file_name=f"satelital_{depto_sel}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )

        else:
            st.error(f"❌ No se pudo cargar la capa: {info_nubes}")
            st.info("💡 Probá cambiando el rango de fechas o reduciendo el filtro de nubosidad.")

    else:
        # Estado inicial — instrucciones
        st.markdown(f"""
        <div style="
            background: rgba(0,255,204,0.04);
            border: 1px solid #00ffcc22;
            border-radius: 12px;
            padding: 24px;
            font-family: 'Courier New', monospace;
            text-align: center;
            margin-top: 20px;
        ">
            <div style="color:#00ffcc; font-size:28px; margin-bottom:12px">🛰️</div>
            <div style="color:#00ffcc; font-size:14px; letter-spacing:2px; margin-bottom:8px">
                SELECCIONÁ PAÍS → PROVINCIA → ZONA → ÍNDICE
            </div>
            <div style="color:#ffffff44; font-size:11px">
                Imágenes Sentinel-2 vía Google Earth Engine · Resolución 10m
            </div>
            <div style="display:flex; justify-content:center; gap:20px; margin-top:20px; flex-wrap:wrap">
                {"".join([f'<div style="color:#00ffcc88; font-size:12px">{v["emoji"]} {k}</div>' for k, v in INDICES.items()])}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================================
# MENÚ: DIAGNÓSTICO IA
# ==========================================================
elif menu == "🔍 Diagnóstico IA":
    st.header("🔍 Laboratorio Móvil")

    if client is None:
        st.error("🚨 La IA no está configurada correctamente.")
        st.stop()

    if "resultado_analisis" not in st.session_state:
        st.session_state.resultado_analisis = None
    if "foto_bytes" not in st.session_state:
        st.session_state.foto_bytes = None

    # Cámara (funciona en móvil y desktop)
    img_camera = st.camera_input("📸 Capturar síntoma")
    if img_camera is not None:
        st.session_state.foto_bytes = img_camera.read()

    # Galería solo para desktop
    st.markdown("**💻 Desde la computadora podés subir una foto:**")
    img_upload = st.file_uploader("Seleccionar imagen", type=['jpg', 'jpeg', 'png'], key="uploader_galeria")
    if img_upload is not None:
        st.session_state.foto_bytes = img_upload.read()

    if st.session_state.foto_bytes:
        from PIL import Image
        import io
        imagen_pil = Image.open(io.BytesIO(st.session_state.foto_bytes))
        st.image(imagen_pil, caption="Muestra seleccionada", use_container_width=True)

        if st.button("🔬 ANALIZAR", type="primary", use_container_width=True):
            with st.status("Analizando...", expanded=True) as status:
                try:
                    prompt = """Sos un ingeniero agrónomo experto en cultivos extensivos e intensivos.

Analizá la imagen y respondé en este formato exacto:

## 🔍 Diagnóstico
Identificá claramente qué es lo que ves (plaga, enfermedad, deficiencia nutricional, daño abiótico, etc.)

## 🌱 Cultivo Afectado
Indicá el cultivo o especie si podés identificarlo.

## ⚠️ Nivel de Severidad
Clasificá como: Leve / Moderado / Severo / Crítico
Justificá brevemente.

## 🧪 Tratamiento Recomendado
- Producto/s recomendado/s con principio activo
- Dosis orientativa
- Momento de aplicación
- Condiciones ideales para aplicar (Delta T, viento, etc.)

## 🔄 Medidas Preventivas
Acciones para evitar recurrencia.

## ⚕️ Urgencia de Intervención
Indicá si requiere acción inmediata o puede esperar.

Respondé siempre en español. Si la imagen no muestra claramente un problema agronómico, indicalo y pedí una foto más cercana."""
                    response = client.generate_content([imagen_pil, prompt])
                    st.session_state.resultado_analisis = response.text
                    status.update(label="✅ Análisis completo", state="complete")
                except Exception as e:
                    st.error(f"Error en el análisis: {e}")
                    status.update(label="❌ Error", state="error")

    if st.session_state.resultado_analisis:
        st.markdown("### 📋 Resultado del Análisis")
        st.markdown(st.session_state.resultado_analisis)
        from datetime import datetime
        fecha_archivo = datetime.now().strftime("%Y%m%d_%H%M")
        pdf_buffer = generar_pdf(st.session_state.resultado_analisis, nombre_imagen="imagen")
        st.download_button(label="📄 Descargar Informe PDF", data=pdf_buffer, file_name=f"diagnostico_{fecha_archivo}.pdf", mime="application/pdf")

    st.divider()
    if st.button("🔄 REINICIAR"):
        st.session_state.resultado_analisis = None
        st.session_state.foto_bytes = None

elif menu == "💳 Suscripción PRO":
    # --- LOGO Y TÍTULO CENTRADOS ---
    # Creamos 3 columnas: la del medio (col_logo) contendrá el logo
    # El ratio [1, 0.5, 1] hace que la del medio sea pequeña y esté centrada
    empty1, col_logo, empty2 = st.columns([1, 0.5, 1])
    
    with col_logo:
        # Cargamos logo1.png del repo con un ancho pequeño (ej: 120)
        st.image("logo1.png", width=120)

    # Título centrado usando HTML
    st.markdown("<h1 style='text-align: center;'>AgroGuardian PRO</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #555;'>Accedé a la tecnología de precisión</h3>", unsafe_allow_html=True)
    
    st.write("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("""
        **Tu suscripción PRO incluye:**
        * 🛰️ **Índices avanzados:** Acceso total a NDVI, NDWI y FWI (Humedad y Fuego).
        * 📊 **Reportes PDF:** Descargas ilimitadas de diagnósticos para tus lotes.
        * 🔔 **Alertas Premium:** Notificaciones prioritarias de heladas y granizo.
        * La versión PRO de AgroGuardian te permite el acceso ilimitado a todas las funciones. 
        * Costo Mensual: U$S 20.00, se factura anualmente. 
        """)
    
    # ... (El resto de tu lógica de Mercado Pago se mantiene igual)        
    #with col2:
    #    st.metric("Costo Mensual", "U$S 20.00, se factura anualmente. Promo por este Mes U$S 200/año", help="Precio final en ARS")

    st.divider()

    # --- LÓGICA DE MERCADO PAGO ---
    try:
        # 1. Inicializar el SDK con tu Token de los Secrets
        sdk = mercadopago.SDK(st.secrets["MP_ACCESS_TOKEN"])

        # 2. Configurar la preferencia
        preference_data = {
            "items": [
                {
                    "title": "Suscripción AgroGuardian PRO",
                    "quantity": 1,
                    "unit_price": 300000,
                    "currency_id": "ARS"
                }
            ],
            "back_urls": {
                "success": "https://agroguardian-app.streamlit.app/?status=approved",
                "failure": "https://agroguardian-app.streamlit.app/?status=failure",
                "pending": "https://agroguardian-app.streamlit.app/?status=pending"
            },
            "auto_return": "approved",
        }

        preference_response = sdk.preference().create(preference_data)
        url_pago = preference_response["response"]["init_point"]

        # 3. Botón de Pago con estilo Mercado Pago
        st.markdown(f"""
            <div style="text-align: center;">
                <a href="{url_pago}" target="_blank" style="text-decoration: none;">
                    <button style="
                        background-color: #009EE3; 
                        color: white; 
                        padding: 18px 40px; 
                        border: none; 
                        border-radius: 8px; 
                        font-weight: bold; 
                        font-size: 18px;
                        cursor: pointer; 
                        width: 100%;
                        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);">
                        PAGAR CON MERCADO PAGO
                    </button>
                </a>
                <p style="color: #888; font-size: 12px; margin-top: 10px;">
                    🔒 Pago procesado de forma segura por Mercado Pago
                </p>
            </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"No se pudo cargar el módulo de pago: {e}")

# Esto crea un espacio vacío al final para que puedas scrollear 
# y la tabla suba por encima del logo rojo.
st.markdown("<br><br><br><br><br>", unsafe_allow_html=True)
