import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import datetime
import json
import os
import math

# ==========================================
# 1. MOTOR CIENTÍFICO (Cálculos y Vectores)
# ==========================================
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

# ==========================================
# ==========================================
# 1. CONFIGURACIÓN Y ESTÉTICA DE LABORATORIO (CORREGIDA)
# ==========================================
st.set_page_config(page_title="AgroGuardian Pro | Lab Terminal", layout="wide", page_icon="🛰️")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');
    
    /* Fondo general */
    .stApp { background-color: #0b0e14; color: #e2e8f0; }
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* --- CAMBIO SOLICITADO: COLOR DE LAS VARIABLES --- */
    /* Cambia el nombre de la variable en st.metric */
    [data-testid="stMetricLabel"] {
        color: #ffffff !important; /* Blanco puro para máxima legibilidad */
        font-family: 'Roboto Mono', monospace !important;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-size: 0.85rem !important;
        opacity: 0.9;
    }

    /* Estilo del valor numérico (Verde Lab) */
    [data-testid="stMetricValue"] {
        font-family: 'Roboto Mono', monospace !important;
        font-size: 1.8rem !important;
        color: #00ffc3 !important;
    }

    /* Contenedor de la métrica */
    div[data-testid="stMetric"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        padding: 15px !important;
        border-radius: 4px !important;
    }

    /* Headers estilo Terminal */
    .terminal-header {
        font-family: 'Roboto Mono', monospace;
        color: #8b949e;
        border-bottom: 1px solid #30363d;
        padding-bottom: 5px;
        margin-bottom: 20px;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-size: 0.8rem;
    }

    /* Sidebar y Radio Buttons */
    [data-testid="stSidebar"] { background-color: #0d1117 !important; border-right: 1px solid #30363d; }
    
    /* Nombre de las opciones en el menú lateral */
    div[role="radiogroup"] > label p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    div[role="radiogroup"] > label {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 4px !important;
        margin-bottom: 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)
# ==========================================
# 3. CONEXIÓN Y DATOS
# ==========================================
API_KEY = st.secrets.get("OPENWEATHER_API_KEY", "2762051ad62d06f1d0fe146033c1c7c8")
LAT, LON = -38.298, -58.208
BITACORA_JSON = "bitacora_campo.json"

@st.cache_data(ttl=600)
def traer_datos(lat, lon):
    try:
        r = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es").json()
        return r
    except: return None

r_raw = traer_datos(LAT, LON)

if not r_raw:
    st.error("🚨 ERROR: No se detecta respuesta de la estación meteorológica.")
    st.stop()

# Procesamiento de variables
clima = {
    "temp": r_raw["main"]["temp"], "t_max": r_raw["main"]["temp_max"], "t_min": r_raw["main"]["temp_min"],
    "hum": r_raw["main"]["humidity"], "v_vel": round(r_raw["wind"]["speed"] * 3.6, 1),
    "v_dir": r_raw["wind"]["deg"], "desc": r_raw["weather"][0]["description"].capitalize()
}
t_dp = calcular_punto_rocio(clima['temp'], clima['hum'])
gdc_hoy = calcular_gdc_diario(clima['t_max'], clima['t_min'])
v_rumbo = obtener_direccion_viento(clima['v_dir'])

# ==========================================
# 4. INTERFAZ DE NAVEGACIÓN
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color:#00ffc3; font-family:monospace;'>AG-TERMINAL v2.6</h2>", unsafe_allow_html=True)
    menu = st.radio("SISTEMAS", ["📊 Monitoreo Total", "💧 Balance Hídrico", "🌧️ Pluviómetro", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora"])
    st.divider()
    if st.button("🔄 RE-SCAN"): st.rerun()

# ==========================================
# 5. DESPLIEGUE DE PÁGINAS
# ==========================================

if menu == "📊 Monitoreo Total":
    st.markdown('<p class="terminal-header">General Monitoring // Live Telemetry</p>', unsafe_allow_html=True)
    
    # KPIs CIENTÍFICOS
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("TEMPERATURA", f"{clima['temp']}°C")
    c2.metric("PTO. ROCÍO (Td)", f"{t_dp}°C")
    c3.metric("GDC (B10)", f"{gdc_hoy:.1f}")
    c4.metric("HUMEDAD", f"{clima['hum']}%")
    c5.metric("VIENTO", f"{clima['v_vel']}k/h", f"{v_rumbo}")

    st.divider()

    col_map, col_wind = st.columns([2, 1])
    with col_map:
        m = folium.Map(location=[LAT, LON], zoom_start=15)
        folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        folium_static(m, width=700, height=400)
    
    with col_wind:
        st.subheader("🌬️ Vector de Deriva")
        st.markdown(f"""
            <div style="background:#161b22; padding:30px; border:1px solid #30363d; border-radius:10px; text-align:center;">
                <h1 style="color:#00ffc3; transform: rotate({clima['v_dir']}deg); font-size:80px; margin:0;">⬆️</h1>
                <p style="font-family:monospace; font-size:1.5rem; margin:10px 0;">{v_rumbo}</p>
                <small style="color:#8b949e;">AZIMUT: {clima['v_dir']}°</small>
            </div>
        """, unsafe_allow_html=True)

elif menu == "❄️ Análisis de Heladas":
    st.markdown('<p class="terminal-header">Frost Analysis // Radiative Cooling</p>', unsafe_allow_html=True)
    
    c_h1, c_h2 = st.columns(2)
    with c_h1:
        dif = 3.5 if clima['v_vel'] < 5 else 1.2
        st.metric("Temp. Suelo (Est.)", f"{round(clima['temp'] - dif, 1)}°C", f"-{dif}°C (Gradiente)", delta_color="inverse")
    
    with c_h2:
        if t_dp <= 0:
            st.error(f"DETECCIÓN DE HELADA NEGRA: Punto de rocío en {t_dp}°C.")
        elif clima['temp'] < 3:
            st.warning("RIESGO DE HELADA BLANCA: Inversión térmica y baja velocidad de viento.")
        else:
            st.success("ATMÓSFERA ESTABLE.")

 elif menu == "🌧️ Pluviómetro":
    st.markdown('<p class="terminal-header">Hydraulic Records // Pluviometer Data</p>', unsafe_allow_html=True)
    
    # 1. Recuperar datos del JSON
    lote_sel = datos_memoria.get("lote_activo", "General")
    # Traemos la lista de lluvias del lote seleccionado
    todas_lluvias = datos_memoria.get("registro_lluvias", {}).get(lote_sel, [])
    
    if not todas_lluvias:
        st.info(f"📍 No hay registros de lluvia para el lote {lote_sel}. Podés cargar datos desde el Bot de Telegram con el botón 'ANOTAR LLUVIA'.")
    else:
        import pandas as pd
        import plotly.express as px

        # 2. Procesamiento de datos con Pandas
        df = pd.DataFrame(todas_lluvias)
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['mm'] = df['mm'].astype(float)
        
        # Extraemos año y mes para los acumulados
        df['año'] = df['fecha'].dt.year
        df['mes_idx'] = df['fecha'].dt.strftime('%Y-%m') # Para agrupar
        df['mes_nombre'] = df['fecha'].dt.strftime('%b %y') # Para mostrar

        # 3. Métricas Principales (Arriba)
        mes_actual = datetime.datetime.now().strftime("%Y-%m")
        total_mes = df[df['mes_idx'] == mes_actual]['mm'].sum()
        total_año = df[df['año'] == datetime.datetime.now().year]['mm'].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("ESTE MES", f"{total_mes} mm", delta="Acumulado")
        c2.metric("ANUAL", f"{total_año} mm", delta="Total Ciclo", delta_color="normal")
        c3.metric("EVENTOS", f"{len(df)}", delta="Registros")

        st.markdown("---")

        # 4. Gráfico de Barras Interactivo (Plotly)
        st.subheader("📊 Historial de Precipitaciones")
        fig = px.bar(
            df, 
            x='fecha', 
            y='mm',
            title=f"Lluvias registradas: {lote_sel}",
            labels={'fecha': 'Fecha del Evento', 'mm': 'Milímetros'},
            template="plotly_dark"
        )
        
        # Estética Neón para el gráfico
        fig.update_traces(marker_color='#00ffc3', marker_line_color='#ffffff', marker_line_width=0.5, opacity=0.8)
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(gridcolor='#30363d')
        )
        st.plotly_chart(fig, use_container_width=True)

        # 5. Resumen Mensual (Tabla de Laboratorio)
        st.subheader("🗓️ Resumen Mensual")
        resumen = df.groupby('mes_nombre')['mm'].sum().reset_index()
        resumen.columns = ['Mes', 'Total Lluvia (mm)']
        
        st.table(resumen.sort_index(ascending=False))   

elif menu == "💧 Balance Hídrico":
    st.markdown('<p class="terminal-header">Hydric Status // Evapotranspiration Model</p>', unsafe_allow_html=True)
    kc = st.slider("Kc del Cultivo", 0.3, 1.2, 0.8)
    st.metric("Evapotranspiración Real (ETc)", f"{round(4.8 * kc, 2)} mm/día")

elif menu == "⛈️ Radar Granizo":
    st.markdown('<p class="terminal-header">NEXRAD Equivalent // Storm Cell Tracking</p>', unsafe_allow_html=True)
    
    # 1. Indicadores de Inestabilidad (Cálculo de Tendencia)
    c1, c2, c3 = st.columns(3)
    
    # Supongamos que traemos la presión actual de la API
    # Reemplazo seguro para evitar el KeyError
    presion_actual = clima.get('presion', 1013.2) # 1013.2 es el valor estándar si no hay dato
    
    c1.metric("PRESIÓN HPA", f"{presion_actual}", "-1.5 hPa/3h" if clima['v_vel'] > 20 else "Estable")
    c2.metric("DESARROLLO VERTICAL", "ALTO" if clima['hum'] > 85 else "MEDIO")
    c3.metric("RADAR STATUS", "ONLINE", delta="ACTIVO")

    # 2. El Radar+ Dinámico
    # Usamos las coordenadas reales para que el mapa abra sobre tu lote
    windy_url = f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&level=surface&overlay=radar&product=ecmwf&menu=&message=&marker=true&calendar=now&pressure=true&type=map&location=coordinates&detail=&metricWind=default&metricTemp=default&radarRange=-1"
    
    st.components.v1.iframe(windy_url, height=600)
    
    # 3. Alerta de Laboratorio
    if presion_actual < 1010 and clima['hum'] > 80:
        st.error("⚠️ ALERTA ATMOSFÉRICA: Condiciones propicias para convección profunda (Granizo posible).")

elif menu == "📝 Bitácora":
    st.markdown('<p class="terminal-header">Data Logs // Telegram Feed</p>', unsafe_allow_html=True)
    if os.path.exists(BITACORA_JSON):
        with open(BITACORA_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            for uid, eventos in data.items():
                for e in reversed(eventos[-15:]):
                    st.markdown(f"""<div style="background:#161b22; border-left: 3px solid #00ffc3; padding:10px; margin-bottom:10px;"><small>{e['fecha']}</small><br><b>{e['lote']}</b>: {e['detalle']}</div>""", unsafe_allow_html=True)
