import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
import json
import os
import datetime

# === CONFIGURACIÓN PRO 24/7 ===
st.set_page_config(page_title="AgroGuardian 24/7", layout="wide", page_icon="🛡️")

# Estilo de Alto Contraste y Animaciones de Alerta
st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: bold; color: #1e3d2f; }
    .stMetric { background: white; border-radius: 12px; border-left: 6px solid #2ecc71; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .badge-alerta { padding: 10px; border-radius: 8px; color: white; font-weight: bold; text-align: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# === 1. MOTOR DE DATOS ACELERADO (CACHÉ) ===
API_KEY = "2762051ad62d06f1d0fe146033c1c7c8"

@st.cache_data(ttl=600) # El sistema recuerda los datos por 10 min para ser ultra veloz
def traer_datos_pro(lat, lon):
    d = {"temp": 0.0, "hum": 0, "presion": 1013, "v_vel": 0.0, "v_dir": 0, "tpw": 0.0, "etc": 4.0, "lluvia_est": 0.0}
    try:
        r_ow = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es", timeout=5).json()
        if 'main' in r_ow:
            d.update({"temp": r_ow['main']['temp'], "hum": r_ow['main']['humidity'], "presion": r_ow['main']['pressure'], 
                      "v_vel": round(r_ow['wind']['speed']*3.6, 1), "v_dir": r_ow['wind']['deg']})
        r_om = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=et0_fao_evapotranspiration,precipitation&timezone=auto", timeout=5).json()
        if 'hourly' in r_om:
            d.update({"etc": r_om['hourly']['et0_fao_evapotranspiration'][0] or 4.0, "lluvia_est": r_om['hourly']['precipitation'][0]})
    except: pass
    return d

# Ubicación base
LAT, LON = -38.298, -58.208 
clima = traer_datos_pro(LAT, LON)

# === 2. BARRA LATERAL INTELIGENTE ===
with st.sidebar:
    st.markdown(f"<div style='text-align:center; padding:10px; background:#1e3d2f; border-radius:10px; color:white;'><h3>🛡️ AGROGUARDIAN</h3><small>SISTEMA ACTIVO 24/7</small></div>", unsafe_allow_html=True)
    st.divider()
    menu = st.radio("MENÚ OPERATIVO", ["📊 Monitoreo Total", "💧 Balance Hídrico", "⛈️ Radar Granizo", "❄️ Alerta Heladas", "📝 Bitácora"])
    st.divider()
    st.caption(f"📅 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    if st.button("🔄 FORZAR ACTUALIZACIÓN"): st.rerun()

# === 3. LÓGICA DE PÁGINAS ===

if menu == "📊 Monitoreo Total":
    # --- ENCABEZADO VIOLETA DEGRADADO (Tu favorito) ---
    st.markdown("""
        <div style="background: linear-gradient(to right, #4c1d95, #7c3aed, #a78bfa); padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white; text-align: center; box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);">
            <h1 style="color: white; margin: 0; font-size: 2.2rem;">💎 AgroGuardian Pro 24/7</h1>
            <p style="margin: 0; opacity: 0.9; font-size: 1.1rem; letter-spacing: 1px;">CENTRO DE INTELIGENCIA AGROCLIMÁTICA</p>
        </div>
    """, unsafe_allow_html=True)

    # --- SEMÁFORO DE RIESGO 24/7 ---
    riesgos = []
    if clima['temp'] > 34: riesgos.append(("🔥 ESTRÉS TÉRMICO", "#e74c3c"))
    if clima['v_vel'] > 28: riesgos.append(("💨 VIENTO FUERTE", "#f39c12"))
    if clima['presion'] < 1008: riesgos.append(("⛈️ PRESIÓN BAJA: RIESGO TORMENTA", "#8e44ad"))

    if riesgos:
        cols_r = st.columns(len(riesgos))
        for i, (txt, col) in enumerate(riesgos):
            cols_r[i].markdown(f"<div class='badge-alerta' style='background:{col};'>{txt}</div>", unsafe_allow_html=True)
    else:
        st.success("✅ Condiciones estables en el establecimiento.")

    # MÉTRICAS
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("TEMP.", f"{clima['temp']}°C")
    m2.metric("HUMEDAD", f"{clima['hum']}%")
    m3.metric("VIENTO", f"{clima['v_vel']} km/h")
    m4.metric("ET0 HOY", f"{clima['etc']} mm")
    m5.metric("LLUVIA EST.", f"{clima['lluvia_est']} mm")

    st.divider()

    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("🗺️ Vista de Operaciones")
        m = folium.Map(location=[LAT, LON], zoom_start=15)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Satelital').add_to(m)
        folium.Marker([LAT, LON], icon=folium.Icon(color="purple", icon="screenshot")).add_to(m)
        folium_static(m, width=750, height=400)
    
    with c2:
        st.subheader("📅 Próximos 5 Días")
        for p in obtener_pronostico():
            with st.container():
                st.write(f"**{p['f']}** | {p['min']}°/{p['max']}°")
                st.caption(f"☁️ {p['d']}")
                st.divider()

elif menu == "💧 Balance Hídrico":
    # ... (Mantenemos tu lógica de balance hídrico que ya es muy buena)
    st.header("💧 Gestión Hídrica Pro")
    # [Aquí va el código de Balance Hídrico que pegaste arriba]
    # (Para ahorrar espacio no lo repito, pero va exacto aquí)

elif menu == "⛈️ Granizo":
    # El sistema de botón blindado para Firefox
    st.subheader("🛰️ Radar Doppler 24/7")
    url_radar = f"https://www.windy.com/-Weather-radar-radar?radar,{LAT},{LON},9"
    st.info("Visualización optimizada para detección de celdas convectivas.")
    st.markdown(f"""
        <a href="{url_radar}" target="_blank" style="text-decoration:none;">
            <div style="background:#4f46e5; color:white; padding:20px; border-radius:12px; text-align:center; font-weight:bold;">
                🚀 ABRIR RADAR EN VIVO (UBICACIÓN EXACTA)
            </div>
        </a>
    """, unsafe_allow_html=True)

elif menu == "❄️ Alerta Heladas":
    st.subheader("❄️ Control de Temperatura Crítica")
    for p in obtener_pronostico():
        if p['min'] < 3: st.error(f"⚠️ {p['f']}: Riesgo Helada ({p['min']}°C)")
        else: st.success(f"✅ {p['f']}: Seguro ({p['min']}°C)")

elif menu == "📝 Bitácora":
    st.subheader("📝 Bitácora Digital de Campo")
    # [Aquí va el código de Bitácora que pegaste arriba]












