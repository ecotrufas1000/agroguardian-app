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

# === LÓGICA DE DATOS ===
API_KEY = "2762051ad62d06f1d0fe146033c1c7c8"
LAT, LON = -38.298, -58.208 

def obtener_direccion_cardinal(grados):
    direcciones = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                   "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
    indice = int((grados + 11.25) / 22.5) % 16
    return direcciones[indice]

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

# === BARRA LATERAL ===
with st.sidebar:
    st.markdown("<div style='text-align:center; background:#1e3d2f; padding:10px; border-radius:10px; color:white;'><h3>🛡️ AGROGUARDIAN</h3><small>SISTEMA ACTIVO 24/7</small></div>", unsafe_allow_html=True)
    menu = st.radio("MENÚ OPERATIVO", ["📊 Monitoreo Total", "💧 Balance Hídrico", "⛈️ Radar Granizo", "❄️ Heladas", "📝 Bitácora"])
    st.divider()
    if st.button("🔄 ACTUALIZAR DATOS"): st.rerun()

# === PÁGINAS ===

if menu == "📊 Monitoreo Total":
    st.markdown("""
        <div style="background: linear-gradient(to right, #4c1d95, #7c3aed, #a78bfa); padding: 30px; border-radius: 15px; margin-bottom: 25px; color: white; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 2.2rem;">🚜 AgroGuardian Pro 24/7</h1>
            <p style="margin: 0; opacity: 0.9; font-size: 1.1rem;">CENTRO DE INTELIGENCIA AGROCLIMÁTICA</p>
        </div>
    """, unsafe_allow_html=True)

    # (Lógica de riesgos y dirección de viento previa...)
    dir_viento = obtener_direccion_cardinal(clima['v_dir'])

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("TEMP.", f"{clima['temp']}°C")
    m2.metric("HUMEDAD", f"{clima['hum']}%")
    m3.metric("VIENTO", f"{clima['v_vel']} km/h", f"Dir: {dir_viento}")
    m4.metric("ET0 HOY", f"{clima['etc']} mm")
    m5.metric("LLUVIA EST.", f"{clima['lluvia_est']} mm")

    st.divider()

    # --- SOLUCIÓN AL ERROR DE FIREFOX ---
    st.subheader("⛈️ Radar de Tormentas y Precipitación")
    
    # Esta URL usa /widgets/ que permite ser incrustada
    windy_widget_url = f"https://www.windy.com/widgets?radar,{LAT},{LON},8&metricTemp=default&metricWind=default"
    
    st.components.v1.iframe(windy_widget_url, height=500, scrolling=False)
    
    # Respaldo: Enlace directo si el iframe falla por configs del usuario
    st.markdown(f"""
        <div style="text-align: right; margin-top: -20px;">
            <a href="https://www.windy.com/-Radar-radar?radar,{LAT},{LON},8" target="_blank" 
               style="color: #4f46e5; text-decoration: none; font-size: 0.85rem; font-weight: bold;">
               ↗️ Ver pantalla completa en Windy.com
            </a>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # (Seguir con el mapa de Folium y Pronóstico...)

    # ... (resto del código de Folium y Pronóstico igual) ...

    # Ventana de Windy Integrada
    st.subheader("⛈️ Radar de Tormentas y Precipitación (Windy)")
    windy_url = f"https://www.windy.com/multimodel?radar,{LAT},{LON},8"
    st.components.v1.iframe(windy_url, height=500, scrolling=True)

    st.divider()

    c1, c2 = st.columns([2, 1])
    with c1:
        st.caption("🗺️ CENTRO DE MONITOREO GEOPRESENCIAL")
        m = folium.Map(location=[LAT, LON], zoom_start=15, control_scale=True)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri', name='Vista Satelital (HD)', overlay=False).add_to(m)
        folium.Marker([LAT, LON], icon=folium.Icon(color="purple", icon="leaf")).add_to(m)
        folium_static(m, width=700, height=400)
    
    with c2:
        st.subheader("📅 Pronóstico")
        for p in obtener_pronostico():
            st.write(f"**{p['f']}**: {p['min']}°/{p['max']}°")
            st.caption(p['d'])

# (Aquí seguirían las otras secciones: Balance Hídrico, Heladas, etc., tal cual las teníamos)
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
    # 1. CSS para eliminar bordes (paréntesis) verdes y mejorar estética
    st.markdown("""
        <style>
        [data-testid="stMetric"] {
            background: white;
            border: none !important;
            border-left: none !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            padding: 15px !important;
            border-radius: 12px;
        }
        /* Eliminar la barra lateral verde de Streamlit */
        [data-testid="stMetric"] > div {
            border-left: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div style="background: linear-gradient(to right, #1e293b, #334155); padding:25px; border-radius:15px; color:white; text-align:center; margin-bottom:20px;">
            <h2 style="color:white; margin:0;">🛰️ Monitor Doppler y Riesgo de Granizo</h2>
            <p style="opacity:0.8; margin:0;">Detección de celdas convectivas en tiempo real</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. CÁLCULO DE PELIGROSIDAD (Índice AgroGuardian)
    # Basado en inestabilidad: Presión baja + Humedad alta + Temperatura alta
    puntos_riesgo = 0
    if clima['presion'] < 1010: puntos_riesgo += 30
    if clima['hum'] > 70: puntos_riesgo += 30
    if clima['temp'] > 28: puntos_riesgo += 40
    
    color_idx = "#2ecc71" if puntos_riesgo < 40 else "#f39c12" if puntos_riesgo < 75 else "#e74c3c"
    nivel_texto = "BAJO" if puntos_riesgo < 40 else "MODERADO" if puntos_riesgo < 75 else "ALTO / INMINENTE"

    col_a, col_b = st.columns([1, 3])
    with col_a:
        st.metric("RIESGO ESTIMADO", nivel_texto)
    with col_b:
        st.markdown(f"""
            <div style="background:{color_idx}; color:white; padding:15px; border-radius:10px; text-align:center; font-weight:bold;">
                ÍNDICE DE INESTABILIDAD: {puntos_riesgo}% <br>
                <small>Factores: Presión {clima['presion']} hPa | Temp {clima['temp']}°C</small>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # 3. VENTANA DOPPLER (URL DE WIDGET PARA EVITAR BLOQUEO DE FIREFOX)
    st.subheader("📡 Radar de Precipitación en Vivo")
    
    # IMPORTANTE: Usamos /widgets/ en la URL, que sí permite 'embedding'
    url_windy_widget = f"https://www.windy.com/widgets?radar,{LAT},{LON},8&metricTemp=default&metricWind=default"
    
    st.components.v1.iframe(url_windy_widget, height=550, scrolling=False)

    # Botón de respaldo elegante
    st.markdown(f"""
        <div style="text-align: right; margin-top: 10px;">
            <a href="https://www.windy.com/-Radar-radar?radar,{LAT},{LON},8" target="_blank" 
               style="text-decoration:none; background:#4f46e5; color:white; padding:10px 20px; border-radius:8px; font-weight:bold;">
               🚀 VER PANTALLA COMPLETA ORIGINAL
            </a>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("❓ ¿Cómo leer el radar para granizo?"):
        st.write("""
        - **Verde/Amarillo:** Lluvia normal.
        - **Rojo/Fucsia:** Tormenta fuerte.
        - **Púrpura/Blanco:** Probabilidad muy alta de **granizo** (alta densidad de hielo).
        """)

import streamlit as st

# -------------------------------------------------
# CONFIGURACIÓN GENERAL
# -------------------------------------------------
st.set_page_config(
    page_title="Monitor de Heladas",
    layout="wide"
)

# -------------------------------------------------
# FUNCIÓN DE PRONÓSTICO (SIMULADA)
# -------------------------------------------------
def obtener_pronostico():
    """
    Devuelve una lista de diccionarios con:
    f   = fecha
    min = temperatura mínima del aire
    """
    return [
        {"f": "28 de Enero", "min": 4.5},
        {"f": "29 de Enero", "min": 2.0},
        {"f": "30 de Enero", "min": -1.3},
        {"f": "31 de Enero", "min": 6.2},
    ]

# -------------------------------------------------
# MENÚ (SIMULADO)
# -------------------------------------------------
menu = st.sidebar.radio(
    "Menú",
    ["Inicio", "Heladas"]
)

# -------------------------------------------------
# PANTALLA INICIO
# -------------------------------------------------
if menu == "Inicio":
    st.title("🌾 Sistema Agrometeorológico")
    st.write("Seleccione una opción del menú lateral.")

# -------------------------------------------------
# PANTALLA HELADAS
# -------------------------------------------------
elif menu == "Heladas":

    # CABECERA
    st.markdown("""
        <div style="
            background: linear-gradient(to right, #075985, #0ea5e9);
            padding: 25px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 20px;
        ">
            <h1 style="margin: 0;">Monitor de Heladas</h1>
            <p style="opacity: 0.9;">
                Detección de helada meteorológica y agrometeorológica
            </p>
        </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------
    # REGISTRO DE FECHAS CRÍTICAS
    # -------------------------------------------------
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("""
            <div style="
                background:white;
                padding:15px;
                border-radius:10px;
                border-left:5px solid #0ea5e9;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
            ">
                <small style="color:gray;">PRIMERA HELADA REGISTRADA</small><br>
                <strong style="font-size:1.2rem; color:#075985;">
                    15 de Mayo
                </strong>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
            <div style="
                background:white;
                padding:15px;
                border-radius:10px;
                border-left:5px solid #f39c12;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
            ">
                <small style="color:gray;">ÚLTIMA HELADA ESTIMADA</small><br>
                <strong style="font-size:1.2rem; color:#d68910;">
                    12 de Septiembre
                </strong>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # -------------------------------------------------
    # ALERTAS DE PRONÓSTICO
    # -------------------------------------------------
    st.subheader("🔍 Alerta de Riesgo (Próximos días)")

    try:
        pronos = obtener_pronostico()
    except Exception as e:
        pronos = []
        st.error(f"No se pudo cargar el pronóstico: {e}")

    if pronos:
        for p in pronos:
            t_min = p["min"]

            # Estimación de temperatura a nivel del suelo
            t_suelo_est = round(t_min - 3.0, 1)

            if t_min <= 0:
                st.error(
                    f"**{p['f']}** 🧊 "
                    f"HELADA METEOROLÓGICA | "
                    f"Aire: {t_min}°C | "
                    f"Suelo est: {t_suelo_est}°C"
                )

            elif t_min <= 3:
                st.warning(
                    f"**{p['f']}** 🌱 "
                    f"RIESGO AGROMETEOROLÓGICO | "
                    f"Suelo est: {t_suelo_est}°C"
                )

            else:
                st.info(
                    f"**{p['f']}** ✅ "
                    f"Sin riesgo ({t_min}°C)"
                )
    else:
        st.warning("No hay datos de pronóstico disponibles.")

    st.divider()

    st.caption(
        "ℹ️ Nota: Helada agrometeorológica ≈ aire ≤ 3°C "
        "puede implicar 0°C o menos a nivel del suelo."
    )

elif menu == "📝 Bitácora":
    st.title("📝 Bitácora de Campo")
    novedad = st.text_area("Observaciones:")
    if st.button("💾 GUARDAR"): st.success("Registro guardado.")















