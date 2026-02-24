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
    page_icon="🛰️"
)

# Inyección de CSS para modo Terminal Negro y Verde
st.markdown("""
    <style>
        /* Fondo principal y Sidebar */
        .stApp {
            background-color: #0d1117 !important;
            color: #00ffc3 !important;
        }
        [data-testid="stSidebar"] {
            background-color: #010409 !important;
            border-right: 1px solid #30363d;
        }

        /* Títulos, textos y etiquetas */
        h1, h2, h3, p, span, label, .stMarkdown {
            color: #00ffc3 !important;
            font-family: 'Courier New', Courier, monospace !important;
        }

        /* Métricas con efecto Neón */
        [data-testid="stMetricValue"] {
            color: #00ffc3 !important;
            font-family: 'Courier New', monospace !important;
            text-shadow: 0px 0px 10px #00ffc3;
        }
        [data-testid="stMetricLabel"] {
            color: #c9d1d9 !important;
        }

        /* Botones estilo Consola */
        .stButton>button {
            background-color: #161b22 !important;
            color: #00ffc3 !important;
            border: 1px solid #00ffc3 !important;
            border-radius: 2px;
            font-family: 'Courier New', monospace;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #00ffc3 !important;
            color: #0d1117 !important;
            box-shadow: 0px 0px 15px #00ffc3;
        }

        /* Tablas y Dataframes */
        .stDataFrame, [data-testid="stTable"] {
            background-color: #0d1117 !important;
        }

        /* Ocultar decoraciones innecesarias de Streamlit */
        header, footer, .stDeployButton {visibility: hidden !important; display: none !important;}
        
       
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
# 4. CARGA DE DATOS Y CLIMA
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
# 5. SIDEBAR (Navegación nativa con flecha)
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
        st.markdown(f"**Condición:** {clima['desc']}")
        st.markdown(f"**Presión:** {clima['presion']} hPa")

elif menu == "❄️ Análisis de Heladas":
    st.subheader("❄️ Detección de Riesgo Térmico")
    dif = 3.5 if clima['v_vel'] < 5 else 1.2
    st.metric("Temp. Suelo (Est.)", f"{round(clima['temp'] - dif, 1)}°C")

    if t_dp <= 0:
        st.error(f"HELADA NEGRA: Punto de rocío {t_dp}°C")
    elif clima['temp'] < 3:
        st.warning("RIESGO DE HELADA BLANCA")
    else:
        st.success("Sin riesgo inmediato")

elif menu == "🌧️ Pluviómetro":
    st.markdown("### 🌧️ Hydraulic Records // Pluviometer Data")
    try:
        import pandas as pd
        import plotly.express as px
        res = supabase.table("registros_lluvia").select("*").order("fecha", desc=False).execute()
        
        if not res.data:
            st.info("📍 No hay registros de lluvia en la base de datos.")
        else:
            df = pd.DataFrame(res.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['mm'] = pd.to_numeric(df['mm'], errors='coerce')
            
            # Gráfico con colores terminal
            fig = px.bar(df, x='fecha', y='mm', title="Distribución de Lluvias", template="plotly_dark")
            fig.update_traces(marker_color='#00ffc3')
            st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(df[['fecha', 'lote', 'mm']].sort_values('fecha', ascending=False), use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")

elif menu == "💧 Balance Hídrico":
    st.subheader("💧 Cálculo de ETc")
    kc = st.slider("Kc del Cultivo", 0.3, 1.2, 0.8)
    st.metric("ETc Estimada", f"{round(4.8 * kc, 2)} mm/día")
    st.caption("ETo base estimada: 4.8 mm")

elif menu == "⛈️ Radar Granizo":
    c1, c2, c3 = st.columns(3)
    c1.metric("PRESIÓN", f"{clima['presion']} hPa")
    c2.metric("HUMEDAD", f"{clima['hum']}%")
    c3.metric("ESTADO", "LIVE")
    windy_url = f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&overlay=radar"
    st.components.v1.iframe(windy_url, height=600)

elif menu == "📝 Bitácora":
    st.subheader("📝 Registros de Campo")
    if os.path.exists(BITACORA_JSON):
        with open(BITACORA_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            for uid, eventos in data.items():
                for e in reversed(eventos[-15:]):
                    st.write(f"**{e['fecha']}** - {e['lote']} → {e['detalle']}")
