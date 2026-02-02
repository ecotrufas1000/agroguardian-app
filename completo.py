import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import datetime
import pandas as pd
import matplotlib.pyplot as plt

# ================= CONFIGURACIÓN GENERAL =================
st.set_page_config(
    page_title="AgroGuardian 24/7",
    layout="wide",
    page_icon="🚜"
)

# ----------------- ESTILO GLOBAL -----------------
st.markdown("""
<style>
/* Fondo de la app */
.main {
    background-color: #a8e6a2;  /* Verde menta */
    color: white;
}

/* Estilo de las métricas */
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

/* Sidebar padding */
.css-1d391kg {
    padding-top: 1rem;
}

/* Radio buttons estilo menú lateral */
div[role="radiogroup"] > label {
    display: block;
    background: linear-gradient(to bottom, #a8e6a2, #4caf50);
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
    font-weight: 600;
    color: white;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: center;
}

/* Hover */
div[role="radiogroup"] > label:hover {
    background: linear-gradient(to bottom, #b4f0b0, #57b657);
}

/* Estado activo seleccionado */
div[role="radiogroup"] > label[data-baseweb="true"][aria-checked="true"] {
    background: linear-gradient(to bottom, #4caf50, #2e7d32);
    color: white;
}
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR INTERACTIVO -----------------
with st.sidebar:
    st.markdown("""
    <div style="
        background: linear-gradient(to bottom, #4caf50, #2e7d32);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        color: white;
        font-weight: bold;
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        margin-bottom: 20px;
    ">
        <h2>🛡️ AGROGUARDIAN</h2>
        <small>Sistema activo 24/7</small>
    </div>
    """, unsafe_allow_html=True)

    menu_items = ["📊 Monitoreo Total", "💧 Balance Hídrico", "⛈️ Radar Granizo", "❄️ Heladas", "📝 Bitácora"]
    menu = st.radio("", menu_items, index=0, label_visibility="collapsed")

# ================= DATOS BASE =================
LAT, LON = -38.298, -58.208
API_KEY = st.secrets.get("OPENWEATHER_API_KEY")

if not API_KEY:
    st.error("❌ Falta configurar la API Key de OpenWeather")
    st.stop()

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

    st.subheader("🗺️ CENTRO DE MONITOREO GEOPRESENCIAL")
    m = folium.Map(location=[LAT, LON], zoom_start=15, control_scale=True)

    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Vista Satelital (HD)',
        overlay=False
    ).add_to(m)

    folium.raster_layers.WmsTileLayer(
        url='https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi',
        layers='MODIS_Terra_NDWI_8Day',
        fmt='image/png',
        transparent=True,
        name='NDWI 8 días',
        overlay=True,
        control=True
    ).add_to(m)

    folium.Marker([LAT, LON], icon=folium.Icon(color="purple", icon="leaf")).add_to(m)
    folium.LayerControl().add_to(m)
    folium_static(m, width=700, height=400)

    st.subheader("📅 Pronóstico")
    for p in obtener_pronostico():
        st.write(f"**{p['f']}** {p['min']}° / {p['max']}°")
        st.caption(p["d"])

# ---------- BALANCE HÍDRICO ----------
elif menu == "💧 Balance Hídrico":
    st.title("💧 Balance Hídrico")

    capacidad_campo = st.number_input("Capacidad de campo (mm)", 0.0, 200.0, 100.0)
    punto_marchitez = st.number_input("Punto de marchitez (mm)", 0.0, 200.0, 40.0)
    kc = st.number_input("Coeficiente cultural (Kc)", 0.0, 2.0, 1.0)
    lluvia_real = st.number_input("Lluvia estimada (mm)", 0.0, 200.0, float(clima["lluvia_est"]))

    etc_real = round(clima["etc"] * kc, 2)
    reserva_inicial = (capacidad_campo + punto_marchitez) / 2
    reserva_actual = max(
        punto_marchitez,
        min(capacidad_campo, reserva_inicial + lluvia_real - etc_real)
    )
    agua_util_pct = int(
        ((reserva_actual - punto_marchitez) /
         (capacidad_campo - punto_marchitez)) * 100
    )

    colg1, colg2 = st.columns([1, 2])
    with colg1:
        color = (
            "#16a34a" if agua_util_pct > 55
            else "#f59e0b" if agua_util_pct > 35
            else "#dc2626"
        )
        st.markdown(f"""
            <div style="background:white;
                        padding:25px;
                        border-radius:18px;
                        text-align:center;
                        box-shadow:0 4px 10px rgba(0,0,0,0.08);">
                <p style="margin:0; color:#666;">AGUA ÚTIL</p>
                <h1 style="margin:0; font-size:52px; color:{color};">
                    {agua_util_pct}%
                </h1>
            </div>
        """, unsafe_allow_html=True)
    with colg2:
        st.subheader("📊 Resumen diario")
        st.metric("ET₀", f"{clima['etc']} mm/día")
        st.metric("ETc (real)", f"{etc_real} mm/día")
        st.metric("Lluvia", f"{lluvia_real} mm")

# ---------- RADAR GRANIZO ----------
elif menu == "⛈️ Radar Granizo":
    st.title("⛈️ Riesgo de granizo")
    riesgo = 0
    if clima["presion"] < 1010: riesgo += 30
    if clima["hum"] > 70: riesgo += 30
    if clima["temp"] > 28: riesgo += 40
    nivel = "BAJO" if riesgo < 40 else "MODERADO" if riesgo < 75 else "ALTO"
    st.metric("Riesgo agrometeorológico", nivel)

# ---------- HELADAS ----------
elif menu == "❄️ Heladas":
    st.title("❄️ Riesgo de Heladas")

# ---------- BITÁCORA ----------
elif menu == "📝 Bitácora":
    st.title("📝 Bitácora de eventos agroclimáticos")
    if "bitacora" not in st.session_state:
        st.session_state["bitacora"] = []

    with st.form("agregar_evento"):
        evento = st.text_area("Registrar un evento o comentario", "")
        submitted = st.form_submit_button("Agregar")
        if submitted and evento.strip() != "":
            st.session_state["bitacora"].append({
                "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "evento": evento
            })
            st.success("✅ Evento agregado a la bitácora")

    if st.session_state["bitacora"]:
        for item in reversed(st.session_state["bitacora"]):
            st.markdown(f"- **{item['fecha']}**: {item['evento']}")





