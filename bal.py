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

# --- FUNCIONES DE DATOS ---
def obtener_datos_clima():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es"
    try:
        r = requests.get(url, timeout=5).json()
        return {
            "temp": r['main']['temp'],
            "hum": r['main']['humidity'],
            "desc": r['weather'][0]['description'].capitalize()
        }
    except:
        return {"temp": 28, "hum": 60, "desc": "Cielo despejado"}

def calcular_ith(temp, hum):
    t_f = (1.8 * temp) + 32
    ith = t_f - (0.55 - 0.55 * (hum / 100)) * (t_f - 58)
    return round(ith, 1)

# === 2. BARRA LATERAL (NAVEGACIÓN) ===
with st.sidebar:
    st.title("🚜 AgroGuardian")
    st.markdown("---")
    # El selector de páginas
    seleccion = st.radio(
        "Navegación:",
        ["📊 Monitoreo de Lote", "💧 Balance Hídrico"],
        index=0
    )
    st.markdown("---")
    st.info(f"**Ubicación:** Miramar, BA\n\n**Coordenadas:** {LAT}, {LON}")

# === 3. LÓGICA DE PÁGINAS ===

# --- PÁGINA 1: MONITOREO ---
if seleccion == "📊 Monitoreo de Lote":
    st.title("📊 Monitoreo de Lote")
    st.info("Visualización de Clima, Bienestar Animal y Vigor Vegetal.")
    
    clima = obtener_datos_clima()
    ith_actual = calcular_ith(clima['temp'], clima['hum'])

    # Métricas
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
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri', name='Satélite Real'
        ).add_to(m)
        folium_static(m, width=700, height=400)

    with col_alertas:
        st.write("### 🐄 Estado Ganadero")
        if ith_actual < 72:
            st.success(f"**ITH: {ith_actual} - CONFORT**")
        elif 72 <= ith_actual < 79:
            st.warning(f"**ITH: {ith_actual} - ALERTA**")
        else:
            st.error(f"**ITH: {ith_actual} - CRÍTICO**")
            
        with st.expander("📊 Ver Tabla ITH"):
            st.table(pd.DataFrame({
                "Rango": ["<72", "72-78", "79-83", ">84"],
                "Estado": ["Confort", "Alerta", "Peligro", "Emergencia"]
            }))

# --- PÁGINA 2: BALANCE HÍDRICO ---
else:
    st.title("💧 Balance Hídrico Operativo")
    st.info("Visualización de Reservas de Agua, Evapotranspiración y Lamina de Riego.")

    # Entradas del usuario
    with st.container(border=True):
        c_in1, c_in2 = st.columns(2)
        with c_in1:
            lluvia = st.number_input("Lluvia registrada (mm):", min_value=0.0, step=1.0)
        with c_in2:
            riego = st.number_input("Riego aplicado (mm):", min_value=0.0, step=1.0)

    # Cálculo simplificado
    etc_estimada = 4.8  #mm/día
    au_ayer = 110.0 #mm
    au_hoy = min(AGUA_UTIL_MAX, max(0, au_ayer + lluvia + riego - etc_estimada))
    porcentaje_au = round((au_hoy / AGUA_UTIL_MAX) * 100, 1)

    # Métricas y Gráficos
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Agua Útil Actual", f"{porcentaje_au}%")
    c2.metric("Consumo (ETc)", f"{etc_estimada} mm")
    c3.metric("Lámina de Agua", f"{round(au_hoy, 1)} mm")

    col_g1, col_g2 = st.columns([2, 1])
    with col_g1:
        st.write("### 📈 Agua en el Suelo")
        df_agua = pd.DataFrame({"Día": ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"], 
                                "Humedad %": [85, 82, 79, 76, 74, 72, porcentaje_au]})
        st.area_chart(df_agua.set_index("Día"), color="#0077b6")
    
    with col_g2:
        st.write("### Almacenaje")
        st.progress(porcentaje_au / 100)
        if porcentaje_au > 60: st.success("Reserva suficiente.")
        else: st.warning("Monitorear riego.")