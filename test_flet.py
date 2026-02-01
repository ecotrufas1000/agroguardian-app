import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# === CONFIGURACIÓN Y API ===
API_KEY = "2762051ad62d06f1d0fe146033c1c7c8"
LAT, LON = -38.34, -57.98

st.set_page_config(page_title="AgroGuardian Pro", layout="wide")

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("🚜 AgroGuardian")
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2913/2913520.png", width=100)
pagina = st.sidebar.radio("Ir a:", ["📊 Monitoreo General", "💧 Balance Hídrico"])

# --- FUNCIONES COMUNES ---
def obtener_clima():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es"
    try:
        r = requests.get(url, timeout=5).json()
        return {"temp": r['main']['temp'], "hum": r['main']['humidity'], "lluvia": r.get('rain', {}).get('1h', 0)}
    except:
        return {"temp": 25, "hum": 50, "lluvia": 0}

# ==========================================
# PAGINA 1: MONITOREO GENERAL
# ==========================================
if pagina == "📊 Monitoreo General":
    st.title("📊 Monitoreo de Lote")
    # (Aquí va todo el código que ya hicimos: Métricas, Mapa Folium e ITH)
    # ... por brevedad, resumimos la lógica que ya funciona perfecto ...
    st.info("Visualización de Clima, Bienestar Animal y Vigor Vegetal.")
    # [Insertar aquí el bloque de código previo de métricas y mapa]

# ==========================================
# PAGINA 2: BALANCE HÍDRICO
# ==========================================
elif pagina == "💧 Balance Hídrico":
    st.title("💧 Balance Hídrico Operativo")
    st.caption("Estimación de Agua Útil en el perfil del suelo (0-60cm)")

    # Simulamos datos de balance
    agua_util_pct = 65  # 65% de capacidad de campo
    evapotranspiracion = 4.2 # mm/día
    lluvia_semanal = 12.0 # mm acumulados

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Agua Útil (AU)", f"{agua_util_pct}%", delta="-2% (Ayer)")
    with col2:
        st.metric("Evapotranspiración (ETc)", f"{evapotranspiracion} mm/día")
    with col3:
        st.metric("Lluvias (Últ. 7 días)", f"{lluvia_semanal} mm")

    st.divider()

    # Gráfico de la salud del "Tanque de Agua"
    st.write("### 🛢️ Estado del Perfil")
    
    # Creamos una barra de progreso visual
    color_barra = "green" if agua_util_pct > 50 else "orange" if agua_util_pct > 25 else "red"
    st.progress(agua_util_pct / 100)
    st.write(f"El suelo se encuentra al **{agua_util_pct}%** de su capacidad de almacenamiento.")

    # Gráfico de evolución semanal (Simulado)
    st.write("### 📈 Evolución Diaria (Humedad vs Consumo)")
    chart_data = pd.DataFrame(
        np.random.randint(50, 80, size=(7, 2)),
        columns=['Humedad Suelo (%)', 'Consumo Cultivo (mm)']
    )
    st.area_chart(chart_data)

    # Panel de Alerta de Riego
    st.divider()
    if agua_util_pct < 40:
        st.error("🚨 **ALERTA DE ESTRÉS HÍDRICO:** Se recomienda iniciar riego o monitorear marchitez.")
    else:
        st.success("✅ **RESERVA SUFICIENTE:** El perfil tiene agua disponible para los próximos 4-5 días.")

    with st.expander("📝 Configurar Parámetros de Suelo"):
        tipo_suelo = st.selectbox("Tipo de Suelo:", ["Franco", "Franco Arenoso", "Arcilloso"])
        st.slider("Capacidad de Almacenaje (mm):", 50, 200, 140)