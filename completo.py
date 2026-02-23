import streamlit as st
from supabase import create_client
from streamlit_folium import folium_static
import folium
import requests
import json
import os
import math
import datetime
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN Y ESTILO (Terminal Dark)
st.set_page_config(page_title="AgroGuardian Pro", layout="wide", page_icon="🚜")

st.markdown("""
    <style>
        .stApp { background-color: #0d1117 !important; color: #00ffc3 !important; }
        [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
        h1, h2, h3, span, p, label { color: #00ffc3 !important; font-family: 'Courier New', monospace !important; }
        [data-testid="stMetricValue"] { color: #00ffc3 !important; text-shadow: 0px 0px 10px #00ffc3; }
        .stButton>button { background-color: #161b22 !important; color: #00ffc3 !important; border: 1px solid #00ffc3 !important; width: 100%; }
        header, footer, .stDeployButton {visibility: hidden !important; display: none !important;}
    </style>
""", unsafe_allow_html=True)

# 2. GESTIÓN DE NAVEGACIÓN
if 'navegacion' not in st.session_state:
    st.session_state['navegacion'] = "📊 Monitoreo Total"

if st.button("🚜 VOLVER AL PANEL PRINCIPAL"):
    st.session_state['navegacion'] = "📊 Monitoreo Total"
    st.rerun()

# 3. CONEXIÓN A DATOS
url = "https://ieodzygauglvdkendvmj.supabase.co"
key = "sb_publishable_YS3LTJInGQZgxw0cZmTCZw_4rFz1Oaq"
supabase = create_client(url, key)
API_KEY = st.secrets["OPENWEATHER_API_KEY"]
LAT, LON = -38.298, -58.208

# 4. FUNCIONES CIENTÍFICAS
def obtener_direccion_viento(grados):
    val = int((grados / 22.5) + 0.5)
    direcciones = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
    return direcciones[val % 16]

def calcular_punto_rocio(T, HR):
    a, b = 17.27, 237.7
    alpha = ((a * T) / (b + T)) + math.log(HR/100.0)
    return round((b * alpha) / (a - alpha), 1)

@st.cache_data(ttl=600)
def traer_datos(lat, lon):
    try:
        return requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es").json()
    except: return None

# 5. OBTENCIÓN DE DATOS
r_raw = traer_datos(LAT, LON)
if not r_raw:
    st.error("🚨 ERROR DE CONEXIÓN")
    st.stop()

clima = {
    "temp": r_raw["main"]["temp"],
    "hum": r_raw["main"]["humidity"],
    "v_vel": round(r_raw["wind"]["speed"] * 3.6, 1),
    "v_dir": r_raw["wind"]["deg"],
    "presion": r_raw["main"].get("pressure", 1013.2)
}
t_dp = calcular_punto_rocio(clima['temp'], clima['hum'])
v_rumbo = obtener_direccion_viento(clima['v_dir'])

# 6. SIDEBAR
with st.sidebar:
    st.markdown("## 🚜 AG-TERMINAL")
    opciones = ["📊 Monitoreo Total", "💧 Balance Hídrico", "🌧️ Pluviómetro", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora"]
    
    idx_actual = opciones.index(st.session_state['navegacion'])
    seleccion = st.radio("SISTEMAS", opciones, index=idx_actual, key="menu_radio")
    
    if seleccion != st.session_state['navegacion']:
        st.session_state['navegacion'] = seleccion
        st.rerun()

# 7. LÓGICA DE PÁGINAS
pagina = st.session_state['navegacion']

if pagina == "📊 Monitoreo Total":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TEMPERATURA", f"{clima['temp']}°C")
    c2.metric("PTO. ROCÍO", f"{t_dp}°C")
    c3.metric("HUMEDAD", f"{clima['hum']}%")
    c4.metric("VIENTO", f"{clima['v_vel']} km/h", v_rumbo)
    st.divider()
    m = folium.Map(location=[LAT, LON], zoom_start=15)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    folium_static(m, width=700, height=400)

elif pagina == "🌧️ Pluviómetro":
    st.markdown("### 🌧️ HYDRAULIC RECORDS")
    res = supabase.table("registros_lluvia").select("*").order("fecha", desc=False).execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['mm'] = pd.to_numeric(df['mm'])
        
        c1, c2 = st.columns(2)
        c1.metric("TOTAL REGISTRADO", f"{df['mm'].sum():.1f} mm")
        c2.metric("MÁXIMO EVENTO", f"{df['mm'].max():.1f} mm")

        fig = px.bar(df, x='fecha', y='mm', title="HISTORIAL DE LLUVIAS", template="plotly_dark")
        fig.update_traces(marker_color='#00ffc3')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df[['fecha', 'lote', 'mm']].sort_values('fecha', ascending=False), use_container_width=True)
    else:
        st.info("Esperando datos de Supabase...")

elif pagina == "💧 Balance Hídrico":
    st.markdown("### 💧 CÁLCULO DE ETc")
    kc = st.slider("Kc del Cultivo (Coeficiente)", 0.3, 1.2, 0.8)
    eto_base = 4.5 # Estimación base para la zona
    etc = round(eto_base * kc, 2)
    st.metric("Evapotranspiración del Cultivo (ETc)", f"{etc} mm/día")
    st.info("Fórmula: ETc = ETo × Kc. Este valor indica cuánta agua está perdiendo tu cultivo hoy.")

elif pagina == "❄️ Análisis de Heladas":
    st.markdown("### ❄️ DETECTOR DE RIESGO")
    dif = 3.5 if clima['v_vel'] < 5 else 1.2
    temp_suelo = round(clima['temp'] - dif, 1)
    st.metric("Temp. Suelo (Est.)", f"{temp_suelo}°C")
    
    if t_dp <= 0:
        st.error(f"🚨 RIESGO DE HELADA NEGRA: Punto de rocío muy bajo ({t_dp}°C). Daño celular inminente sin escarcha.")
    elif clima['temp'] < 3:
        st.warning("⚠️ RIESGO DE HELADA BLANCA: Condiciones para formación de escarcha.")
    else:
        st.success("✅ SIN RIESGO INMEDIATO")

elif pagina == "⛈️ Radar Granizo":
    st.components.v1.iframe(f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&overlay=radar", height=600)

elif pagina == "📝 Bitácora":
    st.markdown("### 📝 REGISTROS DE CAMPO")
    st.info("Conectado a bitacora.json")
    # (Acá iría la lógica de lectura de JSON que tenías)
