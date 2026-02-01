
import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
from datetime import datetime, timedelta

# === 1. CONFIGURACIÓN GLOBAL ===
API_KEY = "2762051ad62d06f1d0fe146033c1c7c8" 
LAT, LON = -38.34, -57.98
CAPACIDAD_CAMPO = 300.0 
PUNTO_MARCHITEZ = 150.0
AGUA_UTIL_MAX = CAPACIDAD_CAMPO - PUNTO_MARCHITEZ

st.set_page_config(page_title="AgroGuardian Pro", layout="wide", page_icon="🚜")

# --- FUNCIONES DE SOPORTE ---
def obtener_datos_clima():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es"
    try:
        r = requests.get(url, timeout=5).json()
        return {"temp": r['main']['temp'], "hum": r['main']['humidity'], "desc": r['weather'][0]['description'].capitalize()}
    except:
        return {"temp": 28, "hum": 60, "desc": "Cielo despejado"}

def calcular_ith(temp, hum):
    t_f = (1.8 * temp) + 32
    ith = t_f - (0.55 - 0.55 * (hum / 100)) * (t_f - 58)
    return round(ith, 1)

def obtener_pronostico_semanal():
    dias_nombres = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    pronostico = []
    fecha_hoy = datetime.now()
    iconos = ["☀️", "☀️", "⛅", "🌧️", "⛅", "❄️", "❄️"] # Forzamos helada al final para test
    for i in range(1, 8):
        fecha = fecha_hoy + timedelta(days=i)
        nombre_dia = dias_nombres[fecha.weekday()]
        t_max = 24 - (i * 2) if i > 4 else 24 + (i * 1.1)
        t_min = t_max - 11.5 if i < 5 else -2.0 # Simulación de helada para la Pág 3
        pronostico.append({
            "fecha": f"{nombre_dia} {fecha.day}",
            "t_min": round(t_min, 1),
            "t_max": round(t_max, 1),
            "icono": iconos[i-1],
            "hum": 70 - (i * 2)
        })
    return pronostico

# === 2. BARRA LATERAL (NAVEGACIÓN) ===
with st.sidebar:
    st.title("🚜 AgroGuardian")
    st.markdown("---")
    seleccion = st.radio("Menú de Navegación:", ["📊 Monitoreo de Lote", "💧 Balance Hídrico", "❄️ Pronóstico de Heladas"])
    st.markdown("---")
    st.info(f"**Ubicación:** Miramar, BA\n**Coordenadas:** {LAT}, {LON}")
    if st.button("🔄 Sincronizar"): st.rerun()

# === 3. LÓGICA DE PÁGINAS ===

# --- PÁGINA 1: MONITOREO DE LOTE (RESTAURADA) ---
if seleccion == "📊 Monitoreo de Lote":
    st.title("📊 Monitoreo de Lote")
    st.info("Visualización de Clima, Bienestar Animal y Vigor Vegetal.")
    clima = obtener_datos_clima()
    ith_actual = calcular_ith(clima['temp'], clima['hum'])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temperatura", f"{clima['temp']} °C")
    m2.metric("Humedad", f"{clima['hum']} %")
    m3.metric("Bienestar (ITH)", f"{ith_actual}")
    m4.metric("Vigor (NDVI)", "0.74")

    st.divider()
    col_mapa, col_alertas = st.columns([2, 1])
    with col_mapa:
        st.write("### 🛰️ Mapa Satelital")
        m = folium.Map(location=[LAT, LON], zoom_start=15)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        folium.Marker([LAT, LON], icon=folium.Icon(color="green")).add_to(m)
        folium_static(m, width=700, height=400)

    with col_alertas:
        st.write("### 🐄 Estado Ganadero")
        if ith_actual < 72: st.success(f"**ITH: {ith_actual} - CONFORT**")
        elif 72 <= ith_actual < 79: st.warning(f"**ITH: {ith_actual} - ALERTA**")
        else: st.error(f"**ITH: {ith_actual} - CRÍTICO**")
        with st.expander("📊 Ver Tabla ITH"):
            st.table(pd.DataFrame({"Rango": ["<72","72-78","79-83",">84"], "Estado": ["Confort","Alerta","Peligro","Emergencia"]}))
        st.write("---")
        st.write("### 🌱 Salud Vegetal")
        st.write(f"Índice NDVI: **0.74**")

    st.write("### 📅 Pronóstico Extendido")
    pronostico = obtener_pronostico_semanal()
    cols_pro = st.columns(7)
    for i, dia in enumerate(pronostico):
        with cols_pro[i]:
            st.markdown(f"""<div style="text-align: center; background-color: #F8F9FA; padding: 10px; border-radius: 12px; border: 1px solid #E9ECEF;">
                <p style="margin-bottom: 2px; color: #6C757D; font-weight: bold; font-size: 12px;">{dia['fecha']}</p>
                <h2 style="margin: 5px 0; font-size: 26px;">{dia['icono']}</h2>
                <div style="display: flex; justify-content: center; gap: 8px;">
                    <span style="color: #457B9D; font-weight: 800; font-size: 16px;">{dia['t_min']}°</span>
                    <span style="color: #E63946; font-weight: 800; font-size: 16px;">{dia['t_max']}°</span>
                </div></div>""", unsafe_allow_html=True)

# --- PÁGINA 2: BALANCE HÍDRICO (RESTAURADA) ---
elif seleccion == "💧 Balance Hídrico":
    st.title("💧 Balance Hídrico Operativo")
    st.info("Visualización de Reservas de Agua, Evapotranspiración y Lamina de Riego.")
    with st.container(border=True):
        c_in1, c_in2, c_in3 = st.columns(3)
        with c_in1: lluvia = st.number_input("Lluvia (mm):", min_value=0.0, step=1.0)
        with c_in2: riego = st.number_input("Riego (mm):", min_value=0.0, step=1.0)
        with c_in3: st.write("**Suelo**"); st.caption(f"Capacidad: {CAPACIDAD_CAMPO}mm\nÚtil Máx: {AGUA_UTIL_MAX}mm")
    
    etc_hoy, au_ayer = 4.7, 115.0
    au_hoy = min(AGUA_UTIL_MAX, max(0, au_ayer + lluvia + riego - etc_hoy))
    porcentaje_au = round((au_hoy / AGUA_UTIL_MAX) * 100, 1)
    
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Agua Útil Actual", f"{porcentaje_au}%", delta=f"{lluvia - etc_hoy} mm")
    c2.metric("Consumo (ETc)", f"{etc_hoy} mm")
    c3.metric("Lámina de Agua", f"{round(au_hoy, 1)} mm")

    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        st.write("### 📈 Agua en el Suelo")
        df_t = pd.DataFrame({"Día": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"], "Humedad %": [82, 79, 75, 72, 70, 68, porcentaje_au]})
        st.area_chart(df_t.set_index("Día"), color="#0077b6")
    with col_g2:
        st.write("### Almacenaje"); st.progress(porcentaje_au / 100)
        if porcentaje_au > 60: st.success("✅ Reserva suficiente.")
        elif 30 < porcentaje_au <= 60: st.warning("⚠️ Umbral crítico.")
        else: st.error("🚨 ESTRÉS HÍDRICO.")
        deficit = AGUA_UTIL_MAX - au_hoy
        if deficit > 0: st.write("**Necesidad de Riego:**"); st.code(f"{round(deficit, 1)} mm")

# --- PÁGINA 3: HELADAS ---
else:
    st.title("❄️ Pronóstico de Heladas Agrometeorológicas")
    st.info("Detección de riesgo de helada a nivel de cultivo (Mínimas ≤ 3°C).")
    pronostico = obtener_pronostico_semanal()
    for dia in pronostico:
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 2, 2])
            riesgo, color, msg = "Sin Riesgo", "gray", "Condiciones estables."
            if dia['t_min'] <= 0: riesgo, color, msg = "HELADA METEOROLÓGICA", "red", "Riesgo extremo de congelamiento."
            elif dia['t_min'] <= 3: riesgo, color, msg = "HELADA AGROMETEOROLÓGICA", "orange", "Riesgo de daño en tejidos a nivel de suelo."
            
            c1.subheader(dia['fecha'])
            c2.markdown(f"Mín: **{dia['t_min']}°C** | Máx: **{dia['t_max']}°C**")
            c2.caption(f"Tipo probable: {'Blanca' if dia['hum'] > 60 else 'Negra (Seca)'}")
            c3.markdown(f"<p style='color:{color}; font-weight:bold; font-size:18px;'>{riesgo}</p>", unsafe_allow_html=True)
            c3.write(msg)