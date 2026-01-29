import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import json
import os
import datetime

# ================= CONFIGURACIÓN GENERAL =================
st.set_page_config(
    page_title="AgroGuardian 24/7",
    layout="wide",
    page_icon="🚜"
)

st.markdown("""
<style>
.main { background-color: #f4f7f6; }
[data-testid="stMetric"] {
    background: white;
    border-radius: 12px;
    padding: 15px !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    border: none !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: bold;
    color: #1e3d2f;
}
</style>
""", unsafe_allow_html=True)

# ================= DATOS BASE =================
LAT, LON = -38.298, -58.208
API_KEY = st.secrets["OPENWEATHER_API_KEY"]  # OpenWeather (NO Windy)

# ================= FUNCIONES =================
def obtener_direccion_cardinal(grados):
    direcciones = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
                   "S","SSO","SO","OSO","O","ONO","NO","NNO"]
    return direcciones[int((grados + 11.25) / 22.5) % 16]

@st.cache_data(ttl=600)
def traer_datos_pro(lat, lon):
    datos = {
        "temp": 0.0, "hum": 0, "presion": 1013,
        "v_vel": 0.0, "v_dir": 0,
        "etc": 4.0, "lluvia_est": 0.0
    }
    try:
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es",
            timeout=5
        ).json()

        if "main" in r:
            datos["temp"] = r["main"]["temp"]
            datos["hum"] = r["main"]["humidity"]
            datos["presion"] = r["main"]["pressure"]
            datos["v_vel"] = round(r["wind"]["speed"] * 3.6, 1)
            datos["v_dir"] = r["wind"]["deg"]
    except:
        pass
    return datos

def obtener_pronostico():
    try:
        r = requests.get(
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es",
            timeout=5
        ).json()

        diario = {}
        for i in r["list"]:
            fecha = i["dt_txt"].split(" ")[0]
            temp = i["main"]["temp"]
            desc = i["weather"][0]["description"]
            if fecha not in diario:
                diario[fecha] = {"min": temp, "max": temp, "desc": desc}
            else:
                diario[fecha]["min"] = min(diario[fecha]["min"], temp)
                diario[fecha]["max"] = max(diario[fecha]["max"], temp)

        dias = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
        salida = []
        for f, v in list(diario.items())[:5]:
            d = datetime.datetime.strptime(f, "%Y-%m-%d")
            salida.append({
                "f": f"{dias[d.weekday()]} {d.day}",
                "min": round(v["min"],1),
                "max": round(v["max"],1),
                "d": v["desc"].capitalize()
            })
        return salida
    except:
        return []

clima = traer_datos_pro(LAT, LON)

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("""
    <div style="background:#1e3d2f;padding:12px;border-radius:10px;color:white;text-align:center">
        <h3>🛡️ AGROGUARDIAN</h3>
        <small>Sistema activo 24/7</small>
    </div>
    """, unsafe_allow_html=True)

    menu = st.radio(
        "MENÚ",
        ["📊 Monitoreo Total", "💧 Balance Hídrico", "⛈️ Radar Granizo", "❄️ Heladas", "📝 Bitácora"]
    )

    if st.button("🔄 Actualizar"):
        st.rerun()

# ================= PÁGINAS =================

# ---------- MONITOREO TOTAL ----------
if menu == "📊 Monitoreo Total":
    st.markdown("""
    <div style="background:linear-gradient(to right,#4c1d95,#7c3aed);
    padding:25px;border-radius:15px;color:white;text-align:center">
    <h1>🚜 AgroGuardian 24/7</h1>
    <p>Centro de inteligencia agroclimática</p>
    </div>
    """, unsafe_allow_html=True)

    d_viento = obtener_direccion_cardinal(clima["v_dir"])

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("Temperatura", f"{clima['temp']} °C")
    c2.metric("Humedad", f"{clima['hum']} %")
    c3.metric("Viento", f"{clima['v_vel']} km/h", d_viento)
    c4.metric("Presión", f"{clima['presion']} hPa")
    c5.metric("Estado", "OK")

    st.divider()

    st.subheader("🌧️ Radar meteorológico")
    windy_link = f"https://www.windy.com/-Radar-radar?radar,{LAT},{LON},8"

    st.markdown(f"""
    <div style="display:flex;justify-content:center;margin-top:25px">
        <a href="{windy_link}" target="_blank"
        style="background:#2563eb;color:white;padding:18px 34px;
        border-radius:14px;font-weight:700;text-decoration:none;">
        🌧️ Abrir radar Windy
        </a>
    </div>
    <p style="text-align:center;color:#555;font-size:0.85rem">
    Se abre en una nueva pestaña (recomendado)
    </p>
    """, unsafe_allow_html=True)

    st.divider()

    col1,col2 = st.columns([2,1])
    with col1:
        m = folium.Map(location=[LAT,LON], zoom_start=14)
        folium.Marker([LAT,LON], tooltip="Lote").add_to(m)
        folium_static(m, width=700, height=400)

    with col2:
        st.subheader("📅 Pronóstico")
        for p in obtener_pronostico():
            st.write(f"**{p['f']}** {p['min']}° / {p['max']}°")
            st.caption(p["d"])

# ---------- BALANCE HÍDRICO ----------
elif menu == "💧 Balance Hídrico":
    st.title("💧 Balance hídrico")
    st.info("Módulo en expansión 🚧")

# ---------- RADAR GRANIZO ----------
elif menu == "⛈️ Radar Granizo":
    st.title("⛈️ Riesgo de granizo")

    riesgo = 0
    if clima["presion"] < 1010: riesgo += 30
    if clima["hum"] > 70: riesgo += 30
    if clima["temp"] > 28: riesgo += 40

    nivel = "BAJO" if riesgo < 40 else "MODERADO" if riesgo < 75 else "ALTO"
    st.metric("Riesgo estimado", nivel)

    st.subheader("🌩️ Radar Windy")
    windy_link = f"https://www.windy.com/-Radar-radar?radar,{LAT},{LON},8"

    st.markdown(f"""
    <div style="display:flex;justify-content:center;margin-top:20px">
        <a href="{windy_link}" target="_blank"
        style="background:#dc2626;color:white;padding:16px 30px;
        border-radius:12px;font-weight:700;text-decoration:none;">
        🚀 Ver radar granizo
        </a>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("❓ Cómo interpretar"):
        st.write("""
        Verde/Amarillo: lluvia  
        Rojo: tormenta fuerte  
        Púrpura/Blanco: posible granizo  
        """)

# ---------- HELADAS ----------
elif menu == "❄️ Heladas":
    st.title("❄️ Alerta de heladas")
    for p in obtener_pronostico():
        if p["min"] <= 0:
            st.error(f"{p['f']} ❄️ Helada ({p['min']}°C)")
        elif p["min"] <= 3:
            st.warning(f"{p['f']} 🌱 Riesgo ({p['min']}°C)")
        else:
            st.success(f"{p['f']} ✅ Sin riesgo")

# ---------- BITÁCORA ----------
elif menu == "📝 Bitácora":
    st.title("📝 Bitácora de campo")
    txt = st.text_area("Observaciones")
    if st.button("Guardar"):
        st.success("Registro guardado")
