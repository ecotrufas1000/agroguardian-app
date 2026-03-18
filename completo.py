import streamlit as st
from google import genai
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
    streamlit_js_eval(
        js_expressions='localStorage.removeItem("ag_usuario"); localStorage.removeItem("ag_user_id");',
        key="ls_remove_sesion"
    )
    st.session_state.cerrando_sesion = False
    st.stop()  # Detiene acá, el próximo rerun arranca limpio

# ==========================================================
# 5. RESTAURAR SESIÓN DESDE localStorage
#===========================================================
if st.session_state.usuario is None:
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
        st.error(f"❌ Error al iniciar sesión: {e}")
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
                    st.success("✅ Cuenta creada correctamente")
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
    streamlit_js_eval(
        js_expressions='localStorage.removeItem("ag_usuario"); localStorage.removeItem("ag_user_id");',
        key="ls_remove_sesion"
    )
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.rerun()
#==========================================================
# 8. APP PRINCIPAL — solo llega acá si está logueado
# ==========================================================
with st.sidebar:
    st.markdown(f"👤 **{st.session_state.get('usuario', '')}**")
    if st.button("🚪 Cerrar sesión"):
        cerrar_sesion()


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
                "presion": r["main"]["pressure"], "localidad": r.get("name", "Zona Rural")
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
        ["📊 Monitoreo Total", "🌧️ Pluviómetro", "💧 Balance Hídrico", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora", "🛰️ Índices Satelitales", "🔍 Diagnóstico IA"],
        key="menu_principal"
    )

    import streamlit.components.v1 as components_sidebar
    components_sidebar.html("""
        <a href="https://wa.me/5491154074144?text=Hola%20AgroGuardian%2C%20necesito%20soporte%20tecnico" target="_blank" style="text-decoration:none;">
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
elif menu == "🌧️ Pluviómetro":
    st.header("🌧️ Pluviómetro Digital")

    try:
        res = supabase.table("registros_lluvia").select("*").eq("productor_id", st.session_state.user_id).execute()

        if res.data and len(res.data) > 0:
            df = pd.DataFrame(res.data)
            df['fecha'] = pd.to_datetime(df['fecha'], format='mixed', utc=True)
            df['mm'] = pd.to_numeric(df['mm'], errors='coerce').fillna(0)
            from datetime import datetime, timezone
            hoy = datetime.now(timezone.utc)

            # --- MÉTRICAS RÁPIDAS ---
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
            import urllib.parse
            mensaje_url = urllib.parse.quote(mensaje_wa)
            wa_url = f"https://wa.me/?text={mensaje_url}"

            st.markdown(f"""
                <a href="{wa_url}" target="_blank" style="text-decoration: none;">
                    <div style="
                        background-color: #25D366;
                        color: white;
                        padding: 15px;
                        border-radius: 12px;
                        text-align: center;
                        font-weight: bold;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 12px;
                        box-shadow: 0px 6px 15px rgba(0,0,0,0.4);
                    ">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="25px">
                        ENVIAR REPORTE + TABLA DIARIA
                    </div>
                </a>
            """, unsafe_allow_html=True)
            st.write("")
            st.divider()

            # --- GRÁFICOS ---
            estilo_grafico = dict(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#00ffc3"),
                height=350,
                margin=dict(l=10, r=10, t=30, b=20)
            )

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
            fig2 = px.bar(df_anual, x='Mes', y='Prec_mm', template="plotly_dark",
                          text_auto='.1f', title="Distribución de Lluvias por Mes")
            fig2.update_traces(marker_color='#00ffc3', textposition="outside")
            fig2.update_layout(**estilo_grafico)
            st.plotly_chart(fig2, use_container_width=True, config={'staticPlot': True})

            st.divider()

            # --- GENERAR EXCEL (antes de mostrarlo) ---
            import io
            df_excel = df.copy().sort_values('fecha', ascending=False)
            df_excel['fecha'] = df_excel['fecha'].dt.tz_localize(None) if df_excel['fecha'].dt.tz is None else df_excel['fecha'].dt.tz_convert(None)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_excel[['fecha', 'lote', 'mm']].to_excel(writer, index=False, sheet_name='Registros_Lluvia')
                workbook = writer.book
                worksheet = writer.sheets['Registros_Lluvia']
                for i, col in enumerate(['fecha', 'lote', 'mm']):
                    column_len = max(df_excel[col].astype(str).map(len).max(), len(col)) + 2
                    worksheet.set_column(i, i, column_len)
            excel_data = output.getvalue()

            # --- TABLA EDITABLE + BOTONES ---
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

            st.markdown("""
                <style>
                div.stDownloadButton > button {
                    background-color:  #00b4d8 !important;
                    color: white:#000000 !important;
                    border: none !important;
                    border-radius: 8px !important;
                    padding: 10px 20px !important;
                    font-weight: bold !important;
                    width: 100% !important;
                    font-size: 14px !important;
                }
                </style>
            """, unsafe_allow_html=True)

            st.download_button(
                label="📥 DESCARGAR EXCEL",
                data=excel_data,
                file_name=f'Lluvias_AgroGuardian_{hoy.strftime("%Y-%m-%d")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True
            )

            # --- BORRADOR DEDICADO ---
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

            fila_seleccionada = st.selectbox(
                "Seleccioná el registro a eliminar:",
                options=list(opciones.keys()),
                key="selector_borrar"
            )

            if st.button("🗑️ ELIMINAR ESTE REGISTRO", type="primary", use_container_width=True):
                try:
                    id_borrar = opciones[fila_seleccionada]
                    supabase.table("registros_lluvia").delete().eq("id", id_borrar).execute()
                    st.success("✅ Registro eliminado correctamente")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")

            # --- ✅ REGISTRO AUTOMÁTICO SATELITAL ---
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
                        url_meteo = (
                            f"https://api.open-meteo.com/v1/forecast?"
                            f"latitude={lat_auto}&longitude={lon_auto}"
                            f"&daily=precipitation_sum"
                            f"&timezone=America/Argentina/Buenos_Aires"
                            f"&start_date={hoy_fecha}&end_date={hoy_fecha}"
                        )
                        r = requests.get(url_meteo).json()
                        mm_hoy = r['daily']['precipitation_sum'][0] or 0.0
                        supabase.table("registros_lluvia").insert({
                            "fecha": hoy_fecha,
                            "mm": mm_hoy,
                            "lote": "🛰️ Automático (Open-Meteo)",
                            "productor_id": st.session_state.user_id
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
                    url_meteo = (
                        f"https://api.open-meteo.com/v1/forecast?"
                        f"latitude={lat_auto}&longitude={lon_auto}"
                        f"&daily=precipitation_sum"
                        f"&timezone=America/Argentina/Buenos_Aires"
                        f"&start_date={fecha_ini}&end_date={fecha_fin}"
                    )
                    r = requests.get(url_meteo).json()
                    fechas = r['daily']['time']
                    lluvias = r['daily']['precipitation_sum']
                    registros = 0
                    for fecha, mm in zip(fechas, lluvias):
                        if mm and mm > 0:
                            supabase.table("registros_lluvia").insert({
                                "fecha": fecha,
                                "mm": mm,
                                "lote": "🛰️ Automático (Open-Meteo)",
                                "productor_id": st.session_state.user_id
                            }).execute()
                            registros += 1
                    st.success(f"✅ Importados {registros} días con lluvia")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        else:
            st.info("🛰️ No hay registros de lluvia cargados todavía.")

    except Exception as e:
        st.error(f"Error al procesar los datos de lluvia: {e}")

    
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
# MENÚ: RADAR GRANIZO
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
            st.caption(f"Puntaje de riesgo: {puntos}/11 | Temp: {temp}°C | Rocío: {rocio}°C | Viento: {viento} km/h | Humedad: {hum}%")

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
            # FILTRAR POR USUARIO LOGUEADO
            res = supabase.table("bitacora").select("*").eq("productor_id", st.session_state.user_id).order("fecha", desc=True).execute()
            if res.data:
                df_bit = pd.DataFrame(res.data)
                df_bit['fecha'] = pd.to_datetime(df_bit['fecha']).dt.strftime('%d/%m/%Y %H:%M')
                st.dataframe(df_bit[['fecha', 'tarea', 'lote', 'clima_temp', 'clima_viento', 'nota']], use_container_width=True,
                    column_config={
                        "clima_temp": st.column_config.NumberColumn("Temp (°C)", format="%.1f"),
                        "clima_viento": st.column_config.NumberColumn("Viento (km/h)", format="%.1f")
                    })
            else:
                st.info("No hay registros cargados.")
        except Exception as e:
            st.error(f"Error al cargar: {e}")

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
    def cargar_limites_argentina():
        ruta_gpkg = "gadm41_AGR_2.gpkg"
        if os.path.exists(ruta_gpkg):
            return gpd.read_file(ruta_gpkg, engine="pyogrio")
        return None

    gdf_argentina = cargar_limites_argentina()

    if gdf_argentina is not None:
        col_prov = "NAME_1"
        col_depto = "NAME_2"
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            provincias = sorted(gdf_argentina[col_prov].unique())
            prov_sel = st.selectbox("Provincia:", ["Seleccionar..."] + provincias)
        with c2:
            if prov_sel != "Seleccionar...":
                deptos = sorted(gdf_argentina[gdf_argentina[col_prov] == prov_sel][col_depto].unique())
                depto_sel = st.selectbox("Departamento:", ["Seleccionar..."] + deptos)
            else:
                depto_sel = st.selectbox("Departamento:", ["Esperando..."], disabled=True)
        with c3:
            indice_sel = st.selectbox("Capa / Índice:", ["NDVI", "NDWI", "TRUE-COLOR", "NDMI", "EVI"])

        if prov_sel != "Seleccionar..." and depto_sel != "Seleccionar...":
            with st.spinner(f"Calculando {indice_sel}..."):
                gdf_loc = gdf_argentina[(gdf_argentina[col_prov] == prov_sel) & (gdf_argentina[col_depto] == depto_sel)]
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
                    prompt = "Sos un agrónomo experto. Identificá plaga/enfermedad y sugerí tratamiento."
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
        st.rerun()
