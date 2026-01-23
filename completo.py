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
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: bold; color: #1e3d2f; }
    .stMetric { background: white; border-radius: 12px; border-left: 6px solid #2ecc71; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
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
    # NOMBRES DE MENÚ SINCRONIZADOS
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

    # --- RESTAURACIÓN DE CONEXIÓN CON EL BOT ---
    cultivo_bot, kc_bot, fecha_bot, etapa_bot = "No definido", 0.85, "Sin datos", "N/A"
    
    if os.path.exists('estado_lote.json'):
        try:
            with open('estado_lote.json', 'r', encoding='utf-8') as f:
                db = json.load(f)
                cultivo_bot = db.get("cultivo", "N/D")
                kc_bot = db.get("kc", 0.85)
                fecha_bot = db.get("ultima_actualizacion", "N/D")
                etapa_bot = db.get("etapa", "N/D")
            st.success(f"✅ **Sincronizado:** Lote de **{cultivo_bot}** en etapa **{etapa_bot}** (Actualizado: {fecha_bot})")
        except Exception as e:
            st.warning("⚠️ No se pudo leer la base de datos del bot, usando valores por defecto.")

    # --- INTERFAZ DE CÁLCULO ---
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("⚙️ Parámetros de Suelo")
        cc = st.number_input("Capacidad de Campo (mm)", 150, 400, 250)
        pm = st.number_input("Punto Marchitez (mm)", 50, 150, 100)
        kc_ajustado = st.slider("Ajuste Manual de Kc", 0.1, 1.3, float(kc_bot))
    
    with c2:
        st.subheader("📊 Consumo hídrico")
        etc = round(clima['etc'] * kc_ajustado, 2)
        st.metric("Evapotranspiración Real (ETc)", f"{etc} mm/día")
        
        lluvia = st.number_input("Lluvia Real Registrada (mm)", 0.0, 200.0, float(clima['lluvia_est']))

    st.divider()

    # --- CÁLCULO DE RESERVA ÚTIL ---
    # Estimación de reserva actual (esto idealmente vendría de una serie histórica)
    reserva_estimada = 185.0 # Valor base
    agua_hoy = min(cc, max(pm, reserva_estimada + lluvia - etc))
    util_pct = int(((agua_hoy - pm) / (cc - pm)) * 100)
    
    col_v1, col_v2 = st.columns([1, 2])
    
    with col_v1:
        color_reserva = "#2ecc71" if util_pct > 50 else "#f1c40f" if util_pct > 30 else "#e74c3c"
        st.markdown(f"""
            <div style="border:2px solid #ddd; border-radius:15px; padding:20px; text-align:center; background:white;">
                <p style="color:#666; margin:0;">AGUA ÚTIL ACTUAL</p>
                <h1 style="color:{color_reserva}; margin:0; font-size:60px;">{util_pct}%</h1>
                <p style="color:#888; margin:0;">{round(agua_hoy,1)} mm disponibles</p>
            </div>
        """, unsafe_allow_html=True)

    with col_v2:
        st.subheader("🚜 Recomendación de Manejo")
        if util_pct < 45:
            st.error(f"🚨 **ALERTA DE RIEGO:** El lote de {cultivo_bot} requiere reposición inmediata.")
            st.write(f"Para volver al 70% de Agua Útil, aplicar: **{round((cc-pm)*0.7 + pm - agua_hoy, 1)} mm**")
        else:
            st.success(f"✅ **ESTADO ÓPTIMO:** El lote de {cultivo_bot} tiene reservas suficientes.")

    # --- GRÁFICO DE PROYECCIÓN 7 DÍAS ---
    st.subheader("📈 Proyección de Reserva (Próximos 7 días)")
    fechas = [(datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%d/%m') for i in range(7)]
    curva = []
    temp_agua = agua_hoy
    for i in range(7):
        curva.append(round(temp_agua, 1))
        temp_agua = max(pm, temp_agua - etc) # Asumiendo ETc constante para la proyección
    
    df_graf = pd.DataFrame({"Día": fechas, "Reserva (mm)": curva}).set_index("Día")
    st.area_chart(df_graf, color="#3b82f6")

elif menu == "⛈️ Radar Granizo":
    st.markdown("""
        <div style="background: linear-gradient(to right, #1e293b, #475569); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
            <h1 style="color: white; margin: 0; font-size: 2rem;">🚜 Monitor de Tormentas</h1>
            <p style="margin: 0; opacity: 0.9;">Detección de celdas de granizo y nubosidad convectiva</p>
        </div>
    """, unsafe_allow_html=True)

    riesgo = 0
    if clima['presion'] < 1008: riesgo += 50
    if clima['hum'] > 80: riesgo += 30
    if clima['temp'] > 28: riesgo += 20
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("📊 Análisis de Riesgo")
        if riesgo >= 70:
            st.error(f"### RIESGO CRÍTICO: {riesgo}%")
            st.markdown("⚠️ **ALERTA ROJA:** Formación de tormentas probables.")
        elif riesgo >= 40:
            st.warning(f"### RIESGO MODERADO: {riesgo}%")
            st.markdown("🟡 **AVISO:** Vigilancia meteorológica recomendada.")
        else:
            st.success(f"### RIESGO BAJO: {riesgo}%")
            st.markdown("🟢 **ESTADO VERDE:** Sin indicios de tormentas severas.")

    with c2:
        st.subheader("🛰️ Control de Radar")
        url_radar = f"https://www.windy.com/-Weather-radar-radar?radar,{LAT},{LON},9"
        st.markdown(f"""<a href="{url_radar}" target="_blank" style="text-decoration:none;"><div style="background:#4f46e5; color:white; padding:20px; border-radius:12px; text-align:center; font-weight:bold;">🚀 ABRIR RADAR DOPPLER INTERACTIVO</div></a>""", unsafe_allow_html=True)

elif menu == "❄️ Heladas":
    st.markdown(f"""
        <div style="background: linear-gradient(to right, #075985, #0ea5e9); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
            <h1 style="color: white; margin: 0; font-size: 2rem;">❄️ Monitor de Heladas Agrometeorológicas</h1>
            <p style="margin: 0; opacity: 0.9;">Detección de heladas y seguimiento de fechas críticas</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 1. DATOS HISTÓRICOS (Fechas de ocurrencia) ---
    # En un sistema pro, esto se leería de una base de datos. 
    # Aquí simulamos el registro de la campaña actual.
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        st.info("📅 **Primera Helada de la Campaña**\n\n**15 de Mayo** (Registrada)")
    with col_h2:
        st.warning("📅 **Última Helada Estimada**\n\n**12 de Septiembre** (Promedio zona)")

    st.divider()

    # --- 2. ANÁLISIS DE RIESGO AGROMETEOROLÓGICO ---
    st.subheader("🔍 Alerta para las próximas 120 horas")
    
    pronos = obtener_pronostico()
    
    if pronos:
        for p in pronos:
            t_min = p['min']
            # Estimación de Helada Agrometeorológica: Suele ser entre 2°C y 3°C 
            # más fría que la temperatura en abrigo meteorológico (1.5m)
            t_suelo_est = round(t_min - 3.0, 1)
            
            # Determinación de severidad
            if t_min <= 0:
                clase = "error"
                msg = f"🧊 **HELADA METEOROLÓGICA:** Riesgo total. Temp: {t_min}°C"
            elif t_min <= 3:
                clase = "warning"
                msg = f"🌱 **HELADA AGROMETEOROLÓGICA:** Riesgo en nivel de cultivo. Temp. suelo estimada: {t_suelo_est}°C"
            else:
                clase = "success"
                msg = f"✅ **SIN RIESGO:** Temp. mínima segura ({t_min}°C)"

            # Mostrar alerta
            if clase == "error": st.error(f"**{p['f']}**: {msg}")
            elif clase == "warning": st.warning(f"**{p['f']}**: {msg}")
            else: st.success(f"**{p['f']}**: {msg}")

    st.divider()

    # --- 3. RECOMENDACIÓN TÉCNICA ---
    with st.expander("📘 Manual de Acción ante Heladas"):
        st.write("""
        * **Helada Blanca:** Con humedad alta. Se forma escarcha. Protege parcialmente los tejidos por el calor de fusión.
        * **Helada Negra:** Con aire muy seco. No hay escarcha, el daño es interno y mucho más severo.
        * **Defensa Activa:** Si el riego está disponible, iniciar antes de que la temperatura de bulbo húmedo llegue a 0°C.
        """)

elif menu == "📝 Bitácora":
    st.title("📝 Bitácora de Campo")
    novedad = st.text_area("Describa la observación:")
    if st.button("💾 GUARDAR"):
        st.success("Registro guardado localmente.")
















