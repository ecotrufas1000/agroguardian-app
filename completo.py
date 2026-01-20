import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
import json
import os
from datetime import datetime

# === CONFIGURACIÓN DE PÁGINA Y ESTILO ===
st.set_page_config(page_title="AgroGuardian Pro", layout="wide", page_icon="🚜")

# --- CSS PERSONALIZADO PARA ESTÉTICA PREMIUM ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f1; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
    }
    div[data-testid="stSidebar"] { background-color: #1e3d2f; color: white; }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        background-color: #4CAF50; 
        color: white; 
        border: none;
        font-weight: bold;
    }
    h1, h2, h3 { color: #1e3d2f; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# === 1. LÓGICA DE DATOS (MANTENEMOS TU LÓGICA) ===
API_KEY = "2762051ad62d06f1d0fe146033c1c7c8"

def cargar_ubicacion():
    if os.path.exists('usuarios.json'):
        try:
            with open('usuarios.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data:
                    ultimo_id = list(data.keys())[-1]
                    return data[ultimo_id]['lat'], data[ultimo_id]['lon']
        except: pass
    return -38.298, -58.208 

LAT, LON = cargar_ubicacion()

# --- FUNCIONES DE CLIMA ---
def obtener_datos():
    datos_base = {"temp": 0.0, "hum": 0, "presion": 1013, "desc": "N/D", "lluvia_est": 0.0, "tpw": 0.0, "etc": 4.0}
    try:
        r_ow = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es", timeout=5).json()
        if 'main' in r_ow:
            datos_base.update({"temp": r_ow['main']['temp'], "hum": r_ow['main']['humidity'], "presion": r_ow['main']['pressure'], "desc": r_ow['weather'][0]['description'].capitalize()})
        r_om = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=precipitable_water,et0_fao_evapotranspiration,precipitation&timezone=auto", timeout=5).json()
        if 'hourly' in r_om:
            datos_base.update({"tpw": r_om['hourly']['precipitable_water'][0], "etc": r_om['hourly']['et0_fao_evapotranspiration'][0] or 4.0, "lluvia_est": r_om['hourly']['precipitation'][0]})
    except: pass
    return datos_base

clima = obtener_datos()

# === 2. INTERFAZ VISUAL ===
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2950/2950798.png", width=80) # Icono Agro
    st.title("AgroGuardian Pro")
    st.markdown("---")
    menu = st.radio("MENÚ PRINCIPAL", ["📊 Monitoreo", "💧 Balance Hídrico", "⛈️ Granizo", "❄️ Heladas", "📝 Bitácora"])
    st.markdown("---")
    st.write(f"📍 **Lote Activo:** \n{round(LAT,4)}, {round(LON,4)}")
    if st.button("🔄 ACTUALIZAR DATOS"): 
        st.cache_data.clear()
        st.rerun()

# --- PÁGINA MONITOREO ---
if menu == "📊 Monitoreo":
    st.title("📊 Monitor de Lote en Tiempo Real")
    
    # Métricas Estilizadas
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("🌡️ Temperatura", f"{clima['temp']}°C")
    with col2: st.metric("💧 Humedad", f"{clima['hum']}%")
    with col3: st.metric("🌍 Presión", f"{clima['presion']} hPa")
    with col4: st.metric("🚿 Agua (TPW)", f"{clima['tpw']} mm")

    st.markdown("---")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("🗺️ Vista Satelital del Lote")
        m = folium.Map(location=[LAT, LON], zoom_start=15)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        folium.Marker([LAT, LON], popup="Tu Lote", icon=folium.Icon(color="green", icon="leaf")).add_to(m)
        folium_static(m, width=800, height=400)
    
    with c2:
        st.subheader("🐮 Bienestar Animal")
        t_f = (1.8 * clima['temp']) + 32
        ith = round(t_f - (0.55 - 0.55 * (clima['hum'] / 100)) * (t_f - 58), 1)
        color = "#2ecc71" if ith < 72 else "#f1c40f" if ith < 79 else "#e74c3c"
        st.markdown(f"""
            <div style="background-color: {color}; padding: 30px; border-radius: 20px; text-align: center; color: white;">
                <h1 style="margin:0; font-size: 50px;">{ith}</h1>
                <p style="margin:0; font-weight: bold;">ÍNDICE ITH</p>
            </div>
            """, unsafe_allow_html=True)
        st.info("El ITH indica el estrés calórico en ganado. Verde: Confort | Naranja: Alerta | Rojo: Peligro.")

# (Aquí seguirían las otras secciones con el mismo estilo de diseño)
elif menu == "💧 Balance Hídrico":
    st.title("💧 Balance Hídrico")
    st.info("Estimación basada en Evapotranspiración (FAO-56)")
    # ... resto del código ...
