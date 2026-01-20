import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
import json
import os
from datetime import datetime

# === 1. CONFIGURACIÓN DINÁMICA ===
API_KEY = "2762051ad62d06f1d0fe146033c1c7c8"

# --- NUEVA FUNCIÓN: Lee la ubicación que mandó el productor por Telegram ---
def cargar_ubicacion():
    if os.path.exists('usuarios.json'):
        try:
            with open('usuarios.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data:
                    # Toma el último lote sincronizado por el Bot
                    ultimo_id = list(data.keys())[-1]
                    return data[ultimo_id]['lat'], data[ultimo_id]['lon']
        except: pass
    return -38.298, -58.208 # Coordenadas de Necochea por defecto

# Cargamos las coordenadas actuales
LAT, LON = cargar_ubicacion()

st.set_page_config(page_title="AgroGuardian Pro", layout="wide", page_icon="🚜")

# --- FUNCIONES DE DATOS ---
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

def obtener_pronostico_completo():
    try:
        r = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es", timeout=5).json()
        diario = {}
        if 'list' in r:
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

# === 2. CARGA DE DATOS E INTERFAZ ===
clima = obtener_datos()

with st.sidebar:
    st.title("🚜 AgroGuardian")
    menu = st.radio("Secciones:", ["📊 Monitoreo", "💧 Balance Hídrico", "⛈️ Granizo", "❄️ Heladas", "📝 Bitácora"])
    st.divider()
    st.info(f"📍 Lote actual: {round(LAT,4)}, {round(LON,4)}")
    if st.button("🔄 Sincronizar con Bot"): 
        st.cache_data.clear()
        st.rerun()

# === 3. PÁGINAS (ESTRUCTURA ORIGINAL MANTENIDA) ===
if menu == "📊 Monitoreo":
    st.title("📊 Panel Operativo")
    
    t_f = (1.8 * clima['temp']) + 32
    ith = round(t_f - (0.55 - 0.55 * (clima['hum'] / 100)) * (t_f - 58), 1)
    color_ith = "green" if ith < 72 else "orange" if ith < 79 else "red"
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temperatura Actual", f"{clima['temp']}°C")
    m2.metric("Humedad", f"{clima['hum']}%")
    m3.metric("ITH (Bienestar)", ith)
    m4.metric("Agua en Aire (TPW)", f"{clima['tpw']} mm")
    
    st.divider()
    st.subheader("📅 Pronóstico Próximos 5 días")
    pronos = obtener_pronostico_completo()
    if pronos:
        cols_p = st.columns(5)
        for i, p in enumerate(pronos):
            with cols_p[i]:
                border = "#ff4b4b" if p['min'] <= 3 else "#e0e0e0"
                st.markdown(f"<div style='border: 2px solid {border}; border-radius: 10px; padding: 10px; text-align: center; background-color: #f9f9f9;'><p style='margin:0; font-weight: bold; color: #555;'>{p['fecha']}</p><h2 style='margin:0; color: #ff4b4b;'>{p['max']}°</h2><h4 style='margin:0; color: #1f77b4;'>{p['min']}°</h4><p style='margin:0; font-size: 0.8em; color: #777;'>{p['desc']}</p></div>", unsafe_allow_html=True)
    
    st.divider()
    c_map, c_vaca = st.columns([2, 1])
    with c_map:
        m = folium.Map(location=[LAT, LON], zoom_start=14)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        folium.Marker([LAT, LON], icon=folium.Icon(color="green")).add_to(m)
        folium_static(m, width=700, height=300)
    with c_vaca:
        st.markdown(f"<div style='background:{color_ith};padding:20px;border-radius:15px;text-align:center;color:white;'><h1>{ith}</h1><p>ESTADO ITH</p></div>", unsafe_allow_html=True)

# ... (El resto de las secciones como Balance, Granizo y Heladas usan LAT y LON dinámicos ahora) ...
elif menu == "💧 Balance Hídrico":
    st.title("💧 Balance (Capacidad 250mm)")
    CC_MAX = 250.0
    lluvia = st.number_input("Lluvia Real (mm):", value=float(clima['lluvia_est']), step=0.1)
    etc = clima['etc']
    agua_hoy = min(CC_MAX, max(0.0, 185.0 + lluvia - etc)) 
    m1, m2 = st.columns(2)
    m1.metric("Agua Útil", f"{round(agua_hoy, 1)} mm", f"{round(lluvia - etc, 1)} mm")
    m2.metric("Déficit", f"{round(CC_MAX - agua_hoy, 1)} mm")
    df = pd.DataFrame({"Día": ["D-4", "D-3", "D-2", "Ayer", "Hoy"], "Agua Útil (mm)": [195, 190, 188, 185, agua_hoy]}).set_index("Día")
    st.line_chart(df)

elif menu == "⛈️ Granizo":
    st.title("⛈️ Riesgo de Granizo")
    riesgo = 40 if clima['presion'] < 1012 else 0
    if clima['tpw'] > 28: riesgo += 40
    st.markdown(f"<h1 style='font-size:100px;text-align:center;color:#555;'>{riesgo}%</h1>", unsafe_allow_html=True)

elif menu == "❄️ Heladas":
    st.title("❄️ Alerta de Heladas")
    pronos = obtener_pronostico_completo()
    if pronos:
        cols = st.columns(5)
        for i, d in enumerate(pronos):
            es_h = d['min'] <= 3.0
            bg = "#ffebee" if es_h else "#f1f8e9"
            with cols[i]:
                st.markdown(f"<div style='background:{bg};padding:10px;border-radius:10px;text-align:center;border:1px solid {'red' if es_h else 'green'};'><b>{d['fecha']}</b><h3>{d['min']}°</h3><small>{d['desc']}</small></div>", unsafe_allow_html=True)

elif menu == "📝 Bitácora":
    st.title("📝 Novedades")
    if os.path.exists('bitacora_campo.txt'):
        with open('bitacora_campo.txt', 'r', encoding='utf-8') as f:
            for n in reversed(f.readlines()): st.info(n.strip())
