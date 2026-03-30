from streamlit_folium import st_folium
import streamlit as st
import google.generativeai as genai
import requests
import json
import os
import math
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

def generar_password_temporal():
    
    caracteres = string.ascii_letters + string.digits
    
    return ''.join(secrets.choice(caracteres) for _ in range(10))


# ==========================================================
# ==========================================================
# 1. CONFIGURACIÓN DE PÁGINA (Debe ser lo primero después de los imports)
# ==========================================================
st.set_page_config(page_title="AgroGuardian", page_icon="🌿", layout="wide")

# ==========================================================
# 2. ESTILOS CSS
# ==========================================================
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
""", unsafe_allow_html=True) # <--- AQUÍ ES DONDE SE CIERRA CORRECTAMENTE
# ==========================================================
# 2. SUPABASE
# ==========================================================
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("🚨 Error de conexión con Supabase.")
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
client = None
try:
    if "GOOGLE_API_KEY" in st.secrets:
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"Error al configurar el cliente: {e}")

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
            a, b = 17.27, 237.7
            alpha = ((a * t) / (b + t)) + math.log(h/100.0)
            rocio = (b * alpha) / (a - alpha)
            return {
                "temp": t, "hum": h, "v_vel": round(r["wind"]["speed"] * 3.6, 1),
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

    st.markdown("<p style='text-align:center; font-size:10px; opacity:0.7;'>PRECISION LAB v2.6</p>", unsafe_allow_html=True)
    st.divider()

    menu = st.radio(
        "MENÚ DE CONTROL",
        ["📊 Monitoreo Total", "🌧️ Pluviómetro", "💧 Balance Hídrico", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora", "🛰️ Índices Satelitales", "🔍 Diagnóstico IA", "🛰️ Rend. Inteligente"],
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
    """, height=60)

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

# ===========================
# MENÚ: MONITOREO TOTAL
# ===========================
if menu == "📊 Monitoreo Total":
    st.header("📊 Tablero de Control")

    # Pastillas GPS
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
        new_lat = c1.number_input(
            "Latitud",
             value=st.session_state.lat,
            format="%.6f",
            key="lat_config"
        )

        new_lon = c2.number_input(
            "Longitud",
             value=st.session_state.lon,
             format="%.6f",
             key="lon_config"
        )
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

    if clima:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric("Temperatura", f"{clima['temp']:.1f} °C")
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
# MENÚ: PLUVIÓMETRO
# ==========================================================
elif menu == "🌧️ Pluviómetro":
    st.header("🌧️ Pluviómetro Digital")
    st.markdown("""
<style>
usuario_id = st.session_state.get("usuario_id", "demo_user")
/* TARJETAS MÉTRICAS (igual que Monitoreo) */
[data-testid="stMetric"] {
    background-color: #0e1117;
    border: 1px solid #00ffc3;
    border-radius: 12px;
    padding: 15px;
}

/* TEXTO MÉTRICAS */
[data-testid="stMetricLabel"] {
    color: #00ffc3 !important;
}

[data-testid="stMetricValue"] {
    color: #00ffc3 !important;
    font-weight: bold;
}

/* BOTONES */
.stButton > button {
    background-color: #0e1117 !important;
    color: #00ffc3 !important;
    border: 1px solid #00ffc3 !important;
    border-radius: 10px !important;
    font-weight: bold;
}

.stButton > button:hover {
    background-color: #00ffc3 !important;
    color: #0e1117 !important;
}

/* BOTÓN DESCARGA */
.stDownloadButton > button {
    background-color: #0e1117 !important;
    color: #00ffc3 !important;
    border: 1px solid #00ffc3 !important;
    border-radius: 10px !important;
    font-weight: bold;
}

.stDownloadButton > button:hover {
    background-color: #00ffc3 !important;
    color: #0e1117 !important;
}

</style>
""", unsafe_allow_html=True)
    try:
        #res = supabase.table("registros_lluvia").select("*").execute()
        usuario_id = st.session_state.get("usuario_id", "demo_user")

        res = supabase.table("registros_lluvia") \
        .select("*") \
        .eq("productor_id", usuario_id) \
        .execute()
        if res.data and len(res.data) > 0:
            df = pd.DataFrame(res.data)
            df['fecha'] = pd.to_datetime(df['fecha'], format='mixed', utc=True)
            df['mm'] = pd.to_numeric(df['mm'], errors='coerce').fillna(0)
            from datetime import datetime, timezone
            hoy = datetime.now(timezone.utc)

            df_mes = df[(df['fecha'].dt.month == hoy.month) & (df['fecha'].dt.year == hoy.year)].copy()
            df_año = df[df['fecha'].dt.year == hoy.year].copy()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💧 Este Mes", f"{df_mes['mm'].sum():.1f} mm")
            c2.metric("📆 Acum. Anual", f"{df_año['mm'].sum():.1f} mm")
            c3.metric("⚡ Máx. Día", f"{df_mes['mm'].max() if not df_mes.empty else 0:.1f} mm")
            c4.metric("📊 Registros", f"{len(df)} eventos")

            st.divider()

            # --- BOTÓN WHATSAPP ---
            df_limpio = df[df['fecha'].notnull()].copy()
            ultimos = df_limpio.sort_values('fecha', ascending=False).head(10)
            detalle_tabla = ""
            for _, row in ultimos.iterrows():
                try:
                    f_str = row['fecha'].strftime('%d/%m')
                    detalle_tabla += f"📍 {f_str}: {row['mm']:.1f} mm\n"
                except:
                    continue

            mensaje_wa = (
                f"🌱 REPORTE AGROGUARDIAN\n"
                f"📅 Fecha: {hoy.strftime('%d/%m/%Y')}\n"
                f"--------------------------------\n"
                f"💧 RESUMEN:\n"
                f"• Mes: {df_mes['mm'].sum():.1f} mm\n"
                f"• Año: {df_año['mm'].sum():.1f} mm\n"
                f"--------------------------------\n"
                f"📋 ÚLTIMOS REGISTROS:\n"
                f"{detalle_tabla if detalle_tabla else 'Sin datos'}\n"
                f"--------------------------------"
            )
            mensaje_url = urllib.parse.quote(mensaje_wa)
            wa_url = f"https://wa.me/?text={mensaje_url}"

            st.markdown(f"""
                <a href="{wa_url}" target="_blank" style="text-decoration: none;">
                    <div style="background-color: #25D366; color: white; padding: 15px; border-radius: 12px; text-align: center; font-weight: bold; font-family: 'Segoe UI'; display: flex; align-items: center; justify-content: center; gap: 12px; box-shadow: 0px 6px 15px rgba(0,0,0,0.4);">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="25px">
                        ENVIAR REPORTE + TABLA DIARIA
                    </div>
                </a>
            """, unsafe_allow_html=True)
            st.write("")
            st.divider()

            # --- GRÁFICOS ---
            estilo_grafico = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#00ffc3"), height=350, margin=dict(l=10, r=10, t=30, b=20))

            st.subheader(f"📅 Detalle Diario — {hoy.strftime('%B %Y')}")
            df_mes['dia'] = df_mes['fecha'].dt.day
            df_dia = df_mes.groupby('dia')['mm'].sum().reindex(range(1, 32), fill_value=0).reset_index()
            fig1 = px.bar(df_dia, x='dia', y='mm', template="plotly_dark")
            fig1.update_traces(marker_color='#1f77b4')
            fig1.update_layout(**estilo_grafico)
            st.plotly_chart(fig1, use_container_width=True, config={'staticPlot': True})

            st.subheader(f"📊 Acumulado Mensual — Año {hoy.year}")
            meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            mensual = df_año.groupby(df_año['fecha'].dt.month)['mm'].sum().reindex(range(1, 13), fill_value=0)
            df_anual = pd.DataFrame({'Mes': meses_nombres, 'Prec_mm': mensual.values})
            fig2 = px.bar(df_anual, x='Mes', y='Prec_mm', template="plotly_dark", text_auto='.1f', title="Distribución de Lluvias por Mes")
            fig2.update_traces(marker_color='#00ffc3', textposition="outside")
            fig2.update_layout(**estilo_grafico)
            st.plotly_chart(fig2, use_container_width=True, config={'staticPlot': True})

            st.divider()

            # --- GENERAR EXCEL ---
            df_excel = df.copy().sort_values('fecha', ascending=False)
            df_excel['fecha'] = df_excel['fecha'].dt.tz_convert(None)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_excel[['fecha', 'lote', 'mm']].to_excel(writer, index=False, sheet_name='Registros_Lluvia')
                workbook = writer.book
                worksheet = writer.sheets['Registros_Lluvia']
                for i, col in enumerate(['fecha', 'lote', 'mm']):
                    column_len = max(df_excel[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, column_len)
            excel_data = output.getvalue()

            # --- TABLA EDITABLE ---
            st.subheader("📂 Base de Datos de Lluvias")
            st.info("💡 Editá valores en la tabla. Para eliminar usá el selector de abajo.")

            df_editable = df.copy().sort_values('fecha', ascending=False).reset_index(drop=True)

            edited_df = st.data_editor(
                df_editable[['id', 'fecha', 'lote', 'mm']],
                key="editor_lluvias",
                num_rows="fixed",
                use_container_width=True,
                disabled=["id", "fecha"],
                column_config={
                    "mm": st.column_config.NumberColumn("Milímetros", format="%.1f mm", min_value=0),
                    "fecha": st.column_config.DatetimeColumn("Fecha", format="DD/MM/YYYY HH:mm"),
                    "lote": "Lote",
                    "id": None
                }
            )

            if st.button("💾 GUARDAR CAMBIOS", use_container_width=True):
                try:
                    for _, row in edited_df.iterrows():
                        if pd.notnull(row['id']):
                            supabase.table("registros_lluvia").update({
                                "mm": float(row['mm']),
                                "lote": str(row['lote'])
                            }).eq("id", int(row['id'])).execute()
                    st.success("✅ Cambios guardados")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

            

            st.download_button(
                label="📥 DESCARGAR EXCEL",
                data=excel_data,
                file_name=f'Lluvias_AgroGuardian_{hoy.strftime("%Y-%m-%d")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True
            )

            # --- BORRADOR ---
            st.divider()

            opciones = {}
            for _, row in df_editable.iterrows():
                try:
                    fecha_str = pd.Timestamp(row['fecha']).tz_convert(None).strftime('%d/%m/%Y')
                except:
                    try:
                        fecha_str = pd.Timestamp(row['fecha']).tz_localize(None).strftime('%d/%m/%Y')
                    except:
                        fecha_str = "Sin fecha"
                key = f"{fecha_str} — {row['lote']} — {row['mm']:.1f} mm"
                opciones[key] = row['id']

            fila_seleccionada = st.selectbox("Seleccioná el registro a eliminar:", options=list(opciones.keys()), key="selector_borrar")

            if st.button("🗑️ ELIMINAR ESTE REGISTRO", type="primary", use_container_width=True):
                try:
                    id_borrar = opciones[fila_seleccionada]
                    supabase.table("registros_lluvia").delete().eq("id", id_borrar).execute()
                    st.success("✅ Registro eliminado correctamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")

            # --- REGISTRO AUTOMÁTICO SATELITAL ---
            st.divider()
            st.markdown("### 🛰️ Registro Automático desde Satélite")
            col_auto1, col_auto2 = st.columns([2, 1])

            with col_auto1:
                st.caption("Obtiene precipitaciones desde Open-Meteo usando tu ubicación GPS. Sin costo, sin límites.")

            with col_auto2:
                if st.button("📡 REGISTRAR HOY", type="primary"):
                    try:
                        from datetime import date
                        lat_auto = LAT if LAT else -38.29
                        lon_auto = LON if LON else -57.55
                        hoy_fecha = date.today().isoformat()
                        url_meteo = (f"https://api.open-meteo.com/v1/forecast?latitude={lat_auto}&longitude={lon_auto}&daily=precipitation_sum&timezone=America/Argentina/Buenos_Aires&start_date={hoy_fecha}&end_date={hoy_fecha}")
                        r = requests.get(url_meteo).json()
                        mm_hoy = r['daily']['precipitation_sum'][0] or 0.0
                        #supabase.table("registros_lluvia").insert({"fecha": hoy_fecha, "mm": mm_hoy, "lote": "🛰️ Automático (Open-Meteo)"}).execute()
                        usuario_id = st.session_state.get("usuario_id", "demo_user")
                        supabase.table("registros_lluvia").insert({
                            "fecha": hoy_fecha,
                            "mm": mm_hoy,
                            "lote": "🛰️ Automático (Open-Meteo)",
                            "productor_id": usuario_id
                        }).execute()
                        st.success(f"✅ Registrado: {mm_hoy:.1f} mm para hoy")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            if st.button("📅 IMPORTAR ÚLTIMOS 7 DÍAS"):
                try:
                    from datetime import date, timedelta
                    lat_auto = LAT if LAT else -38.29
                    lon_auto = LON if LON else -57.55
                    fecha_fin = date.today().isoformat()
                    fecha_ini = (date.today() - timedelta(days=7)).isoformat()
                    url_meteo = (f"https://api.open-meteo.com/v1/forecast?latitude={lat_auto}&longitude={lon_auto}&daily=precipitation_sum&timezone=America/Argentina/Buenos_Aires&start_date={fecha_ini}&end_date={fecha_fin}")
                    r = requests.get(url_meteo).json()
                    fechas = r['daily']['time']
                    lluvias = r['daily']['precipitation_sum']
                    registros = 0
                    for fecha, mm in zip(fechas, lluvias):
                        if mm and mm > 0:
                            supabase.table("registros_lluvia").insert({"fecha": fecha, "mm": mm, "lote": "🛰️ Automático (Open-Meteo)"}).execute()
                            registros += 1
                    st.success(f"✅ Importados {registros} días con lluvia")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        else:
            st.info("🛰️ No hay registros de lluvia cargados todavía.")

    except Exception as e:
        st.error(f"Error al procesar los datos de lluvia: {e}")

# ==========================================================
# MENÚ: BALANCE HÍDRICO
# ==========================================================
elif menu == "💧 Balance Hídrico":
    import folium
    from streamlit_folium import folium_static
    st.markdown("### Evapotranspiracion 💧 Blanney-Criddle")
    try:
        lat = LAT if LAT else -38.29
        lon = LON if LON else -57.55
        temp_media = st.session_state.clima_data['temp'] if 'clima_data' in st.session_state else 25.0
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
        kc = st.slider("Kc del Cultivo", 0.3, 1.2, 0.8)
        etc = eto_diaria * kc
        c1, c2, c3 = st.columns(3)
        c1.metric("ETo (Demanda)", f"{eto_diaria:.2f} mm")
        c2.metric("ETc (Consumo)", f"{etc:.2f} mm")
        c3.metric("Humedad Perfil", f"{hum_perfil_mm:.1f} mm", help="Agua en perfil 28-100cm")
        st.divider()
        st.markdown("### 🌱 Agua Útil en el Suelo - SEPA/INTA")
        st.markdown("""
        <div style="background-color:#111; padding:20px; border-radius:10px; text-align:center;">
            <p style="color:#00ffc3; font-family:monospace; font-size:14px; margin-bottom:10px;">🛰️ Mapas de Agua Útil en Suelo — SEPA/INTA</p>
            <p style="color:#aaa; font-family:monospace; font-size:12px; margin-bottom:15px;">Actualización cada 10 días | Balance hídrico satelital + estaciones INTA/SMN</p>
            <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
                <a href="https://sepa.inta.gob.ar/productos/agua_en_suelo/pj_10d/" target="_blank" style="background-color:#00ffc3; color:#000; padding:12px 24px; border-radius:8px; font-family:monospace; font-weight:bold; text-decoration:none; font-size:14px;">🌱 % Agua Útil (0-2m)</a>
                <a href="https://sepa.inta.gob.ar/productos/agua_en_suelo/ad_10d/" target="_blank" style="background-color:#00b4d8; color:#000; padding:12px 24px; border-radius:8px; font-family:monospace; font-weight:bold; text-decoration:none; font-size:14px;">💧 Agua Disponible (mm)</a>
            </div>
            <p style="color:#888; font-size:11px; margin-top:12px; font-family:monospace;">📡 Mismo producto que usa el SMN | Cubre región pampeana y NOA/NEA</p>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error en Balance Hídrico: {e}")

# ==========================================================
# MENÚ: RADAR GRANIZO|
# ==========================================================
elif menu == "⛈️ Radar Granizo":
    st.header("⛈️ Monitor de Tormentas y Granizo")

    if LAT and LON and clima:
        c1, c2, c3 = st.columns(3)
        hum = clima['hum']
        temp = clima['temp']
        presion = clima['presion']
        rocio = clima['rocio']
        with c1:
            riesgo = "ALTO" if hum > 80 and temp > 25 else "MEDIO" if hum > 60 else "BAJO"
            st.metric("Riesgo de Inestabilidad", riesgo, delta="Basado en Hum/Temp")
        with c2:
            st.metric("Presión Atmosférica", f"{presion} hPa")
        with c3:
            st.metric("Punto de Rocío", f"{rocio} °C", help="A mayor punto de rocío, más combustible para la tormenta")
        st.divider()
        capa = st.radio("Seleccionar Capa del Sensor:", ["Radar", "Rayos", "Nubes"], index=0)
        vistas = {"Radar": "radar", "Rayos": "thunder", "Nubes": "satellite"}
        st.markdown(f"### 🛰️ Sensor Activo: {capa}")
        url_windy = f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&overlay={vistas[capa]}&product=radar&menu=&message=true&marker=true&calendar=now&pressure=true&type=map&location=coordinates&detail=true&metricWind=km%2Fh&metricTemp=%C2%B0C&radarRange=-1"
        st.components.v1.iframe(url_windy, height=600)
        with st.expander("ℹ️ ¿Cómo leer el radar?"):
            st.write("""
            - **Colores Verdes/Azules:** Lluvia ligera o moderada.
            - **Colores Rojos/Amarillos:** Tormentas fuertes, posible granizo pequeño.
            - **Colores Púrpura/Blanco:** Celdas de granizo pesado o tormentas severas.
            - **Capa de Rayos:** Las cruces brillantes indican actividad eléctrica en tiempo real.
            """)
    else:
        st.warning("📍 Se requiere vincular el GPS en el panel lateral para centrar el radar en tu lote.")

# ==========================================================
# ==========================================================
# ==========================================================
# ========================================================== 
elif menu == "❄️ Análisis de Heladas": 

    st.markdown("<h2 style='font-size: 24px;'>❄️ Heladas Agrometeorológicas — Frutales</h2>", unsafe_allow_html=True) 

    # ========================================================== 
    # DATOS DE CULTIVOS: umbral de daño por estado fenológico 
    # ========================================================== 
    CULTIVOS = { 
        "🍎 Manzano": { 
            "estados": { 
                "Yema dormida":       -15.0, 
                "Yema hinchada":       -8.0, 
                "Puntas verdes":       -4.0, 
                "Media pulgada verde": -3.0, 
                "Punta rosada":        -2.8, 
                "Flor abierta":        -2.2, 
                "Fruto cuajado":       -1.7, 
            } 
        }, 
        "🍑 Duraznero": { 
            "estados": { 
                "Yema dormida":        -15.0, 
                "Yema hinchada":        -5.0, 
                "Botón rosado":         -3.9, 
                "Flor abierta":         -2.8, 
                "Plena floración":      -2.2, 
                "Fruto cuajado":        -1.1, 
            } 
        }, 
        "🍒 Cerezo": { 
            "estados": { 
                "Yema dormida":        -15.0, 
                "Yema hinchada":        -5.0, 
                "Botón floral":         -3.3, 
                "Flor abierta":         -2.8, 
                "Plena floración":      -2.2, 
                "Fruto cuajado":        -1.1, 
            } 
        }, 
        "🍐 Peral": { 
            "estados": { 
                "Yema dormida":        -15.0, 
                "Yema hinchada":        -7.0, 
                "Puntas verdes":        -4.0, 
                "Flor abierta":         -2.2, 
                "Plena floración":      -2.0, 
                "Fruto cuajado":        -1.7, 
            } 
        }, 
        "🫐 Ciruelo": { 
            "estados": { 
                "Yema dormida":        -15.0, 
                "Yema hinchada":        -5.5, 
                "Botón floral":         -3.9, 
                "Flor abierta":         -2.8, 
                "Plena floración":      -2.2, 
                "Fruto cuajado":        -1.1, 
            } 
        }, 
        "🌰 Almendro": { 
            "estados": { 
                "Yema dormida":        -15.0, 
                "Yema hinchada":        -6.0, 
                "Botón rosado":         -4.0, 
                "Flor abierta":         -2.2, 
                "Plena floración":      -2.0, 
                "Fruto cuajado":        -1.5, 
            } 
        }, 
        "🥜 Pistacho": { 
            "estados": { 
                "Yema dormida": -15.0, 
                "Yema hinchada": -6.5, 
                "Brote verde": -3.5, 
                "Floración": -2.5, 
                "Cuaje": -1.8, 
                "Fruto joven": -1.5, 
            } 
        }, 
        "🌰 Pecan": { 
            "estados": { 
                "Yema dormida": -18.0, 
                "Yema hinchada": -8.0, 
                "Brotación": -4.0, 
                "Hoja expandiéndose": -2.5, 
                "Floración": -2.0, 
                "Fruto cuajado": -1.5, 
            } 
        } 
    } 
    
    # ========================================================== 
    # SELECTOR DE CULTIVO Y ESTADO FENOLÓGICO 
    # ========================================================== 
    st.markdown("### 🌳 Configuración del Cultivo") 
    col_c1, col_c2 = st.columns(2) 
    with col_c1: 
        cultivo_sel = st.selectbox("Cultivo:", list(CULTIVOS.keys())) 
    with col_c2: 
        estado_sel = st.selectbox("Estado Fenológico:", list(CULTIVOS[cultivo_sel]["estados"].keys())) 

    umbral_daño = CULTIVOS[cultivo_sel]["estados"][estado_sel] 

    st.markdown(f""" 
    <div style='background:#161b22; padding:12px; border-radius:10px; border:1px solid #30363d; margin-bottom:12px;'> 
        <span style='color:#00ffc3; font-family:monospace; font-size:14px;'> 
            ⚠️ Temperatura de daño para <b>{cultivo_sel}</b> en <b>{estado_sel}</b>:  
            <span style='color:#ff4b4b; font-size:18px;'><b>{umbral_daño}°C</b></span> 
        </span> 
    </div> 
    """, unsafe_allow_html=True) 

    st.divider() 

    # ========================================================== 
    # CONDICIONES ACTUALES 
    # ========================================================== 
    st.markdown("### 🌡️ Condiciones Actuales") 

    if clima: 
        temp_actual = clima['temp'] 
        rocio = clima['rocio'] 
        viento = clima['v_vel'] 
        hum = clima['hum'] 
        
        margen = temp_actual - umbral_daño 

        c1, c2, c3, c4 = st.columns(4) 
        with c1: st.metric("🌡️ Temperatura", f"{temp_actual:.1f}°C", delta=f"{margen:+.1f}° del umbral") 
        with c2: st.metric("💧 Punto de Rocío", f"{rocio:.1f}°C") 
        with c3: st.metric("💨 Viento", f"{viento:.1f} km/h") 
        with c4: st.metric("💦 Humedad", f"{hum}%") 

        # --- ÍNDICE DE HELADA RADIATIVA --- 
        st.markdown("### 🔭 Índice de Helada Radiativa") 
        riesgo_rad = 0 
        factores_rad = [] 

        if viento < 5: 
            riesgo_rad += 3 
            factores_rad.append("🔴 Viento calmo — inversión térmica probable") 
        elif viento < 10: 
            riesgo_rad += 1 
            factores_rad.append("🟡 Viento leve") 
        else: 
            factores_rad.append("🟢 Viento suficiente — mezcla de aire activa") 

        if hum < 40: 
            riesgo_rad += 2 
            factores_rad.append("🔴 Humedad muy baja — enfriamiento nocturno intenso") 
        elif hum < 60: 
            riesgo_rad += 1 
            factores_rad.append("🟡 Humedad moderada") 
        else: 
            factores_rad.append("🟢 Humedad alta — amortigua el enfriamiento") 

        dif_rocio = temp_actual - rocio 
        if dif_rocio < 2: 
            riesgo_rad += 3 
            factores_rad.append("🔴 Punto de rocío muy cercano — escarcha posible") 
        elif dif_rocio < 5: 
            riesgo_rad += 1 
            factores_rad.append("🟡 Diferencia temp-rocío moderada") 
        else: 
            factores_rad.append("🟢 Diferencia temp-rocío alta") 

        if riesgo_rad >= 6: 
            st.error(f"🚨 RIESGO RADIATIVO EXTREMO — Condiciones ideales para helada severa esta noche") 
        elif riesgo_rad >= 4: 
            st.warning(f"⚠️ RIESGO RADIATIVO ALTO — Probabilidad elevada de helada nocturna") 
        elif riesgo_rad >= 2: 
            st.warning(f"🟡 RIESGO RADIATIVO MODERADO — Monitorear de madrugada") 
        else: 
            st.success(f"✅ RIESGO RADIATIVO BAJO — Condiciones desfavorables para helada") 

        with st.expander("🔍 Ver factores del índice radiativo"): 
            for f in factores_rad: 
                st.markdown(f"- {f}") 

        # --- ALERTA ESPECÍFICA POR CULTIVO --- 
        st.divider() 
        st.markdown("### 🌳 Alerta por Cultivo") 
        if temp_actual <= umbral_daño: 
            st.error(f"🚨 DAÑO EN CURSO — La temperatura actual ({temp_actual}°C) está por debajo del umbral de daño ({umbral_daño}°C) para {cultivo_sel} en {estado_sel}") 
        elif temp_actual <= umbral_daño + 2: 
            st.warning(f"⚠️ ALERTA CRÍTICA — Temperatura a {margen:.1f}° del umbral de daño. Activar protección.") 
        elif temp_actual <= umbral_daño + 5: 
            st.warning(f"🟡 PRECAUCIÓN — Temperatura a {margen:.1f}° del umbral. Mantener vigilancia.") 
        else: 
            st.success(f"✅ SIN RIESGO INMEDIATO — Margen de {margen:.1f}° sobre el umbral de daño.") 
    else: 
        st.info("📍 Activá el GPS para ver las condiciones actuales.") 

    st.divider() 

    # ========================================================== 
    # PRONÓSTICO 24HS CON OPEN-METEO 
    # ========================================================== 
    st.markdown("### 📅 Pronóstico Horario — Próximas 24 horas") 

    try: 
        lat_h = LAT if 'LAT' in locals() and LAT else -34.59 
        lon_h = LON if 'LON' in locals() and LON else -58.50 

        url_forecast = ( 
            f"https://api.open-meteo.com/v1/forecast?" 
            f"latitude={lat_h}&longitude={lon_h}" 
            f"&hourly=temperature_2m,relativehumidity_2m,windspeed_10m,cloudcover,dewpoint_2m" 
            f"&timezone=America/Argentina/Buenos_Aires" 
            f"&forecast_days=2" 
        ) 
        r_fc = requests.get(url_forecast).json() 
        horas = r_fc['hourly']['time'][:24] 
        temps = r_fc['hourly']['temperature_2m'][:24] 
        humedades = r_fc['hourly']['relativehumidity_2m'][:24] 
        vientos = r_fc['hourly']['windspeed_10m'][:24] 
        nubes = r_fc['hourly']['cloudcover'][:24] 
        rocio_fc = r_fc['hourly']['dewpoint_2m'][:24] 

        df_fc = pd.DataFrame({ 
            'hora': [h[11:16] for h in horas], 
            'temp': temps, 
            'hum': humedades, 
            'viento': vientos, 
            'nubes': nubes, 
            'rocio': rocio_fc 
        }) 

        df_fc['riesgo'] = df_fc['temp'].apply( 
            lambda t: '🚨 DAÑO' if t <= umbral_daño 
            else ('⚠️ ALERTA' if t <= umbral_daño + 2 
            else ('🟡 PRECAUCIÓN' if t <= umbral_daño + 5 else '✅ OK')) 
        ) 
        
        import plotly.graph_objects as go 
        fig = go.Figure() 
        fig.add_trace(go.Scatter(x=df_fc['hora'], y=df_fc['temp'], mode='lines+markers', name='Temperatura', line=dict(color='#00ffc3', width=2))) 
        fig.add_hline(y=umbral_daño, line_dash="dash", line_color="#ff4b4b", annotation_text=f"Umbral daño: {umbral_daño}°C") 

        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#00ffc3"), height=300) 
        st.plotly_chart(fig, use_container_width=True) 

        # Tabla resumen horaria 
        with st.expander("📋 Ver tabla horaria completa"): 
            st.dataframe(df_fc[['hora', 'temp', 'rocio', 'hum', 'viento', 'nubes', 'riesgo']], use_container_width=True) 

        # Mínima pronosticada
        temp_min = min(temps) 
        hora_min = df_fc.loc[df_fc['temp'].idxmin(), 'hora'] 

        st.markdown(f""" 
        <div style='background:#161b22; padding:12px; border-radius:10px; border:1px solid #30363d; margin-top:12px;'> 
            <span style='color:#00ffc3; font-family:monospace;'> 
                🌙 Mínima pronosticada: <b style='color:{"#ff4b4b" if temp_min <= umbral_daño else "#00ffc3"}'>{temp_min:.1f}°C</b>  
                a las <b>{hora_min}hs</b> —  
                {"🚨 POR DEBAJO DEL UMBRAL DE DAÑO" if temp_min <= umbral_daño else f"Margen de {temp_min - umbral_daño:.1f}° sobre el umbral"} 
            </span> 
        </div> 
        """, unsafe_allow_html=True) 

    except Exception as e: 
        st.error(f"Error al obtener pronóstico: {e}") 

    st.divider() 

    # ========================================================== 
    # HORAS DE FRÍO — MODELO UTAH
    # ==========================================================
    st.markdown("### 🧊 Horas de Frío Acumuladas — Modelo Utah")
    st.caption("Conteo de horas con temperatura entre 0°C y 7°C. Determina la dormancia y calidad de floración.")

    try:
        from datetime import date
        fecha_inicio_utah = st.date_input("Desde (inicio de otoño):", value=date(date.today().year, 4, 1), key="utah_inicio")
        fecha_fin_utah = date.today()
        url_utah = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={lat_h}&longitude={lon_h}"
            f"&hourly=temperature_2m"
            f"&timezone=America/Argentina/Buenos_Aires"
            f"&start_date={fecha_inicio_utah.isoformat()}"
            f"&end_date={fecha_fin_utah.isoformat()}"
        )
        r_utah = requests.get(url_utah).json()
        temps_utah = r_utah['hourly']['temperature_2m']

        # MÉTODO UTAH
        horas_frio = sum(1 for t in temps_utah if t is not None and 0 <= t <= 7)
        horas_negativas = sum(1 for t in temps_utah if t is not None and t < 0)

        # MÉTODO PASCALE-DAMARIO
        def unidades_pd(t):
            if t is None: return 0
            if t < 1.4: return 0
            elif t <= 2.4: return 0.5
            elif t <= 9.1: return 1
            elif t <= 12.4: return 0.5
            elif t <= 15.9: return 0
            elif t <= 18.0: return -0.5
            else: return -1

        unidades_pascale = sum(unidades_pd(t) for t in temps_utah)
        unidades_pascale = max(0, round(unidades_pascale))

        # REQUERIMIENTOS
        REQUERIMIENTOS_FRIO = {
            "🍎 Manzano":   1200,
            "🍑 Duraznero":  800,
            "🍒 Cerezo":    1000,
            "🍐 Peral":     1100,
            "🫐 Ciruelo":    700,
            "🌰 Almendro":  1000,
        }
        REQUERIMIENTOS_PD = {
            "🍎 Manzano":   1000,
            "🍑 Duraznero":  600,
            "🍒 Cerezo":     900,
            "🍐 Peral":      900,
            "🫐 Ciruelo":    500,
            "🌰 Almendro":   700,
        }

        req_utah = REQUERIMIENTOS_FRIO.get(cultivo_sel, 1000)
        req_pd = REQUERIMIENTOS_PD.get(cultivo_sel, 800)
        porc_utah = min(100, round((horas_frio / req_utah) * 100))
        porc_pd = min(100, round((unidades_pascale / req_pd) * 100))

        # MÉTRICAS UTAH
        st.markdown("#### Método Utah")
        c1, c2, c3 = st.columns(3)
        c1.metric("🧊 Horas de Frío (0-7°C)", f"{horas_frio} hs")
        c2.metric("❄️ Horas bajo 0°C", f"{horas_negativas} hs")
        c3.metric("🎯 Requerimiento", f"{req_utah} hs")
        st.progress(porc_utah / 100, text=f"Completado: {porc_utah}% del requerimiento")

        if porc_utah >= 100:
            st.success(f"✅ Requerimiento COMPLETO — Floración uniforme esperada.")
        elif porc_utah >= 70:
            st.warning(f"🟡 Requerimiento al {porc_utah}% — Floración puede ser irregular.")
        else:
            st.error(f"🔴 Déficit de frío ({porc_utah}%) — Riesgo de brotación irregular.")

        st.divider()

        # MÉTRICAS PASCALE-DAMARIO
        st.markdown("#### Método Pascale-Damario")
        st.caption("Desarrollado en Argentina. Pondera temperaturas con efecto positivo y negativo sobre la dormancia.")
        c4, c5 = st.columns(2)
        c4.metric("🌡️ Unidades de Frío (P-D)", f"{unidades_pascale} UF")
        c5.metric("🎯 Requerimiento", f"{req_pd} UF")
        st.progress(porc_pd / 100, text=f"Completado: {porc_pd}% del requerimiento")

        if porc_pd >= 100:
            st.success(f"✅ Requerimiento COMPLETO según Pascale-Damario.")
        elif porc_pd >= 70:
            st.warning(f"🟡 Requerimiento al {porc_pd}% según Pascale-Damario.")
        else:
            st.error(f"🔴 Déficit de frío ({porc_pd}%) según Pascale-Damario.")

        st.divider()

        # TABLA COMPARATIVA
        st.markdown("#### 📊 Comparación de Métodos")
        df_comp = pd.DataFrame({
            "Método": ["Utah", "Pascale-Damario"],
            "Unidades acumuladas": [f"{horas_frio} hs", f"{unidades_pascale} UF"],
            "Requerimiento": [f"{req_utah} hs", f"{req_pd} UF"],
            "Completado": [f"{porc_utah}%", f"{porc_pd}%"],
            "Estado": [
                "✅ Completo" if porc_utah >= 100 else "🟡 Parcial" if porc_utah >= 70 else "🔴 Déficit",
                "✅ Completo" if porc_pd >= 100 else "🟡 Parcial" if porc_pd >= 70 else "🔴 Déficit"
            ]
        })
        st.dataframe(df_comp, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error al calcular horas de frío: {e}")
    st.divider()
    # ==========================================================
    # REGISTRO HISTÓRICO DE HELADAS
    # ==========================================================
    try:
        res_h = supabase.table("registros_heladas").select("*").execute()
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
                m3.metric("📅 Días entre heladas", (ultima - primera).days)
                fuerte = df_h_anio.sort_values('Intensidad').iloc[0]
                st.info(f"❄️ **Más intensa:** {fuerte['Intensidad']}°C ({fuerte['Fecha'].strftime('%d/%m')}) | ⏳ **Total Horas Frío:** {df_h_anio['Duracion'].sum():.1f} hs")
            else:
                st.warning(f"No hay registros para el año {hoy.year}")
        else:
            st.info("A la espera de los primeros registros de heladas...")

        st.divider()
        with st.expander("➕ Registrar Nueva Helada", expanded=False):
            with st.form("form_helada", clear_on_submit=True):
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1: nueva_fecha = st.date_input("Fecha", value=datetime.now())
                with f_col2: nueva_int = st.text_input("Temp. (°C)", placeholder="-2.5")
                with f_col3: nueva_dur = st.number_input("Horas", min_value=0.0, step=0.5)
                submitted = st.form_submit_button("Añadir a Bitácora")

        if submitted:
            try:
                val_int = float(nueva_int.replace(',', '.'))
                supabase.table("registros_heladas").insert({"Fecha": nueva_fecha.isoformat(), "Intensidad": val_int, "Duracion": nueva_dur}).execute()
                st.success("✅ ¡Registrada!")
                st.rerun()
            except ValueError:
                st.error("❌ Escribí la temperatura con números (ej: -3.5)")

        with st.expander("📋 Ver Historial de Registros", expanded=False):
            st.info("Para borrar: Seleccioná la fila y tocá la papelera 🗑️ arriba de la tabla.")
            df_display = df_h[['id', 'Fecha', 'Intensidad', 'Duracion']].sort_values('Fecha', ascending=False)
            edited_h = st.data_editor(df_display, key="visor_heladas", num_rows="dynamic", use_container_width=True,
                column_config={"Fecha": st.column_config.DatetimeColumn("Fecha", format="DD/MM/YYYY"),
                               "Intensidad": st.column_config.NumberColumn("Temp °C", format="%.1f"),
                               "Duracion": None, "id": None})
            if len(edited_h) < len(df_display):
                ids_originales = set(df_display['id'].dropna().tolist())
                ids_actuales = set(edited_h['id'].dropna().tolist())
                for id_b in ids_originales - ids_actuales:
                    supabase.table("registros_heladas").delete().eq("id", id_b).execute()
                st.rerun()

    except Exception as e:
        st.error(f"Error en el módulo: {e}")

# ==========================================================
# MENÚ: BITÁCORA
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
                    datos = {"tarea": tarea, "lote": lote, "nota": nota_final, "clima_temp": t_act, "clima_viento": v_act}
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
            res = supabase.table("bitacora").select("*").order("fecha", desc=True).execute()
            if res.data:
                df_bit = pd.DataFrame(res.data)
                df_bit['fecha'] = pd.to_datetime(df_bit['fecha']).dt.strftime('%d/%m/%Y %H:%M')
                st.dataframe(df_bit[['fecha', 'tarea', 'lote', 'clima_temp', 'clima_viento', 'nota']], use_container_width=True,
                    column_config={"clima_temp": st.column_config.NumberColumn("Temp (°C)", format="%.1f"), "clima_viento": st.column_config.NumberColumn("Viento (km/h)", format="%.1f")})
            else:
                st.info("No hay registros cargados.")
        except Exception as e:
            st.error(f"Error al cargar: {e}")

# ========================================================== 
# CONTINUACIÓN DEL CÓDIGO (Ej: Bitácora)
# ==========================================================
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
#Simulacion rendimientos
#===========================================================
# ================================================
# MENÚ: RENDIMIENTO INTELIGENTE
# ================================================
import streamlit as st
import ee
import json
import google.generativeai as genai
import folium
from streamlit_folium import st_folium
import numpy as np

# --- 1. CONFIGURACIÓN DE IA (Gemini 1.5 Flash) ---
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash') 
else:
    st.warning("Falta GOOGLE_API_KEY en los Secrets")

# --- 2. CONEXIÓN A EARTH ENGINE ---
@st.cache_resource
def conectar_geoprocesamiento():
    if "JSON_LLAVE" in st.secrets:
        try:
            info_llave = json.loads(st.secrets["JSON_LLAVE"])
            credentials = ee.ServiceAccountCredentials(
                info_llave['client_email'], 
                key_data=st.secrets["JSON_LLAVE"]
            )
            ee.Initialize(credentials, project='agroguardian-ee')
            return True
        except Exception as e:
            st.sidebar.error(f"Error de conexión GEE: {e}")
            return False
    return False

ee_conectado = conectar_geoprocesamiento()

# --- 3. FUNCIÓN DEL MAPA (Definida arriba para evitar NameError) ---
@st.cache_data
def obtener_mapa_ndvi(lat, lon):
    try:
        punto = ee.Geometry.Point([lon, lat])
        # Filtramos por las fechas más recientes de esta temporada
        coleccion = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                     .filterBounds(punto.buffer(5000)) 
                     .filterDate('2025-01-01', '2026-03-26') 
                     .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                     .median())
        
        ndvi = coleccion.normalizedDifference(['B8', 'B4']).rename('NDVI')
        return ndvi
    except Exception as e:
        return None

if menu == "🛰️ Rend. Inteligente":
    import numpy as np
    import pandas as pd

    st.header("🛰️ Simulación de Rendimiento en Frutales")
    st.caption("Modelo multivariable: EVI · NDWI · LST — Sentinel-2 + MODIS")

    # ← AGREGÁ ESTO
    if "ee_conectado" not in st.session_state:
        try:
            info_llave = json.loads(st.secrets["JSON_LLAVE"])
            credentials = ee.ServiceAccountCredentials(
                info_llave['client_email'],
                key_data=st.secrets["JSON_LLAVE"]
            )
            ee.Initialize(credentials, project='agroguardian-ee')
            st.session_state.ee_conectado = True
        except Exception as e:
            st.error(f"❌ Error conectando Earth Engine: {e}")
            st.stop()

    ee_conectado = st.session_state.ee_conectado

    if not ee_conectado:
        st.error("⚠️ Error de conexión con Earth Engine.")
        st.stop()
    # ================================
    # ESTADOS
    # ================================
    for key, default in {
        "poligono": None,
        "puntos_rinde": [],
        "ultimo_click": None
    }.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # ================================
    # INPUTS GENERALES
    # ================================
    col1, col2, col3 = st.columns(3)
    with col1:
        lat = st.number_input("Latitud", value=-31.3697, format="%.4f")
    with col2:
        lon = st.number_input("Longitud", value=-58.1418, format="%.4f")
    with col3:
        densidad = st.number_input("🌳 Plantas/ha", value=400, step=10)

    # ================================
    # FUNCIONES SATELITALES
    # ================================
    @st.cache_data
    def obtener_indices(coords):
        try:
            poligono_ee = ee.Geometry.Polygon(coords)

            # Sentinel-2 — EVI y NDWI
            s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                  .filterBounds(poligono_ee)
                  .filterDate('2025-09-01', '2026-03-26')
                  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                  .sort('CLOUDY_PIXEL_PERCENTAGE')
                  .first())

            if not s2:
                return None, None, None

            # EVI = 2.5 * (NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1)
            evi = s2.expression(
                '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))',
                {
                    'NIR':  s2.select('B8').divide(10000),
                    'RED':  s2.select('B4').divide(10000),
                    'BLUE': s2.select('B2').divide(10000)
                }
            ).rename('EVI').clip(poligono_ee)

            # NDWI = (GREEN - NIR) / (GREEN + NIR)
            ndwi = s2.normalizedDifference(['B3', 'B8']).rename('NDWI').clip(poligono_ee)

            # LST desde MODIS Terra (1km resolución)
            lst = (ee.ImageCollection("MODIS/061/MOD11A1")
                   .filterBounds(poligono_ee)
                   .filterDate('2025-09-01', '2026-03-26')
                   .mean()
                   .select('LST_Day_1km')
                   .multiply(0.02).subtract(273.15)  # Kelvin → Celsius
                   .rename('LST')
                   .clip(poligono_ee))

            return evi, ndwi, lst

        except Exception as e:
            st.error(f"❌ Error cargando índices: {e}")
            return None, None, None

    @st.cache_data
    def obtener_dem(lat, lon):
        try:
            dem = ee.Image("USGS/SRTMGL1_003")
            punto = ee.Geometry.Point([lon, lat])
            return dem.clip(punto.buffer(5000))
        except:
            return None

    def extraer_valores(punto_lat, punto_lon, evi, ndwi, lst):
        try:
            p = ee.Geometry.Point([punto_lon, punto_lat])
            vals = ee.Image.cat([evi, ndwi, lst]).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=p.buffer(15),
                scale=10
            ).getInfo()
            return vals
        except Exception as e:
            return {}

    # ================================
    # FASE 1: DIBUJAR POLÍGONO
    # ================================
    if not st.session_state.poligono:
        from folium.plugins import Draw

        st.subheader("📐 Paso 1: Delimitá el lote")
        st.info("Dibujá el rectángulo sobre el lote y luego presioná **Save**")

        m = folium.Map(location=[lat, lon], zoom_start=16,
                       tiles="Esri.WorldImagery")
        folium.Marker([lat, lon], popup="Centro",
                      icon=folium.Icon(color="red", icon="star")).add_to(m)
        Draw(export=False, draw_options={
            'polyline': False, 'rectangle': True, 'polygon': True,
            'circle': False, 'marker': False, 'circlemarker': False
        }).add_to(m)

        mapa = st_folium(m, width=720, height=520,
                         key="mapa_dibujo",
                         returned_objects=["all_drawings", "last_active_drawing"])

        # Capturar dibujo sin rerun inmediato
        dibujo = None
        if mapa.get("last_active_drawing"):
            dibujo = mapa["last_active_drawing"]
        elif mapa.get("all_drawings") and len(mapa["all_drawings"]) > 0:
            dibujo = mapa["all_drawings"][-1]

        if dibujo:
            st.session_state.poligono = dibujo
            st.success("✅ Lote capturado — presioná el botón para continuar")
            if st.button("➡️ Continuar al análisis", key="btn_continuar"):
                st.rerun()
        else:
            st.stop()
    # ← FASE 2 EMPIEZA ACÁ
    #st.write(f"✅ DEBUG: Polígono guardado, avanzando a Fase 2")
    
    coords = st.session_state.poligono["geometry"]["coordinates"]
    #st.write(f"✅ DEBUG: Coords tipo={type(coords)}, len={len(coords)}")

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.success(f"✅ Lote definido — {len(st.session_state.puntos_rinde)} punto(s) cargado(s)")
    with col_b:
        if st.button("🔄 Redibujar"):
            for k in ["poligono", "puntos_rinde", "ultimo_click"]:
                st.session_state[k] = None if k != "puntos_rinde" else []
            st.rerun()

    # Cargar índices con debug
    st.write("⏳ DEBUG: Iniciando carga de índices...")
    with st.spinner("🛰️ Cargando índices satelitales..."):
        evi, ndwi, lst = obtener_indices(coords)
        dem = obtener_dem(lat, lon)

    #st.write(f"DEBUG evi={evi}, ndwi={ndwi}, lst={lst}, dem={dem}")

    if evi is None or ndwi is None or lst is None:
        st.error("❌ No se pudieron cargar los índices.")
        st.stop()
    # ================================
    # ================================
    # FASE 2: ÍNDICES + PUNTOS + MODELO
    # ================================
    coords = st.session_state.poligono["geometry"]["coordinates"]
    # Calcular área del lote
    try:
        poligono_ee = ee.Geometry.Polygon(coords)
        area_m2 = poligono_ee.area().getInfo()
        area_ha = area_m2 / 10000
        st.info(f"📐 Superficie del lote: **{area_m2:,.0f} m²** ({area_ha:.2f} ha)")
    except Exception as e:
        st.warning(f"⚠️ No se pudo calcular el área: {e}")
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.success(f"✅ Lote definido — {len(st.session_state.puntos_rinde)} punto(s) cargado(s)")
    with col_b:
        if st.button("🔄 Redibujar", key="btn_redibujar_fase2"):
            for k in ["poligono", "puntos_rinde", "ultimo_click"]:
                st.session_state[k] = None if k != "puntos_rinde" else []
            st.rerun()
    # Cargar índices
    with st.spinner("🛰️ Cargando índices satelitales..."):
        evi, ndwi, lst = obtener_indices(tuple(map(tuple, coords[0])) if coords else coords)
        dem = obtener_dem(lat, lon)

    if not evi or not ndwi or not lst:
        st.error("❌ No se pudieron cargar los índices. Verificá el polígono o el rango de fechas.")
        st.stop()

    # ================================
    # MAPA PRINCIPAL — EVI + NDWI + LST
    # ================================
    m2 = folium.Map(location=[lat, lon], zoom_start=16, tiles="Esri.WorldImagery")

    try:
        # EVI — verde vegetal
        url_evi = evi.visualize(
            min=0.1, max=0.7,
            palette=['#d73027','#fdae61','#a6d96a','#1a9850']
        ).getMapId()['tile_fetcher'].url_format
        folium.TileLayer(tiles=url_evi, attr='GEE', name='EVI (vigor)',
                         overlay=True, opacity=0.65).add_to(m2)

        # NDWI — humedad
        url_ndwi = ndwi.visualize(
            min=-0.3, max=0.3,
            palette=['#d7191c','#ffffbf','#2c7bb6']
        ).getMapId()['tile_fetcher'].url_format
        folium.TileLayer(tiles=url_ndwi, attr='GEE', name='NDWI (humedad)',
                         overlay=True, opacity=0.0).add_to(m2)  # oculto por defecto

        # LST — temperatura
        url_lst = lst.visualize(
            min=15, max=40,
            palette=['#313695','#74add1','#ffffbf','#f46d43','#a50026']
        ).getMapId()['tile_fetcher'].url_format
        folium.TileLayer(tiles=url_lst, attr='GEE', name='LST (temp. suelo)',
                         overlay=True, opacity=0.0).add_to(m2)  # oculto por defecto

    except Exception as e:
        st.error(f"❌ Error visualizando capas: {e}")

    # Polígono del lote
    folium.GeoJson(
        st.session_state.poligono,
        name="Lote",
        style_function=lambda x: {"color": "yellow", "weight": 2, "fillOpacity": 0}
    ).add_to(m2)

    # Marcadores de puntos guardados
    for i, p in enumerate(st.session_state.puntos_rinde):
        folium.Marker(
            [p["lat"], p["lon"]],
            popup=f"Punto {i+1}: {p['rend']} kg/ha",
            icon=folium.Icon(color="blue", icon="leaf")
        ).add_to(m2)

    folium.LayerControl().add_to(m2)

    st.subheader("🌿 Paso 2: Hacé click en puntos de muestra dentro del lote")
    mapa2 = st_folium(m2, width=720, height=520,
                      key="mapa_indices",
                      returned_objects=["last_clicked"])

    # Captura click
    if mapa2 and mapa2.get("last_clicked"):
        st.session_state.ultimo_click = mapa2["last_clicked"]

    # Formulario de carga
    if st.session_state.ultimo_click:
        uc = st.session_state.ultimo_click
        st.info(f"📍 Punto: {uc['lat']:.5f}, {uc['lng']:.5f}")
        rend = st.number_input("📦 Rendimiento (kg/ha)", min_value=0.0, step=50.0)

        if st.button("💾 Guardar punto de muestra", key="btn_guardar"):
            ya_existe = any(
                abs(p["lat"] - uc["lat"]) < 0.00001 and
                abs(p["lon"] - uc["lng"]) < 0.00001
                for p in st.session_state.puntos_rinde
            )
            if not ya_existe:
                st.session_state.puntos_rinde.append({
                    "lat": uc["lat"], "lon": uc["lng"], "rend": rend
                })
                st.success(f"✅ Guardado: {rend} kg/ha")
            else:
                st.warning("⚠️ Ese punto ya existe")
            st.rerun()

    # Tabla de puntos
    if st.session_state.puntos_rinde:
        df_pts = pd.DataFrame(st.session_state.puntos_rinde)
        df_pts.index += 1
        df_pts.columns = ["Lat", "Lon", "kg/ha"]
        st.dataframe(df_pts, use_container_width=True)

        if st.button("🗑️ Limpiar puntos", key="btn_limpiar"):
            st.session_state.puntos_rinde = []
            st.session_state.ultimo_click = None
            st.rerun()

    # ================================
    # MODELO MULTIVARIABLE
    # ================================
    n_puntos = len(st.session_state.puntos_rinde)
    st.write(f"🔬 Puntos cargados: **{n_puntos}/3**")

    if n_puntos >= 3:

        evi_vals, ndwi_vals, lst_vals, rend_vals = [], [], [], []

        with st.spinner("🔄 Extrayendo índices satelitales por punto..."):
            for pt in st.session_state.puntos_rinde:
                vals = extraer_valores(pt["lat"], pt["lon"], evi, ndwi, lst)
                e = vals.get("EVI")
                w = vals.get("NDWI")
                l = vals.get("LST")

                if e is not None and w is not None and l is not None:
                    evi_vals.append(e)
                    ndwi_vals.append(w)
                    lst_vals.append(l)
                    rend_vals.append(pt["rend"])
                else:
                    st.warning(f"⚠️ Sin datos en {pt['lat']:.4f}, {pt['lon']:.4f} — {vals}")

        st.write(f"✅ Puntos con índices válidos: **{len(evi_vals)}/{n_puntos}**")

        if len(evi_vals) >= 3:

            # Regresión múltiple: Rend = a*EVI + b*NDWI + c*LST + d
            X = np.column_stack([evi_vals, ndwi_vals, lst_vals, np.ones(len(evi_vals))])
            y = np.array(rend_vals)
            coefs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
            a, b, c, d = coefs

            st.success(f"📈 Modelo: Rend = {a:.1f}·EVI + {b:.1f}·NDWI + {c:.1f}·LST + {d:.1f}")

            # Imagen de rendimiento estimado
            rend_est = (
                evi.multiply(a)
                .add(ndwi.multiply(b))
                .add(lst.multiply(c))
                .add(d)
                .multiply(densidad / 400)
            )

            # Umbrales zonas de manejo
            rend_arr = np.array(rend_vals)
            p33 = float(np.percentile(rend_arr, 33))
            p66 = float(np.percentile(rend_arr, 66))
            max_r = float(rend_arr.max() * 1.2)
            min_r = max(0, float(rend_arr.min() * 0.8))

            # Zonas de manejo: bajo / medio / alto
            zonas = (
                rend_est.where(rend_est.lt(p33), 1)
                        .where(rend_est.gte(p33).And(rend_est.lt(p66)), 2)
                        .where(rend_est.gte(p66), 3)
            )

            # ================================
            # MAPA FINAL
            # ================================
            # ================================
            # MAPA FINAL
            # ================================
            import math

            def generar_grilla(coords, rend_est, a_coef, b_coef, p33, p66, densidad):
                """Divide el lote en celdas y estima rendimiento por celda"""
                # Obtener bounding box del polígono
                puntos = coords[0]
                lats = [p[1] for p in puntos]
                lons = [p[0] for p in puntos]
                lat_min, lat_max = min(lats), max(lats)
                lon_min, lon_max = min(lons), max(lons)

                # Tamaño de celda ~20x20 metros en grados
                delta_lat = 20 / 111320
                delta_lon = 20 / (111320 * math.cos(math.radians((lat_min + lat_max) / 2)))

                celdas = []
                lat = lat_min
                while lat < lat_max:
                    lon = lon_min
                    while lon < lon_max:
                        centro_lat = lat + delta_lat / 2
                        centro_lon = lon + delta_lon / 2

                        # Esquinas de la celda
                        celda_coords = [
                            [lon,           lat],
                            [lon + delta_lon, lat],
                            [lon + delta_lon, lat + delta_lat],
                            [lon,           lat + delta_lat],
                            [lon,           lat]
                        ]

                        try:
                            p = ee.Geometry.Point([centro_lon, centro_lat])
                            val = rend_est.reduceRegion(
                                reducer=ee.Reducer.mean(),
                                geometry=p.buffer(10),
                                scale=10
                            ).getInfo()

                            rend_val = list(val.values())[0] if val else None

                            if rend_val is not None:
                                if rend_val < p33:
                                    color = "#ffffcc"
                                    zona = f"Bajo: {rend_val:.0f} kg/ha"
                                elif rend_val < p66:
                                    color = "#fd8d3c"
                                    zona = f"Medio: {rend_val:.0f} kg/ha"
                                else:
                                    color = "#e31a1c"
                                    zona = f"Alto: {rend_val:.0f} kg/ha"

                                celdas.append({
                                    "coords": celda_coords,
                                    "color": color,
                                    "zona": zona,
                                    "rend": rend_val
                                })
                        except:
                            pass

                        lon += delta_lon
                    lat += delta_lat

                return celdas

            m3 = folium.Map(location=[lat, lon], zoom_start=17,
                            tiles="Esri.WorldImagery")

            try:
                # CAPA 1: Mapa de calor continuo GEE
                url_rend = rend_est.visualize(
                    min=min_r, max=max_r,
                    palette=['#ffffcc', '#fed976', '#fd8d3c', '#e31a1c']
                ).getMapId()['tile_fetcher'].url_format
                folium.TileLayer(tiles=url_rend, attr='GEE',
                                 name='🌡️ Calor continuo',
                                 overlay=True, opacity=0.75).add_to(m3)

                # CAPA 2: Grilla de celdas
                grilla_group = folium.FeatureGroup(name="🟥 Grilla por zonas", show=False)

                with st.spinner("⏳ Generando grilla de celdas..."):
                    celdas = generar_grilla(coords, rend_est, a_coef, b_coef, p33, p66, densidad)

                for celda in celdas:
                    folium.Polygon(
                        locations=[[p[1], p[0]] for p in celda["coords"]],
                        color="white",
                        weight=0.5,
                        fill=True,
                        fill_color=celda["color"],
                        fill_opacity=0.7,
                        tooltip=celda["zona"]
                    ).add_to(grilla_group)

                grilla_group.add_to(m3)
                st.success(f"✅ Grilla generada: {len(celdas)} celdas")

                # CAPA 3: Zonas de manejo GEE
                url_zonas = zonas.visualize(
                    min=1, max=3,
                    palette=['#ffffcc', '#fd8d3c', '#e31a1c']
                ).getMapId()['tile_fetcher'].url_format
                folium.TileLayer(tiles=url_zonas, attr='GEE',
                                 name='🗺️ Zonas Bajo/Medio/Alto',
                                 overlay=True, opacity=0.0).add_to(m3)

            except Exception as e:
                st.error(f"❌ Error mapa final: {e}")

            # Polígono del lote
            folium.GeoJson(
                st.session_state.poligono,
                name="Lote",
                style_function=lambda x: {"color": "white", "weight": 2, "fillOpacity": 0}
            ).add_to(m3)

            # Marcadores pequeños puntos de muestra
            for i, pt in enumerate(st.session_state.puntos_rinde):
                folium.CircleMarker(
                    location=[pt["lat"], pt["lon"]],
                    radius=5,
                    color="white",
                    fill=True,
                    fill_color="white",
                    fill_opacity=0.9,
                    tooltip=f"Muestra {i+1}: {pt['rend']} kg/ha"
                ).add_to(m3)

            folium.LayerControl(collapsed=False).add_to(m3)

            st.subheader("🔥 Mapa de Rendimiento Estimado")
            st.caption("Activá 'Grilla' en el control de capas para ver las celdas individuales")
            st_folium(m3, width=720, height=540, key="mapa_rend")
            # ================================
            # ESTADÍSTICAS
            # ================================
            st.subheader("📊 Resumen del modelo")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🔴 Zona Baja", f"< {p33:.0f} kg/ha")
            col2.metric("🟡 Zona Media", f"{p33:.0f} – {p66:.0f} kg/ha")
            col3.metric("🟢 Zona Alta", f"> {p66:.0f} kg/ha")
            col4.metric("📦 Promedio muestras", f"{np.mean(rend_vals):.0f} kg/ha")

            # Descarga
            st.download_button(
                "📥 Descargar mapa HTML",
                data=m3._repr_html_(),
                file_name="rendimiento_frutales.html",
                mime="text/html"
            )

        else:
            st.warning(f"⚠️ Solo {len(evi_vals)} puntos con índices válidos — necesitás 3 dentro del área con cobertura Sentinel-2")

    else:
        st.info(f"👉 Marcá al menos 3 puntos de muestra dentro del lote ({n_puntos}/3)")
# ==========================================================
# MENÚ: ÍNDICES SATELITALES
# ==========================================================
elif menu == "🛰️ Índices Satelitales":
    import geopandas as gpd
    import streamlit.components.v1 as components
    from datetime import datetime

    st.markdown("""<style>.leaflet-control-attribution { display: none !important; }</style>""", unsafe_allow_html=True)
    st.header("🛰️ Monitor Satelital Dinámico")

    INSTANCE_ID = "95f18ee6-a5c6-4c82-b286-f0641c20410d"

    @st.cache_data
    def cargar_limites():
        gdf_arg = None
        gdf_ury = None
        if os.path.exists("gadm41_AGR_2.gpkg"):
            gdf_arg = gpd.read_file("gadm41_AGR_2.gpkg", engine="pyogrio")
            gdf_arg["PAIS"] = "Argentina"
        if os.path.exists("gadm41_URY.gpkg"):
            gdf_ury = gpd.read_file("gadm41_URY.gpkg", layer="ADM_ADM_2", engine="pyogrio")
            gdf_ury["PAIS"] = "Uruguay"
            gdf_ury = gdf_ury.rename(columns={"NAME_1": "NAME_1", "NAME_2": "NAME_2"})
        if gdf_arg is not None and gdf_ury is not None:
            return gpd.GeoDataFrame(pd.concat([gdf_arg, gdf_ury], ignore_index=True))
        return gdf_arg
    
    gdf_argentina = cargar_limites()

    if gdf_argentina is not None:
        col_prov = "NAME_1"
        col_depto = "NAME_2"
        c0, c1, c2, c3 = st.columns([1, 1, 1, 1])
        with c0:
            pais_sel = st.selectbox("País:", ["Seleccionar...", "Argentina", "Uruguay"])
        with c1:
            if pais_sel == "Argentina":
                gdf_pais = gdf_argentina[gdf_argentina["PAIS"] == "Argentina"]
                label_prov = "Provincia:"
                label_depto = "Departamento:"
                opciones_prov = sorted(gdf_pais[col_prov].unique())
                prov_sel = st.selectbox(label_prov, ["Seleccionar..."] + opciones_prov)
            elif pais_sel == "Uruguay":
                gdf_pais = gdf_argentina[gdf_argentina["PAIS"] == "Uruguay"]
                label_prov = "Departamento:"
                label_depto = "Sección:"
                opciones_prov = sorted(gdf_pais[col_prov].unique())
                prov_sel = st.selectbox(label_prov, ["Seleccionar..."] + opciones_prov)
            else:
                prov_sel = st.selectbox("Provincia:", ["Seleccionar..."], disabled=True)
                gdf_pais = gdf_argentina
        with c2:
            if pais_sel != "Seleccionar..." and prov_sel != "Seleccionar...":
                deptos = sorted(gdf_pais[gdf_pais[col_prov] == prov_sel][col_depto].unique())
                depto_sel = st.selectbox(label_depto, ["Seleccionar..."] + deptos)
            else:
                depto_sel = st.selectbox("Zona:", ["Esperando..."], disabled=True)
        with c3:
            indice_sel = st.selectbox("Capa / Índice:", ["NDVI", "NDWI", "TRUE-COLOR", "NDMI", "EVI"])

        if prov_sel != "Seleccionar..." and depto_sel != "Seleccionar...":
            with st.spinner(f"Calculando {indice_sel}..."):
                gdf_loc = gdf_pais[(gdf_pais[col_prov] == prov_sel) & (gdf_pais[col_depto] == depto_sel)]
                centro = gdf_loc.geometry.centroid.iloc[0]
                m = folium.Map(location=[centro.y, centro.x], zoom_start=13, tiles='OpenStreetMap', attr=' ', height='100%', width='100%')
                capa_wms = {
                    "NDVI": "NDVI",
                    "NDWI": "NDWI",
                    "TRUE-COLOR": "TRUE-COLOR",
                    "NDMI": "NDMI",
                    "EVI": "EVI"
                }    

                folium.WmsTileLayer(url=f"https://services.sentinel-hub.com/ogc/wms/{INSTANCE_ID}", layers=capa_wms[indice_sel], name=f"Sentinel-2 {indice_sel}", fmt="image/png", transparent=True, overlay=True, opacity=1.0, zindex=1000, version="1.1.1", maxcc=100, time="2023-01-01/2026-03-04", attr=' ').add_to(m)
                # Todos los departamentos de la provincia en gris
                gdf_prov = gdf_argentina[gdf_argentina[col_prov] == prov_sel]
                folium.GeoJson(
                    gdf_prov,
                    style_function=lambda x: {
                        'fillColor': '#333333',
                        'color': '#666666',
                        'weight': 1,
                        'fillOpacity': 0.3
                    }
                ).add_to(m)
                
                # Departamento seleccionado resaltado en verde
                folium.GeoJson(
                    gdf_loc,
                    style_function=lambda x: {
                        'fillColor': 'transparent',
                        'color': '#00ffc3',
                        'weight': 3,
                        'fillOpacity': 0
                    }
                ).add_to(m)
                
                m.fit_bounds(gdf_loc.total_bounds.tolist())
                mapa_html = m.get_root().render()
                mapa_html = mapa_html.replace(
                    '</head>',
                    '<style>.leaflet-control-attribution { display: none !important; } .leaflet-control-container .leaflet-top, .leaflet-control-container .leaflet-bottom { display: none !important; }</style></head>'
                )
                components.html(mapa_html, height=1000, width=None)
                st.write("---")

                if indice_sel == "NDVI":
                    st.subheader("🍃 Análisis de Vigor Vegetal (NDVI)")
                    st.markdown("""El **NDVI** mide la salud de la vegetación:\n* 🟩 **Verde Oscuro:** Cultivo muy sano o bosque denso.\n* 🟩 **Verde Claro:** Vegetación en crecimiento.\n* 🟨 **Amarillo/Marrón:** Suelo desnudo o cultivo estresado.\n* 🟥 **Rojo/Blanco:** Zonas sin vegetación o agua.""")
                elif indice_sel == "NDWI":
                    st.subheader("💧 Monitor de Humedad y Agua (NDWI)")
                    st.markdown("""El **NDWI** resalta la presencia de agua:\n* 🟦 **Azul Oscuro:** Cuerpos de agua claros.\n* 🔷 **Celeste:** Suelo muy húmedo o inundado.\n* ⬜ **Blanco:** Suelo seco o zonas urbanas.""")
                elif indice_sel == "TRUE-COLOR":
                    st.subheader("📸 Fotografía Satelital Real (True Color)")
                    st.markdown("""Composición de color natural (RGB):\n* 🌿 **Verdes:** Cultivos activos y montes.\n* 🪵 **Marrones/Grises:** Lotes preparados o rastrojo.\n* ⚫ **Oscuros:** Agua profunda o sombras.\n* ☁️ **Blanco Brillante:** Nubes.""")
                elif indice_sel == "NDMI":
                    st.subheader("💦 Índice de Humedad del Cultivo (NDMI)")
                    st.markdown("""El **NDMI** detecta el contenido de agua en la vegetación:\n* 🔵 **Azul Oscuro:** Alta humedad en canopeo — cultivo bien abastecido.\n* 🟦 **Celeste:** Humedad moderada — monitorear.\n* 🟨 **Amarillo:** Humedad baja — estrés hídrico incipiente.\n* 🟥 **Rojo:** Estrés hídrico severo — intervención urgente.""")
                elif indice_sel == "EVI":
                    st.subheader("🌱 Índice de Vegetación Mejorado (EVI)")
                    st.markdown("""El **EVI** mejora el NDVI en zonas de alta biomasa:\n* 🟩 **Verde Oscuro:** Cultivo muy denso y sano.\n* 🟩 **Verde Claro:** Vegetación activa en crecimiento.\n* 🟨 **Amarillo:** Cultivo con estrés o baja densidad.\n* 🟥 **Rojo/Naranja:** Suelo desnudo o cultivo muy estresado.""")

                fecha_reporte = datetime.now().strftime('%d/%m/%Y')
                texto_reporte = f"📊 INFORME DE MONITOREO SATELITAL\n---------------------------------\n📍 Ubicación: {depto_sel}, {prov_sel}\n📅 Fecha: {fecha_reporte}\n🛰️ Capa: {indice_sel}\n"
                st.download_button(label=f"📥 Descargar Reporte {depto_sel}", data=texto_reporte, file_name=f"Reporte_{depto_sel}_{datetime.now().strftime('%Y%m%d')}.txt", mime="text/plain")

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
    st.markdown("**💻 Desde computadora podés subir una foto:**")
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
                    prompt = """Sos un ingeniero agrónomo experto en cultivos extensivos e intensivos de Argentina y Uruguay.

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
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[imagen_pil, prompt]
                    )
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
