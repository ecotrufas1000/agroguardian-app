import streamlit as st
from supabase import create_client
from streamlit_folium import folium_static
import folium
import requests
import json
import os
import math
# Reemplazá tus líneas 9, 10 y 11 en GitHub por estas 3:
url = "https://ieodzygauglvdkendvmj.supabase.co"
key = "sb_publishable_YS3LTJInGQZgxw0cZmTCZw_4rFz1Oaq"
supabase = create_client(url, key)
# Conexión a Supabase
#url = st.secrets["SUPABASE_URL"]
#key = st.secrets["SUPABASE_KEY"]
# = create_client(url, key)

# Conexión a Clima (Cambiamos el nombre para que coincida con tu función)
API_KEY = st.secrets["OPENWEATHER_API_KEY"]

# Coordenadas (Asegurate que estén definidas)
LAT, LON = -38.298, -58.208
# ==========================================================
# 1. CONFIGURACIÓN BASE
# ==========================================================
st.set_page_config(
    page_title="AgroGuardian Pro | Lab Terminal",
    layout="wide",
    page_icon="🛰️"
)

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

# PLUVIÓMETRO (Versión Pro con Supabase)
# -------------------------
elif menu == "🌧️ Pluviómetro":
    st.markdown('<p style="color:#00ffc3; font-size:20px; font-weight:bold; font-family:monospace;">Hydraulic Records // Pluviometer Data</p>', unsafe_allow_html=True)
    
    try:
        import pandas as pd
        import plotly.express as px
        import datetime

        # 1. Recuperar datos
        res = supabase.table("registros_lluvia").select("*").order("fecha", desc=False).execute()
        
        if not res.data:
            st.info("📍 No hay registros de lluvia.")
        else:
            df = pd.DataFrame(res.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['mm'] = pd.to_numeric(df['mm'], errors='coerce')
            df['mes_nombre'] = df['fecha'].dt.strftime('%b %Y')
            df['mes_idx'] = df['fecha'].dt.to_period('M').astype(str)

            # --- MÉTRICAS ---
            hoy = datetime.datetime.now()
            mes_actual_str = hoy.strftime("%Y-%m")
            total_mes = df[df['fecha'].dt.strftime("%Y-%m") == mes_actual_str]['mm'].sum()
            total_año = df[df['fecha'].dt.year == hoy.year]['mm'].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("ESTE MES", f"{total_mes:.1f} mm")
            c2.metric("TOTAL ANUAL", f"{total_año:.1f} mm")
            c3.metric("REGISTROS", f"{len(df)}")

            st.divider()

            # --- GRÁFICO 1: DIARIO (MES EN CURSO) ---
            st.subheader(f"📅 Detalle Diario: {hoy.strftime('%B %Y')}")
            df_mes_actual = df[df['fecha'].dt.strftime("%Y-%m") == mes_actual_str]
            
            if df_mes_actual.empty:
                st.warning("No hay lluvias registradas en el mes actual.")
            else:
                fig_diario = px.bar(
                    df_mes_actual, x='fecha', y='mm',
                    title="Milímetros por día (Mes actual)",
                    labels={'fecha': 'Día', 'mm': 'Milímetros'},
                    text_auto=True, template="plotly_dark"
                )
                fig_diario.update_traces(marker_color='#00ffc3', opacity=0.8)
                st.plotly_chart(fig_diario, use_container_width=True)

            st.divider()

           # --- GRÁFICO 2: MENSUAL (TODO EL AÑO) ---
            st.subheader("📊 Acumulados Mensuales")
            df_mensual = df.groupby('mes_idx')['mm'].sum().reset_index()
            
            fig_mensual = px.bar(
                df_mensual, x='mes_idx', y='mm',
                title="Total acumulado por mes",
                labels={'mes_idx': 'Mes', 'mm': 'Total mm'},
                text_auto='.1f', # Un decimal para que no sea tan largo el número
                template="plotly_dark"
            )
            
            # Ajustes de estética: Color y Ancho de barra
            fig_mensual.update_traces(
                marker_color='#3d5afe', 
                opacity=0.9,
                width=0.4 # <-- Esto controla el ancho individual de la barra (0.1 a 1.0)
            )
            
            fig_mensual.update_layout(
                bargap=0.5, # <-- Esto agrega espacio entre las barras
                xaxis=dict(type='category'), # Asegura que los meses se vean como etiquetas
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig_mensual, use_container_width=True)
            # Tabla oculta por si querés ver los números exactos
            with st.expander("📝 Ver todos los registros (Historial completo)"):
                st.dataframe(df[['fecha', 'lote', 'mm']].sort_values('fecha', ascending=False), use_container_width=True)
            
    except Exception as e:
        st.error(f"Error al procesar gráficos: {e}")

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
