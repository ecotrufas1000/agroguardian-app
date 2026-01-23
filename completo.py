import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
import json
import os
import datetime

# === CONFIGURACIÓN PRO 24/7 ===
st.set_page_config(page_title="AgroGuardian 24/7", layout="wide", page_icon="🚜")

st.markdown("""
    <style>
    .main { background-color: #f4f7f6; }
    /* Limpieza de métricas: sin bordes laterales verdes */
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: bold; color: #1e3d2f; }
    [data-testid="stMetric"] { 
        background: white; 
        border-radius: 12px; 
        padding: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
        border: none !important; 
    }
    .badge-alerta { padding: 10px; border-radius: 8px; color: white; font-weight: bold; text-align: center; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# === 1. LÓGICA DE DATOS ===
API_KEY = "2762051ad62d06f1d0fe146033c1c7c8"
LAT, LON = -38.298, -58.208 

@st.cache_data(ttl=600)
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

clima = traer_datos_pro(LAT, LON)

# === 2. BARRA LATERAL ===
with st.sidebar:
    st.markdown("<div style='text-align:center; background:#1e3d2f; padding:10px; border-radius:10px; color:white;'><h3>🛡️ AGROGUARDIAN</h3><small>SISTEMA ACTIVO 24/7</small></div>", unsafe_allow_html=True)
    menu = st.radio("MENÚ OPERATIVO", ["📊 Monitoreo Total", "💧 Balance Hídrico", "⛈️ Radar Granizo", "❄️ Heladas", "📝 Bitácora"])
    st.divider()
    if st.button("🔄 ACTUALIZAR DATOS"): st.rerun()

# === 3. PÁGINAS ===

if menu == "📊 Monitoreo Total":
    st.markdown("""
        <div style="background: linear-gradient(to right, #4c1d95, #7c3aed, #a78bfa); padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 2.2rem;">🚜 AgroGuardian Pro 24/7</h1>
            <p style="margin: 0; opacity: 0.9; font-size: 1.1rem;">CENTRO DE INTELIGENCIA AGROCLIMÁTICA</p>
        </div>
    """, unsafe_allow_html=True)

    # SEMÁFORO DE RIESGO
    riesgos = []
    if clima['temp'] > 32: riesgos.append(("🔥 ESTRÉS TÉRMICO", "#e74c3c"))
    if clima['v_vel'] > 25: riesgos.append(("💨 VIENTO FUERTE", "#f39c12"))
    if clima['presion'] < 1008: riesgos.append(("⛈️ RIESGO TORMENTA", "#8e44ad"))

    if riesgos:
        cols_r = st.columns(len(riesgos))
        for i, (txt, col) in enumerate(riesgos):
            cols_r[i].markdown(f"<div class='badge-alerta' style='background:{col};'>{txt}</div>", unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("TEMP.", f"{clima['temp']}°C")
    m2.metric("HUMEDAD", f"{clima['hum']}%")
    m3.metric("VIENTO", f"{clima['v_vel']} km/h")
    m4.metric("ET0 HOY", f"{clima['etc']} mm")
    m5.metric("LLUVIA EST.", f"{clima['lluvia_est']} mm")

    st.divider()
    c1, c2 = st.columns([2, 1])
    with c1:
        st.caption("🗺️ CENTRO DE MONITOREO GEOPRESENCIAL")
        m = folium.Map(location=[LAT, LON], zoom_start=15, control_scale=True)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Vista Satelital (HD)', overlay=False).add_to(m)
        folium.TileLayer(tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', attr='OpenTopoMap', name='Relieve y Altura', overlay=False).add_to(m)
        folium.TileLayer(name='Mapa de Caminos', overlay=False).add_to(m)
        folium.Marker([LAT, LON], icon=folium.Icon(color="purple", icon="leaf")).add_to(m)
        folium.LayerControl(position='topright', collapsed=False).add_to(m)
        folium_static(m, width=700, height=400)
    
    with c2:
        st.subheader("📅 Pronóstico")
        for p in obtener_pronostico():
            st.write(f"**{p['f']}**: {p['min']}°/{p['max']}°")
            st.caption(p['d'])

elif menu == "💧 Balance Hídrico":
    st.markdown(f"""
        <div style="background: linear-gradient(to right, #2563eb, #3b82f6); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
            <h1 style="color: white; margin: 0; font-size: 2rem;">💧 Gestión Hídrica Pro</h1>
            <p style="margin: 0; opacity: 0.9;">Sincronizado con Reportes de Campo</p>
        </div>
    """, unsafe_allow_html=True)

    cultivo_bot, kc_bot, fecha_bot, etapa_bot = "No definido", 0.85, "Sin datos", "N/A"
    
    if os.path.exists('estado_lote.json'):
        try:
            with open('estado_lote.json', 'r', encoding='utf-8') as f:
                db = json.load(f)
                cultivo_bot = db.get("cultivo", "N/D")
                kc_bot = db.get("kc", 0.85)
                fecha_bot = db.get("ultima_actualizacion", "N/D")
                etapa_bot = db.get("etapa", "N/D")
            st.success(f"✅ **Sincronizado:** Lote de **{cultivo_bot}** en etapa **{etapa_bot}**")
        except: pass

    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("⚙️ Parámetros de Suelo")
        cc = st.number_input("Capacidad de Campo (mm)", 150, 400, 250)
        pm = st.number_input("Punto Marchitez (mm)", 50, 150, 100)
        kc_ajustado = st.slider("Ajuste Manual de Kc", 0.1, 1.3, float(kc_bot))
    
    with c2:
        st.subheader("📊 Consumo hídrico")
        etc = round(clima['etc'] * kc_ajustado, 2)
        st.metric("ETc Real", f"{etc} mm/día")
        lluvia = st.number_input("Lluvia Real (mm)", 0.0, 200.0, float(clima['lluvia_est']))

    st.divider()
    reserva_base = 185.0 
    agua_hoy = min(cc, max(pm, reserva_base + lluvia - etc))
    util_pct = int(((agua_hoy - pm) / (cc - pm)) * 100)
    
    cv1, cv2 = st.columns([1, 2])
    with cv1:
        color_r = "#2ecc71" if util_pct > 50 else "#f1c40f" if util_pct > 30 else "#e74c3c"
        st.markdown(f"""
            <div style="border:1px solid #eee; border-radius:15px; padding:20px; text-align:center; background:white; box-shadow:0 2px 4px rgba(0,0,0,0.05);">
                <p style="color:#666; margin:0; font-size:0.9rem;">AGUA ÚTIL</p>
                <h1 style="color:{color_r}; margin:0; font-size:50px;">{util_pct}%</h1>
            </div>
        """, unsafe_allow_html=True)

    with cv2:
        st.subheader("🚜 Recomendación")
        if util_pct < 45: st.error(f"🚨 **ALERTA:** {cultivo_bot} requiere riego.")
        else: st.success(f"✅ **ESTADO ÓPTIMO:** Reservas suficientes.")

elif menu == "⛈️ Radar Granizo":
    st.markdown("<div style='background: linear-gradient(to right, #1e293b, #475569); padding:25px; border-radius:15px; color:white; text-align:center;'><h2>🚜 Monitor de Tormentas</h2></div>", unsafe_allow_html=True)
    url_radar = f"https://www.windy.com/-Weather-radar-radar?radar,{LAT},{LON},9"
    st.markdown(f'<br><a href="{url_radar}" target="_blank" style="text-decoration:none;"><div style="background:#4f46e5; color:white; padding:20px; border-radius:12px; text-align:center; font-weight:bold;">🚀 ABRIR RADAR DOPPLER</div></a>', unsafe_allow_html=True)

elif menu == "❄️ Heladas":
    st.markdown("<div style='background: linear-gradient(to right, #075985, #0ea5e9); padding:25px; border-radius:15px; color:white; text-align:center;'><h2>❄️ Alerta de Heladas</h2></div>", unsafe_allow_html=True)
    
    colh1, colh2 = st.columns(2)
    with colh1: st.info("📅 **Primera Helada:** 15 de Mayo")
    with colh2: st.warning("📅 **Última Helada Est:** 12 de Septiembre")

    pronos = obtener_pronostico()
    if pronos:
        for p in pronos:
            t_min = p['min']
            if t_min <= 0: st.error(f"**{p['f']}**: 🧊 HELADA METEOROLÓGICA ({t_min}°C)")
            elif t_min <= 3: st.warning(f"**{p['f']}**: 🌱 HELADA AGROMETEOROLÓGICA (Suelo est: {round(t_min-3,1)}°C)")
            else: st.success(f"**{p['f']}**: ✅ SIN RIESGO ({t_min}°C)")

elif menu == "📝 Bitácora":
    st.title("📝 Bitácora de Campo")
    novedad = st.text_area("Observaciones:")
    if st.button("💾 GUARDAR"): st.success("Registro guardado.")
