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
# 1. CONFIGURACIÓN BASE Y ESTILO TERMINAL (LIMPIO)
# ==========================================================
st.set_page_config(
    page_title="AgroGuardian Pro | Lab Terminal",
    layout="wide",
    page_icon="🛰️"
)

# CSS que respeta iconos pero mantiene el modo negro/verde
st.markdown("""
    <style>
        /* Fondo Principal */
        .stApp {
            background-color: #0d1117 !important;
            color: #00ffc3 !important;
        }

        /* Barra Lateral */
        [data-testid="stSidebar"] {
            background-color: #010409 !important;
            border-right: 1px solid #30363d;
        }

        /* Color de los Iconos (Flecha) */
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0) !important;
        }
        
        /* Aseguramos que la flecha sea verde neón */
        button[kind="header"] {
            color: #00ffc3 !important;
        }

        /* Textos y Títulos */
        h1, h2, h3, p, label, .stMarkdown {
            color: #00ffc3 !important;
            font-family: 'Courier New', monospace !important;
        }

        /* Métricas Neón */
        [data-testid="stMetricValue"] {
            color: #00ffc3 !important;
            text-shadow: 0px 0px 10px #00ffc3;
        }

        /* Estilo de Tablas y Dataframes */
        .stDataFrame, [data-testid="stTable"] {
            background-color: #0d1117 !important;
        }

        /* Eliminar pie de página de Streamlit */
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================================
# 2. CONEXIÓN A DATOS
# ==========================================================
url = "https://ieodzygauglvdkendvmj.supabase.co"
key = "sb_publishable_YS3LTJInGQZgxw0cZmTCZw_4rFz1Oaq"
supabase = create_client(url, key)
API_KEY = st.secrets["OPENWEATHER_API_KEY"]
LAT, LON = -38.298, -58.208
BITACORA_JSON = "bitacora.json"

# ==========================================================
# 3. FUNCIONES CIENTÍFICAS
# ==========================================================
def obtener_direccion_viento(grados):
    val = int((grados / 22.5) + 0.5)
    direcciones = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                   "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
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
        return requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
        ).json()
    except: return None

# ==========================================================
# 4. CARGA DE DATOS
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
# 5. SIDEBAR (Navegación nativa)
# ==========================================================
with st.sidebar:
    st.markdown("## AG-TERMINAL v2.6")
    menu = st.radio(
        "SISTEMAS",
        ["📊 Monitoreo Total", "💧 Balance Hídrico", "🌧️ Pluviómetro", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora"]
    )
    if st.button("🔄 RE-SCAN"):
        st.rerun()

# ==========================================================
# 6. PÁGINAS
# ==========================================================

if menu == "📊 Monitoreo Total":
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("TEMPERATURA", f"{clima['temp']}°C")
    c2.metric("PTO. ROCÍO", f"{t_dp}°C")
    c3.metric("GDC (B10)", f"{gdc_hoy:.1f}")
    c4.metric("HUMEDAD", f"{clima['hum']}%")
    c5.metric("VIENTO", f"{clima['v_vel']} km/h", v_rumbo)
    st.divider()
    m = folium.Map(location=[LAT, LON], zoom_start=15)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    folium_static(m, width=700, height=400)

elif menu == "🌧️ Pluviómetro":
    st.markdown("### 🌧️ Hydraulic Records")
    try:
        import pandas as pd
        import plotly.express as px
        res = supabase.table("registros_lluvia").select("*").order("fecha", desc=False).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['mm'] = pd.to_numeric(df['mm'])
            fig = px.bar(df, x='fecha', y='mm', template="plotly_dark")
            fig.update_traces(marker_color='#00ffc3')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df[['fecha', 'lote', 'mm']].sort_values('fecha', ascending=False), use_container_width=True)
    except: st.info("Sincronizando con base de datos...")

elif menu == "💧 Balance Hídrico":
    st.subheader("💧 Balance Hídrico")
    kc = st.slider("Kc del Cultivo", 0.3, 1.2, 0.8)
    st.metric("ETc Estimada", f"{round(4.8 * kc, 2)} mm/día")

elif menu == "⛈️ Radar Granizo":
    st.components.v1.iframe(f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&overlay=radar", height=600)

elif menu == "❄️ Análisis de Heladas":
    dif = 3.5 if clima['v_vel'] < 5 else 1.2
    st.metric("Temp. Suelo (Est.)", f"{round(clima['temp'] - dif, 1)}°C")
    if t_dp <= 0: st.error(f"HELADA NEGRA: {t_dp}°C")
    elif clima['temp'] < 3: st.warning("RIESGO DE HELADA BLANCA")
    else: st.success("Sin riesgo inmediato")

elif menu == "📝 Bitácora":
    st.write("Registros cargados desde Supabase/JSON")
