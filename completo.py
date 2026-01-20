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

# --- CSS PERSONALIZADO ---
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
    .forecast-card {
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
    }
    h1, h2, h3 { color: #1e3d2f; }
    </style>
    """, unsafe_allow_html=True)

# === 1. LÓGICA DE DATOS ===
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

def obtener_datos():
    datos = {"temp": 0.0, "hum": 0, "presion": 1013, "desc": "N/D", "lluvia_est": 0.0, "tpw": 0.0, "etc": 4.0}
    try:
        r_ow = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es", timeout=5).json()
        if 'main' in r_ow:
            datos.update({"temp": r_ow['main']['temp'], "hum": r_ow['main']['humidity'], "presion": r_ow['main']['pressure'], "desc": r_ow['weather'][0]['description'].capitalize()})
        r_om = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=precipitable_water,et0_fao_evapotranspiration,precipitation&timezone=auto", timeout=5).json()
        if 'hourly' in r_om:
            datos.update({"tpw": r_om['hourly']['precipitable_water'][0], "etc": r_om['hourly']['et0_fao_evapotranspiration'][0] or 4.0, "lluvia_est": r_om['hourly']['precipitation'][0]})
    except: pass
    return datos

def obtener_pronostico_completo():
    try:
        r = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es", timeout=5).json()
        diario = {}
        for item in r['list']:
            fecha = item['dt_txt'].split(" ")[0]
            t = item['main']['temp']
            if fecha not in diario: diario[fecha] = {"min": t, "max": t, "desc": item['weather'][0]['description']}
            else:
                diario[fecha]["min"] = min(diario[fecha]["min"], t)
                diario[fecha]["max"] = max(diario[fecha]["max"], t)
        res = []
        dias_es = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for f_str, v in list(diario.items())[:5]:
            dt = datetime.strptime(f_str, '%Y-%m-%d')
            res.append({"fecha": f"{dias_es[dt.weekday()]} {dt.day}", "min": round(v["min"], 1), "max": round(v["max"], 1), "desc": v["desc"].capitalize()})
        return res
    except: return []

clima = obtener_datos()

# === 2. INTERFAZ ===
with st.sidebar:
    st.title("AgroGuardian Pro")
    st.markdown("---")
    menu = st.radio("MENÚ PRINCIPAL", ["📊 Monitoreo", "💧 Balance Hídrico", "⛈️ Granizo", "❄️ Heladas", "📝 Bitácora"])
    st.markdown("---")
    st.info(f"📍 Lote: {round(LAT,3)}, {round(LON,3)}")
    if st.button("🔄 ACTUALIZAR"): 
        st.cache_data.clear()
        st.rerun()

# --- PÁGINA MONITOREO ---
if menu == "📊 Monitoreo":
    st.title("📊 Monitor de Lote")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Temperatura", f"{clima['temp']}°C")
    col2.metric("Humedad", f"{clima['hum']}%")
    col3.metric("Presión", f"{clima['presion']} hPa")
    col4.metric("Agua Aire", f"{clima['tpw']} mm")

    st.subheader("📅 Pronóstico 5 Días")
    pronos = obtener_pronostico_completo()
    if pronos:
        cols_p = st.columns(5)
        for i, p in enumerate(pronos):
            with cols_p[i]:
                border_color = "#ff4b4b" if p['min'] <= 3 else "#e0e0e0"
                st.markdown(f"""
                    <div class="forecast-card" style="border-top: 5px solid {border_color};">
                        <p style="margin:0; font-weight:bold;">{p['fecha']}</p>
                        <h3 style="margin:0; color:#ff4b4b;">{p['max']}°</h3>
                        <h5 style="margin:0; color:#1f77b4;">{p['min']}°</h5>
                        <p style="margin:0; font-size:0.8em;">{p['desc']}</p>
                    </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns([2, 1])
    with c1:
        m = folium.Map(location=[LAT, LON], zoom_start=15)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        folium.Marker([LAT, LON], icon=folium.Icon(color="green", icon="leaf")).add_to(m)
        folium_static(m, width=800, height=350)
    with c2:
        st.subheader("🐮 Bienestar")
        t_f = (1.8 * clima['temp']) + 32
        ith = round(t_f - (0.55 - 0.55 * (clima['hum'] / 100)) * (t_f - 58), 1)
        color = "#2ecc71" if ith < 72 else "#f1c40f" if ith < 79 else "#e74c3c"
        st.markdown(f"<div style='background:{color};padding:25px;border-radius:15px;text-align:center;color:white;'><h1>{ith}</h1><p>ITH ACTUAL</p></div>", unsafe_allow_html=True)

# --- PÁGINA BALANCE HÍDRICO ---
elif menu == "💧 Balance Hídrico":
    st.title("💧 Gestión de Riego y Balance")
    CC_MAX = 250.0 # Capacidad de campo max
    
    col1, col2 = st.columns(2)
    with col1:
        lluvia_manual = st.number_input("Lluvia registrada (mm):", value=float(clima['lluvia_est']), step=0.1)
        etc = clima['etc']
        st.write(f"📉 Consumo estimado (ETc): **{round(etc, 2)} mm**")
    
    agua_hoy = min(CC_MAX, max(0.0, 185.0 + lluvia_manual - etc))
    
    with col2:
        st.metric("Agua Útil en Suelo", f"{round(agua_hoy, 1)} mm")
        st.metric("Déficit a completar", f"{round(CC_MAX - agua_hoy, 1)} mm")

    st.subheader("Evolución Semanal")
    df = pd.DataFrame({
        "Día": ["D-4", "D-3", "D-2", "Ayer", "Hoy"],
        "Agua Útil (mm)": [195, 190, 188, 185, agua_hoy],
        "Límite Crítico": [100] * 5
    }).set_index("Día")
    st.area_chart(df)

# Secciones simplificadas para mantener velocidad
elif menu == "⛈️ Granizo":
    st.title("⛈️ Alerta de Granizo")
    riesgo = 40 if clima['presion'] < 1012 else 10
    if clima['tpw'] > 28: riesgo += 50
    st.metric("Riesgo Estimado", f"{riesgo}%")
    st.progress(riesgo / 100)

elif menu == "❄️ Heladas":
    st.title("❄️ Monitor de Heladas")
    pronos = obtener_pronostico_completo()
    cols = st.columns(len(pronos))
    for i, d in enumerate(pronos):
        es_h = d['min'] <= 3.0
        with cols[i]:
            st.markdown(f"<div style='background:{'#ffebee' if es_h else '#f1f8e9'}; padding:10px; border-radius:10px; text-align:center; border: 1px solid {'red' if es_h else 'green'};'><b>{d['fecha']}</b><h3>{d['min']}°</h3></div>", unsafe_allow_html=True)

elif menu == "📝 Bitácora":
    st.title("📝 Bitácora de Campo")
    if os.path.exists('bitacora_campo.txt'):
        with open('bitacora_campo.txt', 'r', encoding='utf-8') as f:
            for n in reversed(f.readlines()): st.info(n.strip())
    else: st.warning("No hay registros en la bitácora.")
