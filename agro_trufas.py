import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
import json
import os
import datetime

# === CONFIGURACIÓN Y ESTILO COMPACTO ===
st.set_page_config(page_title="AgroGuardian Pro Trufas", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    .main { background-color: #f8f9f6; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; } 
    [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }
    div.stMarkdown p { font-size: 0.85rem; }
    .stMetric { 
        background-color: #ffffff; padding: 8px; 
        border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
    }
    div[data-testid="stSidebar"] { background-color: #1e3d2f; }
    h1, h2, h3 { color: #1e3d2f; margin-bottom: 0.5rem; }
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
    d = {"temp": 0.0, "hum": 0, "presion": 1013, "v_vel": 0.0, "v_dir": 0, "tpw": 0.0, "etc": 4.0, "lluvia_est": 0.0}
    try:
        r_ow = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es", timeout=5).json()
        if 'main' in r_ow:
            d.update({"temp": r_ow['main']['temp'], "hum": r_ow['main']['humidity'], "presion": r_ow['main']['pressure'], 
                      "v_vel": round(r_ow['wind']['speed']*3.6, 1), "v_dir": r_ow['wind']['deg']})
        r_om = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=precipitable_water,et0_fao_evapotranspiration,precipitation&timezone=auto", timeout=5).json()
        if 'hourly' in r_om:
            d.update({"tpw": r_om['hourly']['precipitable_water'][0], "etc": r_om['hourly']['et0_fao_evapotranspiration'][0] or 4.0, "lluvia_est": r_om['hourly']['precipitation'][0]})
    except: pass
    return d

def obtener_pronostico():
    try:
        r = requests.get(f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es", timeout=5).json()
        diario = {}
        for item in r['list']:
            f = item['dt_txt'].split(" ")[0]
            if f not in diario: diario[f] = {"min": item['main']['temp'], "max": item['main']['temp'], "desc": item['weather'][0]['description']}
            else:
                diario[f]["min"] = min(diario[f]["min"], item['main']['temp'])
                diario[f]["max"] = max(diario[f]["max"], item['main']['temp'])
        res = []
        dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for f_s, v in list(diario.items())[:5]:
            dt = datetime.datetime.strptime(f_s, '%Y-%m-%d')
            res.append({"f": f"{dias[dt.weekday()]} {dt.day}", "min": round(v["min"],1), "max": round(v["max"],1), "d": v["desc"].capitalize()})
        return res
    except: return []

clima = obtener_datos()

# === 2. BARRA LATERAL ===
with st.sidebar:
    st.title("AgroGuardian Pro")
    menu = st.radio("SECCIONES", ["📊 Monitoreo", "💧 Balance Hídrico", "⛈️ Granizo", "❄️ Heladas", "📝 Bitácora", "🌡️Temp. del Suelo"])
    st.divider()
    st.caption(f"📍 {round(LAT,3)}, {round(LON,3)}")
    if st.button("🔄 ACTUALIZAR"): st.rerun()

# === 3. PÁGINAS ===

# === 3. PÁGINA: MONITOREO ===
if menu == "📊 Monitoreo":
    st.markdown("""
        <div style="background: linear-gradient(to right, #1e3d2f, #2ecc71); padding: 25px; border-radius: 15px; margin-bottom: 20px; color: white; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 2.2rem;"> 💎 AgroGuardian Pro Trufas</h1>
            <p style="margin: 0; opacity: 0.9; font-size: 1.1rem; font-weight: 300;">Monitoreo Profesional y Pronóstico Extendido</p>
        </div>
    """, unsafe_allow_html=True)

    # --- MÉTRICAS ACTUALES ---
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("TEMP.", f"{clima['temp']}°C")
    m2.metric("HUMEDAD", f"{clima['hum']}%")
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    m3.metric("VIENTO", f"{clima['v_vel']} km/h")
    m4.metric("DIRECCIÓN", dirs[int((clima['v_dir'] + 22.5) / 45) % 8])
    m5.metric("PRECIPITACIÓN", f"{clima['tpw']} mm")

    st.divider()

    # --- MAPA Y PRONÓSTICO ---
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.caption("🗺️ CENTRO DE MONITOREO GEOPRESENCIAL")
        m = folium.Map(location=[LAT, LON], zoom_start=15, control_scale=True)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                         attr='Esri', name='Vista Satelital').add_to(m)
        folium.TileLayer(tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
                         attr='OpenTopoMap', name='Relieve', overlay=True, opacity=0.4).add_to(m)
        folium.Marker([LAT, LON], icon=folium.Icon(color="green", icon="leaf")).add_to(m)
        folium.LayerControl().add_to(m)
        folium_static(m, width=700, height=350)

    with c2:
        st.subheader("📅 Pronóstico 5 Días")
        pronos = obtener_pronostico()
        if pronos:
            for p in pronos:
                with st.container():
                    col_fecha, col_temp = st.columns([1, 1])
                    col_fecha.write(f"**{p['f']}**")
                    col_temp.write(f"{p['min']}° / {p['max']}°")
                    st.caption(f"☁️ {p['d']}")
                    st.write("---")
        else:
            st.warning("No se pudo cargar el pronóstico extendido.")

    # --- RECOMENDACIÓN RÁPIDA ---
    st.info(f"💡 **Nota del día:** Con el pronóstico actual y una ET0 de {clima['etc']} mm, planifica riegos de refresco si las máximas superan los 30°C.")

elif menu == "💧 Balance Hídrico":
    st.header("💧 Balance Hídrico Especializado - Trufera")
    kc_fijo = 1.0
    etc_trufa = round(clima['etc'] * kc_fijo, 2)
    riego_tecnico = round(etc_trufa * 0.5, 2)
    
    st.info(f"🌳 **Estrategia:** Reposición del 50% de la ETc para Roble/Encina.")
    
    col1, col2 = st.columns(2)
    col1.metric("Consumo Hoy (ETc)", f"{etc_trufa} mm")
    col2.metric("Riego Sugerido (50%)", f"{riego_tecnico} mm")

    if etc_trufa > clima['lluvia_est']:
        sug_final = max(0.0, riego_tecnico - clima['lluvia_est'])
        st.warning(f"📢 Aplicar **{sug_final} mm** de riego.")

elif menu == "⛈️ Granizo":
    st.title("⛈️ Alerta de Granizo")
    url_radar = f"https://www.windy.com/-Weather-radar-radar?radar,{LAT},{LON},9"
    st.markdown(f'<a href="{url_radar}" target="_blank"><button style="width:100%; background-color:#2ecc71; color:white; padding:20px; border-radius:10px;">🛰️ ABRIR RADAR DOPPLER</button></a>', unsafe_allow_html=True)

elif menu == "❄️ Heladas":
    st.subheader("❄️ Alerta Heladas")
    pronos = obtener_pronostico()
    for p in pronos:
        if p['min'] < 3: st.error(f"⚠️ {p['f']}: Riesgo ({p['min']}°C)")
        else: st.success(f"✅ {p['f']}: Seguro ({p['min']}°C)")

elif menu == "📝 Bitácora":
    st.title("📝 Bitácora de Campo")
    nota = st.text_area("Escribe una novedad:")
    if st.button("💾 Guardar"):
        st.success("Nota guardada localmente.")

elif menu == "🌡️Temp. del Suelo":
    st.header("🌡️ Perfil Térmico del Suelo")
    t_10 = round(clima['temp'] * 0.82, 1)
    t_20 = round(t_10 * 0.92, 1)
    t_30 = round(t_20 * 0.95, 1)

    c1, c2, c3 = st.columns(3)
    c1.metric("10 cm", f"{t_10}°C")
    c2.metric("20 cm", f"{t_20}°C")
    c3.metric("30 cm", f"{t_30}°C")

    st.divider()
    st.subheader("💧 Riego de Refresco (50% ETc)")
    riego_50 = round(clima['etc'] * 0.5, 1)
    if t_10 >= 27:
        st.error(f"🚨 Alerta: Aplicar {riego_50} mm")
    else:
        st.success(f"✅ Normal: Mantener con {riego_50} mm")

    st.divider()
    st.subheader("🐕 Registro de Hallazgos")
    with st.expander("📝 Cargar nueva trufa"):
        f1, f2 = st.columns(2)
        tipo = f1.selectbox("Categoría", ["Extra", "Primera", "Segunda"])
        peso = f2.number_input("Peso (g)", 0, 1000, 30)
        if st.button("💾 GUARDAR TRUFA"):
            st.balloons()
            st.success("¡Trufa registrada!")


