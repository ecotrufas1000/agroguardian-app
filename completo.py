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

# ==========================================================
# 1. CONFIGURACIÓN BASE Y ESTILO TERMINAL
# ==========================================================
st.set_page_config(
    page_title="AgroGuardian Pro | Lab Terminal",
    layout="wide",
    page_icon="🛰️"
)

st.markdown("""
    <style>
        .stApp { background-color: #0d1117 !important; color: #00ffc3 !important; }
        [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
        
        header [data-testid="stHeaderActionElements"] button, 
        [data-testid="stSidebarCollapseIcon"],
        .st-emotion-cache-6qob1r { 
            color: #00ffc3 !important; 
            fill: #00ffc3 !important;
        }

        h1, h2, h3, p, label, .stMarkdown {
            color: #00ffc3 !important;
            font-family: 'Courier New', monospace !important;
        }

        [data-testid="stMetricValue"] {
            color: #00ffc3 !important;
            text-shadow: 0px 0px 10px #00ffc3;
        }
        
        .stDataFrame, [data-testid="stTable"] { background-color: #0d1117 !important; }
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE SUPABASE (Asegúrate de tener tus credenciales) ---
# url: str = st.secrets["SUPABASE_URL"]
# key: str = st.secrets["SUPABASE_KEY"]
# supabase = create_client(url, key)
# ==========================================================
# 1.5 CONEXIÓN A BASE DE DATOS (CRUCIAL PARA EL GPS)
# ==========================================================
# Reemplazá con tus datos de Supabase o usá st.secrets
if 'supabase' not in locals():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        supabase = create_client(url, key)
    except Exception as e:
        st.error("❌ Error de configuración: Faltan credenciales de Supabase en Secrets.")
# ==========================================================
# 2. MOTOR DE UBICACIÓN Y CLIMA CIENTÍFICO (AUTÓNOMO)
# ==========================================================
from streamlit_js_eval import get_geolocation

def obtener_clima_completo(lat, lon):
    if not lat or not lon: return None
    try:
        API_KEY = st.secrets["OPENWEATHER_API_KEY"]
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
        r = requests.get(url).json()
        
        if r.get("main"):
            t = r["main"]["temp"]
            h = r["main"]["humidity"]
            a, b = 17.27, 237.7
            alpha = ((a * t) / (b + t)) + math.log(h/100.0)
            punto_rocio = (b * alpha) / (a - alpha)
            
            return {
                "temp": t,
                "hum": h,
                "v_vel": round(r["wind"]["speed"] * 3.6, 1),
                "v_dir": r["wind"].get("deg", 0),
                "rocio": round(punto_rocio, 1),
                "presion": r["main"]["pressure"],
                "localidad": r.get("name", "Zona Rural")
            }
    except Exception as e:
        st.error(f"Error de conexión meteorológica: {e}")
    return None

if 'lat' not in st.session_state:
    try:
        res = supabase.table("configuracion").select("latitud", "longitud").order("created_at", desc=True).limit(1).execute()
        if res.data:
            st.session_state.lat = float(res.data[0]['latitud'])
            st.session_state.lon = float(res.data[0]['longitud'])
    except:
        st.session_state.lat = None

# --- SIDEBAR Y NAVEGACIÓN ---
with st.sidebar:
    st.markdown("### 🛰️ SENSORES DEL LOTE")
    gps_data = get_geolocation()
    
    if st.button("📍 VINCULAR GPS DEL MÓVIL"):
        if gps_data:
            lat_gps = gps_data['coords']['latitude']
            lon_gps = gps_data['coords']['longitude']
            supabase.table("configuracion").insert({"latitud": lat_gps, "longitud": lon_gps}).execute()
            st.session_state.lat = lat_gps
            st.session_state.lon = lon_gps
            st.success("✅ Ubicación actualizada")
            st.rerun()
        else:
            st.warning("⚠️ Activá el GPS y permití el acceso.")

    st.divider()
    menu = st.radio("MENÚ DE CONTROL", 
                   ["📊 Monitoreo Total", "🌧️ Pluviómetro", "💧 Balance Hídrico", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora"])

LAT = st.session_state.get('lat')
LON = st.session_state.get('lon')
clima = obtener_clima_completo(LAT, LON)

if clima:
    st.session_state.clima_data = clima

# ==========================================================
# 4. PÁGINAS (ESTRUCTURA INTEGRADA)
# ==========================================================

if menu == "📊 Monitoreo Total":
    st.header("📊 Tablero de Control Integral")
    
    if clima:
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Temperatura", f"{clima['temp']} °C")
        with col2: st.metric("Humedad Rel.", f"{clima['hum']} %")
        with col3: st.metric("Pto. de Rocío", f"{clima['rocio']} °C")
        with col4: st.metric("Viento", f"{clima['v_vel']} km/h")

        st.divider()
        c_a1, c_a2 = st.columns(2)
        with c_a1:
            delta_t = round(clima['temp'] - clima['rocio'], 1)
            st.markdown(f"**Delta T (Pulverización):** `{delta_t}`")
            if 2 <= delta_t <= 8: st.success("✅ CONDICIONES ÓPTIMAS")
            else: st.warning("⚠️ PRECAUCIÓN: Delta T fuera de rango")
        with c_a2:
            st.markdown(f"**Dirección:** `{clima['v_dir']}°` — " + 
                       ("Norte ⬆️" if 315 <= clima['v_dir'] or clima['v_dir'] <= 45 else "Sur ⬇️" if 135 <= clima['v_dir'] <= 225 else "Lateral ➡️"))
    else:
        st.info("📍 Vinculá el GPS para activar el monitoreo en tiempo real.")

elif menu == "🌧️ Pluviómetro":
    st.header("🌧️ Pluviómetro Digital")
    try:
        res = supabase.table("registros_lluvia").select("*").execute()
        if res.data and len(res.data) > 0:
            df = pd.DataFrame(res.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['mm'] = pd.to_numeric(df['mm'], errors='coerce').fillna(0)
            hoy = datetime.datetime.now(datetime.timezone.utc)

            df_mes = df[(df['fecha'].dt.month == hoy.month) & (df['fecha'].dt.year == hoy.year)].copy()
            df_año = df[df['fecha'].dt.year == hoy.year].copy()
            df_7d = df[df['fecha'] >= (hoy - datetime.timedelta(days=7))].copy()

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💧 Este Mes", f"{df_mes['mm'].sum():.1f} mm")
            c2.metric("📅 Últimos 7 días", f"{df_7d['mm'].sum():.1f} mm")
            c3.metric("📆 Acum. Anual", f"{df_año['mm'].sum():.1f} mm")
            c4.metric("⚡ Máx. en un día", f"{df_mes['mm'].max() if not df_mes.empty else 0:.1f} mm")

            st.divider()
            estilo_grafico = dict(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#00ffc3"), height=350)
            
            st.subheader(f"📅 Registro Diario — {hoy.strftime('%B %Y')}")
            df_mes['dia'] = df_mes['fecha'].dt.day
            df_dia = df_mes.groupby('dia')['mm'].sum().reindex(range(1, 32), fill_value=0).reset_index()
            fig1 = px.bar(df_dia, x='dia', y='mm', template="plotly_dark")
            fig1.update_traces(marker_color='#1f77b4')
            fig1.update_layout(**estilo_grafico)
            st.plotly_chart(fig1, use_container_width=True)

            # (Resto de tus gráficos de lluvia...)
        else:
            st.info("🛰️ No hay registros de lluvia cargados todavía.")
    except Exception as e:
        st.error(f"Error en Pluviómetro: {e}")

elif menu == "💧 Balance Hídrico":
    st.markdown("### 💧 CÁLCULO DE PRECISIÓN (Blaney-Criddle)")
    try:
        if 'clima_data' in st.session_state:
            temp_media = st.session_state.clima_data['temp']
            lat = LAT if LAT else -38.29
        else:
            temp_media, lat = 25.0, -38.29
        
        doy = datetime.datetime.now().timetuple().tm_yday
        delta = 0.409 * math.sin((2 * math.pi * doy / 365) - 1.39)
        lat_rad = math.radians(lat)
        arg = -math.tan(lat_rad) * math.tan(delta)
        ws = math.acos(max(-1, min(1, arg)))
        N = (24 / math.pi) * ws
        p_diario = (N / 4380) * 100
        eto_diaria = p_diario * (0.46 * temp_media + 8)

        st.success(f"📍 GPS: {lat:.4f} | Factor Luz: {p_diario:.4f}")
        kc = st.slider("Kc del Cultivo", 0.3, 1.2, 0.8)
        etc = eto_diaria * kc

        c1, gap, c2 = st.columns([1, 0.1, 1])
        c1.metric("Demanda (ETo)", f"{eto_diaria:.2f} mm/día")
        c2.metric("Consumo (ETc)", f"{etc:.2f} mm/día", delta=f"Kc: {kc}")
        st.progress(min(etc / 10.0, 1.0))
    except Exception as e:
        st.error(f"Error en cálculo: {e}")

elif menu == "⛈️ Radar Granizo":
    if LAT and LON:
        st.components.v1.iframe(f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&overlay=radar", height=600)
    else: st.warning("Requiere GPS")

elif menu == "❄️ Análisis de Heladas":
    if clima:
        st.metric("Riesgo Térmico", f"{clima['temp']}°C")
        if clima['temp'] < 3: st.warning("ALERTA DE HELADA")
        else: st.success("Sin riesgo")

elif menu == "📝 Bitácora":
    st.write("Módulo de bitácora activo.")

# --- FOOTER ---
st.sidebar.divider()
ahora_arg = datetime.datetime.now() - datetime.timedelta(hours=3)
st.sidebar.markdown(f"<div style='text-align:center; color:#00ffc3; font-family:monospace;'>🛰️ ONLINE (GMT-3)<br>{ahora_arg.strftime('%d/%m/%Y %H:%M')}</div>", unsafe_allow_html=True)
