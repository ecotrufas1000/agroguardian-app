import streamlit as st
from supabase import create_client
from streamlit_folium import folium_static
import folium
import requests
import json
import os
import math
import datetime

# ==========================================================
# 1. CONFIGURACIÓN BASE Y ESTILO TERMINAL
# ==========================================================
st.set_page_config(
    page_title="AgroGuardian Pro | Lab Terminal",
    layout="wide",
    page_icon="🛰️",
    initial_sidebar_state="expanded"
)

# CSS PROFESIONAL: NEGRO CARBÓN Y VERDE NEÓN
st.markdown("""
    <style>
        .stApp { background-color: #0d1117 !important; color: #00ffc3 !important; }
        [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
        
        /* Tipografía Terminal */
        h1, h2, h3, span, p, label, .stMarkdown {
            color: #00ffc3 !important;
            font-family: 'Courier New', Courier, monospace !important;
        }

        /* Métricas Neón */
        [data-testid="stMetricValue"] {
            color: #00ffc3 !important;
            text-shadow: 0px 0px 10px #00ffc3;
            font-family: 'Courier New', monospace !important;
        }

        /* Botones de Comando */
        .stButton>button {
            background-color: #161b22 !important;
            color: #00ffc3 !important;
            border: 1px solid #00ffc3 !important;
            border-radius: 2px;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #00ffc3 !important;
            color: #0d1117 !important;
            box-shadow: 0px 0px 15px #00ffc3;
        }

        /* Ocultar elementos de Streamlit */
        header, footer, .stDeployButton {visibility: hidden !important; display: none !important;}
        
        /* Tablas y Dataframes */
        .stDataFrame, .stTable { background-color: #0d1117 !important; color: #00ffc3 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================================
# 2. LÓGICA DE NAVEGACIÓN (Rescate para Celular)
# ==========================================================
if "menu_principal" not in st.session_state:
    st.session_state["menu_principal"] = "📊 Monitoreo Total"

if st.button("🚜 VOLVER AL PANEL PRINCIPAL"):
    st.session_state["menu_principal"] = "📊 Monitoreo Total"
    st.rerun()

# ==========================================================
# 3. CONEXIÓN A DATOS
# ==========================================================
url = "https://ieodzygauglvdkendvmj.supabase.co"
key = "sb_publishable_YS3LTJInGQZgxw0cZmTCZw_4rFz1Oaq"
supabase = create_client(url, key)
API_KEY = st.secrets["OPENWEATHER_API_KEY"]
LAT, LON = -38.298, -58.208
BITACORA_JSON = "bitacora.json"

# ==========================================================
# 4. FUNCIONES CIENTÍFICAS
# ==========================================================
def obtener_direccion_viento(grados):
    val = int((grados / 22.5) + 0.5)
    direcciones = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
    return direcciones[val % 16]

def calcular_punto_rocio(T, HR):
    a, b = 17.27, 237.7
    alpha = ((a * T) / (b + T)) + math.log(HR/100.0)
    return round((b * alpha) / (a - alpha), 1)

def calcular_gdc_diario(t_max, t_min, t_base=10):
    return max(0, ((max(t_max, t_base) + max(t_min, t_base)) / 2) - t_base)

@st.cache_data(ttl=600)
def traer_datos(lat, lon):
    try:
        return requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es").json()
    except: return None

# ==========================================================
# 5. PROCESAMIENTO
# ==========================================================
r_raw = traer_datos(LAT, LON)
if not r_raw:
    st.error("🚨 ERROR: No se detecta respuesta meteorológica.")
    st.stop()

clima = {
    "temp": r_raw["main"]["temp"],
    "t_max": r_raw["main"]["temp_max"],
    "t_min": r_raw["main"]["temp_min"],
    "hum": r_raw["main"]["humidity"],
    "v_vel": round(r_raw["wind"]["speed"] * 3.6, 1),
    "v_dir": r_raw["wind"]["deg"],
    "desc": r_raw["weather"][0]["description"].capitalize(),
    "presion": r_raw["main"].get("pressure", 1013.2)
}

t_dp = calcular_punto_rocio(clima['temp'], clima['hum'])
gdc_hoy = calcular_gdc_diario(clima['t_max'], clima['t_min'])
v_rumbo = obtener_direccion_viento(clima['v_dir'])

# ==========================================================
# 6. SIDEBAR Y MENÚ
# ==========================================================
with st.sidebar:
    st.markdown("## 🚜 AG-TERMINAL")
    menu = st.radio(
        "SISTEMAS_MENU",
        ["📊 Monitoreo Total", "💧 Balance Hídrico", "🌧️ Pluviómetro", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora"],
        key="menu_principal"
    )
    
    st.markdown("---")
    # Indicador de Sistema
    col1, col2 = st.columns([1, 4])
    col1.markdown("<div style='height:12px;width:12px;background-color:#00ffc3;border-radius:50%;margin-top:5px;box-shadow:0 0 10px #00ffc3;'></div>", unsafe_allow_html=True)
    col2.markdown("<span style='color:#00ffc3;font-weight:bold;'>SYS_ONLINE</span>", unsafe_allow_html=True)
    st.caption(f"SYNC: {datetime.datetime.now().strftime('%H:%M:%S')}")

# ==========================================================
# 7. LÓGICA DE PÁGINAS
# ==========================================================

if menu == "📊 Monitoreo Total":
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("TEMPERATURA", f"{clima['temp']}°C")
    c2.metric("PTO. ROCÍO", f"{t_dp}°C")
    c3.metric("GDC (B10)", f"{gdc_hoy:.1f}")
    c4.metric("HUMEDAD", f"{clima['hum']}%")
    c5.metric("VIENTO", f"{clima['v_vel']} km/h", v_rumbo)
    st.divider()
    
    col_map, col_info = st.columns([2,1])
    with col_map:
        m = folium.Map(location=[LAT, LON], zoom_start=15)
        folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        folium_static(m, width=700, height=400)
    with col_info:
        st.markdown(f"### 📍 Ubicación\nLat: `{LAT}`\nLon: `{LON}`")
        st.markdown(f"**Condición:** {clima['desc']}")

elif menu == "🌧️ Pluviómetro":
    st.markdown("### 🌧️ HYDRAULIC RECORDS")
    try:
        import pandas as pd
        import plotly.express as px
        res = supabase.table("registros_lluvia").select("*").order("fecha", desc=False).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df['mm'] = pd.to_numeric(df['mm'])
            fig = px.bar(df, x='fecha', y='mm', template="plotly_dark", title="REGISTRO HISTÓRICO")
            fig.update_traces(marker_color='#00ffc3')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df[['fecha', 'lote', 'mm']].tail(10), use_container_width=True)
        else:
            st.info("No hay registros en Supabase.")
    except Exception as e:
        st.error(f"Error de base de datos: {e}")

elif menu == "⛈️ Radar Granizo":
    st.markdown("### ⛈️ RADAR DE PRECIPITACIÓN")
    windy_url = f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&overlay=radar"
    st.components.v1.iframe(windy_url, height=600)

elif menu == "❄️ Análisis de Heladas":
    st.markdown("### ❄️ DETECTOR DE RIESGO")
    dif = 3.5 if clima['v_vel'] < 5 else 1.2
    temp_suelo = round(clima['temp'] - dif, 1)
    st.metric("Temp. Suelo (Est.)", f"{temp_suelo}°C")
    if t_dp <= 0: st.error(f"🚨 RIESGO DE HELADA NEGRA: {t_dp}°C")
    elif clima['temp'] < 3: st.warning("⚠️ ALERTA DE HELADA BLANCA")
    else: st.success("✅ SIN RIESGO INMEDIATO")

elif menu == "💧 Balance Hídrico":
    st.markdown("### 💧 CÁLCULO DE ETc")
    kc = st.slider("Kc del Cultivo", 0.3, 1.2, 0.8)
    st.metric("Evapotranspiración", f"{round(4.8 * kc, 2)} mm/día")

elif menu == "📝 Bitácora":
    st.markdown("### 📝 REGISTROS DE CAMPO")
    if os.path.exists(BITACORA_JSON):
        with open(BITACORA_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            for uid, eventos in data.items():
                for e in reversed(eventos[-15:]):
                    st.write(f"📅 {e['fecha']} | 🚜 {e['lote']} → {e['detalle']}")
    else:
        st.info("Sin registros locales en la bitácora.")
