import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
import numpy as np
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
    # Generamos datos que incluyan algunos extremos para probar la Pág 4
    for i in range(1, 8):
        fecha = fecha_hoy + timedelta(days=i)
        nombre_dia = dias_nombres[fecha.weekday()]
        # Simulación: Días 1-3 calor extremo, Días 5-7 frío extremo
        if i <= 3:
            t_max, t_min = 36.5 + i, 22.0
        else:
            t_max, t_min = 12.0, -1.5 + (i * 0.2)
            
        pronostico.append({
            "fecha": f"{nombre_dia} {fecha.day}",
            "t_min": round(t_min, 1),
            "t_max": round(t_max, 1),
            "icono": "🔥" if t_max > 34 else "❄️" if t_min < 3 else "⛅",
            "hum": 40 if t_max > 34 else 80
        })
    return pronostico

# === 2. BARRA LATERAL (NAVEGACIÓN) ===
with st.sidebar:
    st.title("🚜 AgroGuardian")
    st.markdown("---")
    seleccion = st.radio("Menú de Navegación:", [
        "📊 Monitoreo de Lote", 
        "💧 Balance Hídrico", 
        "❄️ Pronóstico de Heladas",
        "⚠️ Temperaturas Extremas"
    ])
    st.markdown("---")
    st.info(f"**Miramar, BA**\n{LAT}, {LON}")

# === 3. LÓGICA DE PÁGINAS ===

# --- PÁGINA 1: MONITOREO ---
if seleccion == "📊 Monitoreo de Lote":
    st.title("📊 Monitoreo de Lote")
    clima = obtener_datos_clima()
    ith_actual = calcular_ith(clima['temp'], clima['hum'])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temperatura", f"{clima['temp']} °C")
    m2.metric("Humedad", f"{clima['hum']} %")
    m3.metric("Bienestar (ITH)", f"{ith_actual}")
    m4.metric("Vigor (NDVI)", "0.74")
    st.divider()
    c_map, c_alt = st.columns([2, 1])
    with c_map:
        m = folium.Map(location=[LAT, LON], zoom_start=15)
        folium.TileLayer(tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
        folium_static(m, width=700, height=400)
    with c_alt:
        st.write("### 🐄 Estado Ganadero")
        if ith_actual < 72: st.success("CONFORT")
        else: st.error("ALERTA ESTRÉS")
        st.write("### 📅 Pronóstico")
        for d in obtener_pronostico_semanal()[:3]:
            st.write(f"{d['fecha']}: {d['t_min']}° / {d['t_max']}°")

# --- PÁGINA 2: BALANCE HÍDRICO ---
elif seleccion == "💧 Balance Hídrico":
    st.title("💧 Balance Hídrico")
    lluvia = st.number_input("Lluvia (mm):", min_value=0.0)
    riego = st.number_input("Riego (mm):", min_value=0.0)
    st.divider()
    st.metric("Agua Útil Actual", "72%", delta=f"{lluvia} mm")
    st.area_chart(np.random.randn(7, 1) + [70])

# --- PÁGINA 3: HELADAS ---
elif seleccion == "❄️ Pronóstico de Heladas":
    st.title("❄️ Heladas Agrometeorológicas")
    for d in obtener_pronostico_semanal():
        if d['t_min'] <= 3:
            with st.container(border=True):
                st.write(f"**{d['fecha']}** - Mínima esperada: {d['t_min']}°C")
                st.progress(0.8 if d['t_min'] < 0 else 0.4)

# --- PÁGINA 4: TEMPERATURAS EXTREMAS ---
else:
    st.title("⚠️ Temperaturas Extremas")
    st.info("Resumen de alertas por picos térmicos que afectan la fisiología del cultivo y el ganado.")
    
    pro = obtener_pronostico_semanal()
    
    col_calor, col_frio = st.columns(2)
    
    with col_calor:
        st.subheader("🔥 Alerta de Calor")
        for d in pro:
            if d['t_max'] >= 35:
                st.error(f"**{d['fecha']} - Máxima: {d['t_max']}°C**")
                st.caption("Riesgo de golpe de calor y alta evapotranspiración.")
                
    with col_frio:
        st.subheader("🧊 Alerta de Frío")
        for d in pro:
            if d['t_min'] <= 0:
                st.info(f"**{d['fecha']} - Mínima: {d['t_min']}°C**")
                st.caption("Riesgo de daño por congelamiento (Helada Meteorológica).")

    st.divider()
    st.write("### 📊 Histórico Semanal de Amplitud")
    df_ext = pd.DataFrame(pro)
    st.line_chart(df_ext.set_index("fecha")[["t_min", "t_max"]])