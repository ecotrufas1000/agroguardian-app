import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
import json
import os
import datetime

# === CONFIGURACIÓN Y ESTILO COMPACTO ===
st.set_page_config(page_title="AgroGuardian Pro", layout="wide", page_icon="🚜")

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
    menu = st.radio("SECCIONES", ["📊 Monitoreo", "💧 Balance Hídrico", "⛈️ Granizo", "❄️ Heladas", "📝 Bitácora"])
    st.divider()
    st.caption(f"📍 {round(LAT,3)}, {round(LON,3)}")
    if st.button("🔄 ACTUALIZAR"): st.rerun()

# === 3. PÁGINA: MONITOREO ===
if menu == "📊 Monitoreo":
    # --- ENCABEZADO PROFESIONAL ---
    st.markdown("""
        <div style="background: linear-gradient(to right, #1e3d2f, #2ecc71); padding: 25px; border-radius: 15px; margin-bottom: 20px; color: white; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 2.2rem;">🚜 AgroGuardian Pro</h1>
            <p style="margin: 0; opacity: 0.9; font-size: 1.1rem; font-weight: 300;">Tu asistente profesional de monitoreo y decisiones climáticas</p>
        </div>
    """, unsafe_allow_html=True)

    # --- LÓGICA DE ALERTAS ---
    riesgo_granizo = 0
    if clima['presion'] < 1010: riesgo_granizo += 30
    if clima['tpw'] > 30: riesgo_granizo += 30
    if clima['v_vel'] > 25: riesgo_granizo += 20
    
    # Colores para métricas (evita NameError)
    t_color = "normal" if clima['temp'] < 32 else "inverse"
    v_color = "off" if clima['v_vel'] < 18 else "normal"

    if riesgo_granizo >= 50:
        st.error(f"⚠️ **ALERTA DE TORMENTA:** El riesgo de granizo es del **{riesgo_granizo}%**. Revisa la sección de Granizo para ver el Radar.")

    # Fila de métricas
    m1, m2, m3, m4, m5 = st.columns(5)
    
    m1.metric("TEMP.", f"{clima['temp']}°C", delta="Calor" if clima['temp'] > 32 else None, delta_color=t_color)
    m2.metric("HUMEDAD", f"{clima['hum']}%")
    
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    m3.metric("VIENTO", f"{clima['v_vel']} km/h", delta="Fuerte" if clima['v_vel'] > 18 else None, delta_color=v_color)
    m4.metric("DIRECCIÓN", dirs[int((clima['v_dir'] + 22.5) / 45) % 8])
    m5.metric("PRECIPITACION", f"{clima['tpw']} mm")

    st.divider()
    
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
        for p in pronos[:3]:
            st.write(f"**{p['f']}:** {p['min']}°/{p['max']}° - {p['d']}")

# === 4. PÁGINA: BALANCE HÍDRICO ===
elif menu == "💧 Balance Hídrico":
    st.title("💧 Gestión Hídrica del Lote")

    cultivo_bot, kc_bot, fecha_bot, etapa_bot = "No definido", 0.85, "Sin datos", "N/A"
    if os.path.exists('estado_lote.json'):
        try:
            with open('estado_lote.json', 'r', encoding='utf-8') as f:
                db = json.load(f)
                cultivo_bot, kc_bot = db.get("cultivo", "N/D"), db.get("kc", 0.85)
                fecha_bot, etapa_bot = db.get("ultima_actualizacion", "N/D"), db.get("etapa", "N/D")
        except: pass

    st.info(f"🔄 **Lote:** {cultivo_bot} | **Kc:** {kc_bot} | **Fase:** {etapa_bot} (Act: {fecha_bot})")
    
    with st.expander("⚙️ Configuración de Suelo"):
        col1, col2 = st.columns(2)
        cc = col1.number_input("Capacidad de Campo (mm)", 200, 400, 250)
        pm = col1.number_input("Punto Marchitez (mm)", 50, 150, 100)
        kc_web = col2.slider("Ajuste Kc", 0.1, 1.3, float(kc_bot))
        lluvia = col2.number_input("Lluvia Real (mm)", 0.0, 200.0, float(clima['lluvia_est']))

    etc = round(clima['etc'] * kc_web, 2)
    agua_hoy = min(cc, max(pm, 185.0 + lluvia - etc))
    util_pct = int(((agua_hoy - pm) / (cc - pm)) * 100)
    umbral = pm + (cc - pm) * 0.4 

    c1, c2 = st.columns([1, 2])
    with c1:
        color = "#2ecc71" if util_pct > 50 else "#f1c40f" if util_pct > 30 else "#e74c3c"
        st.markdown(f"<div style='border:2px solid #ddd;border-radius:15px;padding:20px;text-align:center;background:white;'><p style='color:#666;margin:0;'>AGUA ÚTIL</p><h1 style='color:{color};margin:0;font-size:50px;'>{util_pct}%</h1><p style='color:#888;margin:0;'>{round(agua_hoy,1)} mm</p></div>", unsafe_allow_html=True)

    with c2:
        st.write(f"💧 **Consumo (ETc):** {etc} mm/día")
        if util_pct < 40: st.error("🚨 **ALERTA DE RIEGO:** El suelo está bajo el umbral crítico.")
        else: st.success("✅ **ESTADO ÓPTIMO:** Reserva hídrica suficiente.")

    st.divider()
    st.subheader("📈 Proyección de Reserva (7 días)")
    fechas = [(datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%d/%m') for i in range(7)]
    curva = []
    temp_agua = agua_hoy
    for i in range(7):
        curva.append(round(temp_agua, 1))
        temp_agua = max(pm, temp_agua - etc)
    
    df_graf = pd.DataFrame({"Día": fechas, "Reserva (mm)": curva, "Umbral Crítico": [umbral]*7}).set_index("Día")
    st.area_chart(df_graf, color=["#3498db", "#e74c3c"])

elif menu == "⛈️ Granizo":
    st.title("⛈️ Alerta de Granizo y Tormentas")
    
    riesgo = 0
    if clima['presion'] < 1010: riesgo += 30
    if clima['hum'] > 80: riesgo += 20
    if clima['tpw'] > 30: riesgo += 30
    if clima['v_vel'] > 25: riesgo += 20
    
    color_riesgo = "#2ecc71" if riesgo < 40 else "#f1c40f" if riesgo < 70 else "#e74c3c"
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"""
            <div style="background:{color_riesgo}; padding:30px; border-radius:15px; text-align:center; color:white;">
                <h3 style="margin:0; color:white;">Probabilidad de Tormenta</h3>
                <h1 style="margin:0; font-size:80px; color:white;">{riesgo}%</h1>
            </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.subheader("📡 Monitoreo Doppler")
        st.write("Para ver ecos de granizo en tiempo real:")
        url_radar = f"https://www.windy.com/-Weather-radar-radar?radar,{LAT},{LON},9"
        
        st.markdown(f"""
            <a href="{url_radar}" target="_blank">
                <button style="width:100%; background-color:#2ecc71; color:white; padding:20px; font-size:18px; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">
                    🛰️ ABRIR RADAR DOPPLER
                </button>
            </a>
        """, unsafe_allow_html=True)

    st.divider()
    if riesgo >= 70: st.error("🚨 **AVISO URGENTE:** Riesgo extremo de granizo.")
    elif riesgo >= 40: st.warning("⚠️ **ATENCIÓN:** Atmósfera inestable.")
    else: st.success("✅ **TIEMPO ESTABLE.**")

elif menu == "❄️ Heladas":
    st.subheader("❄️ Alerta Heladas")
    for p in obtener_pronostico():
        if p['min'] < 3: st.error(f"⚠️ {p['f']}: Riesgo de helada ({p['min']}°C)")
        else: st.success(f"✅ {p['f']}: Sin riesgo ({p['min']}°C)")

elif menu == "📝 Bitácora":
    st.subheader("📝 Historial de Novedades")
    if os.path.exists('bitacora_campo.txt'):
        with open('bitacora_campo.txt', 'r', encoding='utf-8') as f:
            for l in reversed(f.readlines()): st.info(l.strip())
