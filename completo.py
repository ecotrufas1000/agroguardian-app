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
        import datetime
        import pandas as pd
        import plotly.express as px

        # 1. Recuperar datos
        res = supabase.table("registros_lluvia").select("*").order("fecha", desc=False).execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['mm'] = pd.to_numeric(df['mm'])
            hoy = datetime.datetime.now()

            # --- CÁLCULOS ---
            df_año_actual = df[df['fecha'].dt.year == hoy.year].copy()
            mensual_sum = df_año_actual.groupby(df_año_actual['fecha'].dt.month)['mm'].sum().reindex(range(1, 13), fill_value=0)
            
            acum_mes = mensual_sum[hoy.month]
            acum_año = mensual_sum.sum()

            # --- PROCESAMIENTO GRÁFICO 1: DIARIO (1 al 31) ---
            df_mes_actual = df[(df['fecha'].dt.month == hoy.month) & (df['fecha'].dt.year == hoy.year)].copy()
            df_mes_actual['dia'] = df_mes_actual['fecha'].dt.day
            df_dia_fijo = df_mes_actual.groupby('dia')['mm'].sum().reindex(range(1, 32), fill_value=0).reset_index()

            # --- PROCESAMIENTO GRÁFICO 2: ANUAL (E, F, M...) ---
            meses_letras = ['E', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
            df_anual_fijo = pd.DataFrame({'Mes': meses_letras, 'mm': mensual_sum.values})

            # --- MÉTRICAS DE CABECERA ---
            c1, c2, c3 = st.columns(3)
            c1.metric("ESTE MES", f"{acum_mes:.1f} mm")
            c2.metric("ANUAL", f"{acum_año:.1f} mm")
            c3.metric("MÁX. DÍA", f"{df_mes_actual['mm'].max() if not df_mes_actual.empty else 0:.1f} mm")

            st.divider()

            # --- GRÁFICO 1: DIARIO ---
            st.subheader(f"📅 Registro Diario: {hoy.strftime('%B %Y')}")
            fig1 = px.bar(df_dia_fijo, x='dia', y='mm', template="plotly_dark")
            fig1.update_traces(marker_color='#1f77b4') 
            fig1.update_layout(
                xaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, 31.5], fixedrange=True, tickangle=0, tickfont=dict(size=9), title=None),
                yaxis=dict(fixedrange=True, title=None, tickfont=dict(size=10)),
                height=350,
                dragmode=False,
                bargap=0.1,
                margin=dict(l=10, r=10, t=10, b=20)
            )
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

            # --- GRÁFICO 2: ANUAL ---
            st.subheader(f"📊 Acumulado Mensual {hoy.year}")
            fig2 = px.bar(df_anual_fijo, x='Mes', y='mm', template="plotly_dark")
            fig2.update_traces(marker_color='#1f77b4')
            fig2.update_layout(
                xaxis=dict(fixedrange=True, categoryorder='array', categoryarray=meses_letras, tickangle=0, tickfont=dict(size=10), title=None),
                yaxis=dict(fixedrange=True, title=None, tickfont=dict(size=10)),
                height=350,
                dragmode=False,
                bargap=0.2,
                margin=dict(l=10, r=10, t=10, b=20)
            )
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

            st.divider()
            with st.expander("📂 ACCEDER A REGISTROS (PLANILLA)"):
                st.dataframe(df[['fecha', 'lote', 'mm']].sort_values('fecha', ascending=False), use_container_width=True)

        else:
            st.info("🛰️ Esperando sincronización de datos o sin registros...")
            
    except Exception as e:
        st.error(f"Error en el sistema de analítica: {e}")
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
