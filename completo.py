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
        
        /* FLECHA VERDE NEÓN */
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

# ==========================================================
# 2. CONEXIÓN Y DATOS
# ==========================================================
url = "https://ieodzygauglvdkendvmj.supabase.co"
key = "sb_publishable_YS3LTJInGQZgxw0cZmTCZw_4rFz1Oaq"
supabase = create_client(url, key)
API_KEY = st.secrets["OPENWEATHER_API_KEY"]
LAT, LON = -38.298, -58.208

@st.cache_data(ttl=600)
def traer_datos(lat, lon):
    try:
        return requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es").json()
    except: return None

r_raw = traer_datos(LAT, LON)
clima = {
    "temp": r_raw["main"]["temp"] if r_raw else 0,
    "hum": r_raw["main"]["humidity"] if r_raw else 0,
    "v_vel": round(r_raw["wind"]["speed"] * 3.6, 1) if r_raw else 0,
    "v_dir": r_raw["wind"]["deg"] if r_raw else 0
}

# ==========================================================
# 3. SIDEBAR
# ==========================================================
with st.sidebar:
    st.markdown("## AG-TERMINAL v2.6")
    menu = st.radio(
        "SISTEMAS",
        ["📊 Monitoreo Total", "💧 Balance Hídrico", "🌧️ Pluviómetro", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora"]
    )

# ==========================================================
# 4. PÁGINAS (PLUVIÓMETRO RESTAURADO)
# ==========================================================

if menu == "📊 Monitoreo Total":
    c1, c2, c3 = st.columns(3)
    c1.metric("TEMPERATURA", f"{clima['temp']}°C")
    c2.metric("HUMEDAD", f"{clima['hum']}%")
    c3.metric("VIENTO", f"{clima['v_vel']} km/h")
    st.divider()
    m = folium.Map(location=[LAT, LON], zoom_start=15)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    folium_static(m, width=700, height=400)

elif menu == "🌧️ Pluviómetro":
    st.markdown("### 🌧️ ANALÍTICA DE PRECIPITACIONES")
    try:
        res = supabase.table("registros_lluvia").select("*").order("fecha", desc=False).execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['mm'] = pd.to_numeric(df['mm'])
            
            # --- PROCESAMIENTO PARA GRÁFICOS ---
            # 1. Gráfico Diario (Eventos individuales)
            df_diario = df.copy()
            
            # 2. Gráfico Mensual (Agrupado)
            df_mensual = df.set_index('fecha').resample('M')['mm'].sum().reset_index()
            df_mensual['mes_nombre'] = df_mensual['fecha'].dt.strftime('%b %Y')

            # --- MÉTRICAS ---
            hoy = datetime.datetime.now()
            acum_mes = df[df['fecha'].dt.month == hoy.month]['mm'].sum()
            acum_año = df[df['fecha'].dt.year == hoy.year]['mm'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("MES ACTUAL", f"{acum_mes:.1f} mm")
            c2.metric("ACUM. ANUAL", f"{acum_año:.1f} mm")
            c3.metric("MÁX. EVENTO", f"{df['mm'].max():.1f} mm")

            st.divider()

            # --- GRÁFICO 1: LLUVIA DIARIA (Barras Azules) ---
            st.subheader("📅 Registro de Lluvias Diarias")
            fig_diario = px.bar(
                df_diario, 
                x='fecha', 
                y='mm', 
                title="Milímetros por Evento",
                template="plotly_dark",
                labels={'mm': 'Milímetros', 'fecha': 'Día'}
            )
            fig_diario.update_traces(marker_color='#1f77b4') # Azul clásico
            st.plotly_chart(fig_diario, use_container_width=True)

            # --- GRÁFICO 2: LLUVIA MENSUAL ACUMULADA (Barras Azules) ---
            st.subheader("📊 Acumulado por Mes")
            fig_mensual = px.bar(
                df_mensual, 
                x='mes_nombre', 
                y='mm', 
                title="Suma Mensual de Precipitación",
                template="plotly_dark",
                labels={'mm': 'Total mm', 'mes_nombre': 'Mes'}
            )
            fig_mensual.update_traces(marker_color='#00d4ff') # Azul más brillante para el mensual
            st.plotly_chart(fig_mensual, use_container_width=True)

            # --- TABLA DE DATOS ---
            with st.expander("📝 Listado Detallado de Registros"):
                st.dataframe(df[['fecha', 'lote', 'mm']].sort_values('fecha', ascending=False), use_container_width=True)
                
        else:
            st.info("No hay datos cargados para generar los gráficos.")
    except Exception as e:
        st.error(f"Error al generar analítica: {e}")

elif menu == "💧 Balance Hídrico":
    st.subheader("💧 Balance Hídrico")
    kc = st.slider("Kc del Cultivo", 0.3, 1.2, 0.8)
    st.metric("ETc Estimada", f"{round(4.8 * kc, 2)} mm/día")

elif menu == "⛈️ Radar Granizo":
    st.components.v1.iframe(f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&overlay=radar", height=600)

elif menu == "❄️ Análisis de Heladas":
    st.metric("Riesgo Térmico", f"{clima['temp']}°C")
    if clima['temp'] < 3: st.warning("ALERTA DE HELADA")
    else: st.success("Sin riesgo")

elif menu == "📝 Bitácora":
    st.write("Módulo de bitácora activo.")
