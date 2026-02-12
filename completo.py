import streamlit as st
from supabase import create_client
from streamlit_folium import folium_static
import folium
import requests
import json
import os
import math

# ==========================================================
# 1. CONFIGURACIÓN BASE
# ==========================================================
st.set_page_config(
    page_title="AgroGuardian Pro | Lab Terminal",
    layout="wide",
    page_icon="🛰️"
)

# ==========================================================
# 2. CONEXIONES (SUPABASE + API)
# ==========================================================
try:
    supabase = create_client(
        st.secrets["https://ieodzygauglvdkendvmj.supabase.co"],
        st.secrets["sb_publishable_YS3LTJInGQZgxw0cZmTCZw_4rFz1Oaq"]
    )
except:
    st.error("⚠️ Error: No se encontraron los Secrets de Supabase.")
    st.stop()

API_KEY = st.secrets.get("OPENWEATHER_API_KEY")
LAT, LON = -38.298, -58.208
BITACORA_JSON = "bitacora_campo.json"

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

def cargar_memoria():
    if os.path.exists("memoria_lotes.json"):
        with open("memoria_lotes.json", "r", encoding="utf-8") as f:
            full_data = json.load(f)
            if full_data:
                first_key = list(full_data.keys())[0]
                return full_data.get(first_key, {})
    return {}

@st.cache_data(ttl=600)
def traer_datos(lat, lon):
    try:
        return requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
        ).json()
    except:
        return None

# ==========================================================
# 4. CARGA DE DATOS
# ==========================================================
datos_memoria = cargar_memoria()
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
# 5. SIDEBAR
# ==========================================================
with st.sidebar:
    st.markdown("## AG-TERMINAL v2.6")
    menu = st.radio(
        "SISTEMAS",
        [
            "📊 Monitoreo Total",
            "💧 Balance Hídrico",
            "🌧️ Pluviómetro",
            "⛈️ Radar Granizo",
            "❄️ Análisis de Heladas",
            "📝 Bitácora"
        ]
    )
    if st.button("🔄 RE-SCAN"):
        st.rerun()

# ==========================================================
# 6. PÁGINAS
# ==========================================================

# -------------------------
# MONITOREO
# -------------------------
if menu == "📊 Monitoreo Total":

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("TEMPERATURA", f"{clima['temp']}°C")
    c2.metric("PTO. ROCÍO", f"{t_dp}°C")
    c3.metric("GDC (B10)", f"{gdc_hoy:.1f}")
    c4.metric("HUMEDAD", f"{clima['hum']}%")
    c5.metric("VIENTO", f"{clima['v_vel']} km/h", v_rumbo)

    st.divider()

    col_map, col_wind = st.columns([2,1])

    with col_map:
        m = folium.Map(location=[LAT, LON], zoom_start=15)
        folium.TileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri'
        ).add_to(m)
        folium_static(m, width=700, height=400)

    with col_wind:
        st.metric("Dirección", f"{clima['v_dir']}°", v_rumbo)

# -------------------------
# HELADAS
# -------------------------
elif menu == "❄️ Análisis de Heladas":

    dif = 3.5 if clima['v_vel'] < 5 else 1.2
    st.metric("Temp. Suelo (Est.)", f"{round(clima['temp'] - dif, 1)}°C")

    if t_dp <= 0:
        st.error(f"HELADA NEGRA: Punto de rocío {t_dp}°C")
    elif clima['temp'] < 3:
        st.warning("RIESGO DE HELADA BLANCA")
    else:
        st.success("Sin riesgo inmediato")

# -------------------------
# PLUVIÓMETRO
# -------------------------
elif menu == "🌧️ Pluviómetro":

    try:
        res = supabase.table("registros_lluvia").select("*").execute()
        if res.data:
            import pandas as pd
            st.dataframe(pd.DataFrame(res.data))
        else:
            st.write("Sin registros.")
    except Exception as e:
        st.error(e)

# -------------------------
# BALANCE HÍDRICO
# -------------------------
elif menu == "💧 Balance Hídrico":

    kc = st.slider("Kc del Cultivo", 0.3, 1.2, 0.8)
    st.metric("ETc", f"{round(4.8 * kc, 2)} mm/día")

# -------------------------
# RADAR GRANIZO
# -------------------------
elif menu == "⛈️ Radar Granizo":

    c1, c2, c3 = st.columns(3)
    c1.metric("PRESIÓN", f"{clima['presion']} hPa")
    c2.metric("HUMEDAD", f"{clima['hum']}%")
    c3.metric("ESTADO", "ONLINE")

    windy_url = f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&overlay=radar"
    st.components.v1.iframe(windy_url, height=600)

    if clima['presion'] < 1010 and clima['hum'] > 80:
        st.error("⚠️ Condiciones favorables para granizo")

# -------------------------
# BITÁCORA
# -------------------------
elif menu == "📝 Bitácora":

    if os.path.exists(BITACORA_JSON):
        with open(BITACORA_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            for uid, eventos in data.items():
                for e in reversed(eventos[-15:]):
                    st.write(f"{e['fecha']} - {e['lote']} → {e['detalle']}")
