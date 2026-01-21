import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
import json
import os
from datetime import datetime

# === CONFIGURACIÓN Y ESTILO COMPACTO ===
st.set_page_config(page_title="AgroGuardian Pro", layout="wide", page_icon="🚜")

st.markdown("""
    <style>
    .main { background-color: #f8f9f6; }
    /* Achicar métricas y textos */
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
        # OpenWeather (Actual)
        r_ow = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es", timeout=5).json()
        if 'main' in r_ow:
            d.update({"temp": r_ow['main']['temp'], "hum": r_ow['main']['humidity'], "presion": r_ow['main']['pressure'], 
                      "v_vel": round(r_ow['wind']['speed']*3.6, 1), "v_dir": r_ow['wind']['deg']})
        # OpenMeteo (Agro)
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
            dt = datetime.strptime(f_s, '%Y-%m-%d')
            res.append({"f": f"{dias[dt.weekday()]} {dt.day}", "min": round(v["min"],1), "max": round(v["max"],1), "d": v["desc"].capitalize()})
        return res
    except: return []

clima = obtener_datos()

# === 2. BARRA LATERAL (Define la variable 'menu' primero) ===
with st.sidebar:
    st.title("AgroGuardian Pro")
    st.markdown("---")
    menu = st.radio("SECCIONES", ["📊 Monitoreo", "💧 Balance Hídrico", "⛈️ Granizo", "❄️ Heladas", "📝 Bitácora"])
    st.markdown("---")
    st.caption(f"📍 {round(LAT,3)}, {round(LON,3)}")
    if st.button("🔄 ACTUALIZAR"): st.rerun()

# === 3. PÁGINA: MONITOREO ===
if menu == "📊 Monitoreo":
    # Fila de métricas con alertas visuales
    m1, m2, m3, m4, m5 = st.columns(5)
    
    # Alertas
    t_color = "normal" if clima['temp'] < 32 else "inverse"
    v_color = "off" if clima['v_vel'] < 18 else "normal"
    
    m1.metric("TEMP.", f"{clima['temp']}°C", delta="Calor" if clima['temp'] > 32 else None, delta_color=t_color)
    m2.metric("HUMEDAD", f"{clima['hum']}%")
    
    # Dirección de viento
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    m3.metric("VIENTO", f"{clima['v_vel']} km/h", delta="Fuerte" if clima['v_vel'] > 18 else None, delta_color=v_color)
    m4.metric("DIRECCIÓN", dirs[int((clima['v_dir'] + 22.5) / 45) % 8])
    m5.metric("PRECIPITACION", f"{clima['tpw']} mm")

    st.markdown("---")
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.caption("🗺️ VISTA SATELITAL")
        m = folium.Map(location=[LAT, LON], zoom_start=15)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        folium.Marker([LAT, LON], icon=folium.Icon(color="green", icon="leaf")).add_to(m)
        folium_static(m, width=700, height=280)
    
    with c2:
        st.caption("🐮 BIENESTAR (ITH)")
        t_f = (1.8 * clima['temp']) + 32
        ith = round(t_f - (0.55 - 0.55 * (clima['hum'] / 100)) * (t_f - 58), 1)
        bg = "#2ecc71" if ith < 72 else "#f1c40f" if ith < 79 else "#e74c3c"
        st.markdown(f"<div style='background:{bg}; padding:15px; border-radius:10px; text-align:center; color:white;'><h2 style='margin:0;'>{ith}</h2><small>ESTADO ITH</small></div>", unsafe_allow_html=True)
        
        st.caption("📅 PRONÓSTICO CORTO")
        pronos = obtener_pronostico()
        for p in pronos[:3]: # Solo 3 para que sea compacto
            st.write(f"**{p['f']}:** {p['min']}°/{p['max']}° - {p['d']}")

# === 4. OTRAS SECCIONES (Para evitar errores de NameError si cambias de pestaña) ===
elif menu == "💧 Balance Hídrico":
    st.subheader("💧 Gestión de Agua en Suelo")

    # --- LEER SINCRONIZACIÓN DESDE EL BOT ---
    cultivo_bot = "No definido"
    kc_bot = 0.85
    if os.path.exists('estado_lote.json'):
        with open('estado_lote.json', 'r', encoding='utf-8') as f:
            datos_bot = json.load(f)
            cultivo_bot = datos_bot.get("cultivo", "No definido")
            kc_bot = datos_bot.get("kc", 0.85)
            fecha_bot = datos_bot.get("ultima_actualizacion", "-")

    # --- INTERFAZ ---
    st.info(f"🔄 **Sincronizado con Bot:** {cultivo_bot} (Kc: {kc_bot}) - Actualizado: {fecha_bot}")
    
    with st.expander("⚙️ Ajustar Parámetros Manualmente"):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            capacidad_campo = st.number_input("Capacidad de Campo (mm)", value=250)
            punto_marchitez = st.number_input("Punto de Marchitez (mm)", value=100)
        with col_c2:
            # Si el bot eligió algo, lo usamos por defecto
            cultivo_web = st.selectbox("Cultivo Actual", ["Pastura", "Maíz", "Trigo", "Soja", "Girasol"], 
                                      index=0 if cultivo_bot == "No definido" else ["Pastura", "Maíz", "Trigo", "Soja", "Girasol"].index(cultivo_bot.split()[-1]) if cultivo_bot.split()[-1] in ["Pastura", "Maíz", "Trigo", "Soja", "Girasol"] else 0)
            kc_web = st.slider("Coeficiente Kc", 0.1, 1.3, float(kc_bot))

    # El resto del cálculo de balance hídrico usa 'kc_web'
elif menu == "⛈️ Granizo":
    st.subheader("⛈️ Riesgo Granizo")
    r = 30 if clima['presion'] < 1012 else 10
    if clima['tpw'] > 25: r += 40
    st.metric("Probabilidad", f"{r}%")

elif menu == "❄️ Heladas":
    st.subheader("❄️ Alerta Heladas")
    for p in obtener_pronostico():
        if p['min'] < 3: st.error(f"⚠️ {p['f']}: Riesgo de helada ({p['min']}°C)")
        else: st.success(f"✅ {p['f']}: Sin riesgo ({p['min']}°C)")

elif menu == "📝 Bitácora":
    st.subheader("📝 Bitácora")
    if os.path.exists('bitacora_campo.txt'):
        with open('bitacora_campo.txt', 'r') as f:
            for l in reversed(f.readlines()): st.info(l.strip())




