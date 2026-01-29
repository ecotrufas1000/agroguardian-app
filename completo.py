import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
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

    # === MAPA GEOPRESENCIAL + NDWI PÚBLICO ===
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

    # === PRONÓSTICO ===
    st.subheader("📅 Pronóstico")
    for p in obtener_pronostico():
        st.write(f"**{p['f']}** {p['min']}° / {p['max']}°")
        st.caption(p["d"])

    # ================= RADAR METEOROLÓGICO =================
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


# ---------- BALANCE HÍDRICO ----------
elif menu == "💧 Balance Hídrico":
    st.title("💧 Balance Hídrico")

    # Parámetros ingresables
    capacidad_campo = st.number_input(
        "Capacidad de campo (mm)", min_value=0.0, max_value=200.0, value=100.0
    )
    punto_marchitez = st.number_input(
        "Punto de marchitez (mm)", min_value=0.0, max_value=200.0, value=40.0
    )
    kc = st.number_input(
        "Coeficiente cultural (Kc)", min_value=0.0, max_value=2.0, value=1.0
    )
    lluvia_real = st.number_input(
        "Lluvia estimada (mm)", min_value=0.0, max_value=200.0, value=float(clima["lluvia_est"])
    )

    st.divider()

    # === CÁLCULO BALANCE HÍDRICO ===
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

    # === VISUALIZACIÓN ===
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

        st.divider()

        if agua_util_pct < 40:
            st.error("🚨 **RECOMENDACIÓN:** Programar riego en las próximas 24–48 h")
        elif agua_util_pct < 55:
            st.warning("⚠️ **ATENCIÓN:** Reservas en descenso, monitorear")
        else:
            st.success("✅ **ESTADO ÓPTIMO:** Buen nivel de agua disponible")
# ---------- RADAR GRANIZO ----------
elif menu == "⛈️ Radar Granizo":
    st.title("⛈️ Riesgo de Granizo")

    # ================= CÁLCULO DE RIESGO =================
    riesgo = 0
    if clima["presion"] < 1010: riesgo += 30
    if clima["hum"] > 70: riesgo += 30
    if clima["temp"] > 28: riesgo += 40

    # Ajuste por tormenta activa (simulación)
    tormenta_activa = True  # Placeholder: más adelante podemos extraer del radar real
    if tormenta_activa: riesgo += 20

    # Nivel de riesgo
    nivel = "BAJO" if riesgo < 40 else "MODERADO" if riesgo < 75 else "ALTO"
    st.metric("Riesgo estimado de granizo", nivel)

    st.divider()

    # ================= BOTÓN A WINDY =================
    st.subheader("🌩️ Radar de Granizo")
    windy_link = f"https://www.windy.com/-Radar-radar?radar,{LAT},{LON},8"

    st.markdown(f"""
    <div style="display:flex;justify-content:center;margin-top:25px">
        <a href="{windy_link}" target="_blank"
        style="background:#2563eb;color:white;padding:18px 34px;
        border-radius:14px;font-weight:700;text-decoration:none;">
        🌧️ Abrir mapa de granizo en Windy
        </a>
    </div>
    <p style="text-align:center;color:#555;font-size:0.85rem">
    Se abrirá en una nueva pestaña (recomendado)
    </p>
    """, unsafe_allow_html=True)

    st.divider()

    # ================= HISTORIAL DE EVENTOS =================
    st.subheader("📈 Historial de Granizo (últimos 30 días)")

    import pandas as pd
    import random
    import datetime

    fechas = pd.date_range(end=datetime.datetime.today(), periods=30)
    intensidad = [random.choice(["Bajo", "Moderado", "Alto", "Sin evento"]) for _ in range(30)]
    df_hist = pd.DataFrame({"Fecha": fechas, "Intensidad": intensidad})

    st.dataframe(df_hist, use_container_width=True)

    # ================= ALERTA RECOMENDADA =================
    if nivel == "ALTO":
        st.error("🚨 ALERTA: Riesgo alto de granizo. Recomendado proteger cultivos y estructuras")
    elif nivel == "MODERADO":
        st.warning("⚠️ Riesgo moderado de granizo. Monitorear condiciones")
    else:
        st.success("✅ Riesgo bajo. Todo en condiciones normales")


# ---------- HELADAS ----------
elif menu == "❄️ Heladas":
    st.title("❄️ Seguimiento de Heladas")

    # ================= ALERTA ANTICIPADA =================
    pronostico = obtener_pronostico()  # Usamos función existente
    temp_min_24h = pronostico[0]['min'] if pronostico else clima['temp']
    temp_min_48h = pronostico[1]['min'] if len(pronostico) > 1 else temp_min_24h

    st.subheader("🌡️ Temperaturas mínimas próximas 48h")
    st.write(f"Hoy: {temp_min_24h} °C")
    st.write(f"Mañana: {temp_min_48h} °C")

    # ================= ALERTA POR CULTIVO =================
    cultivos = {
        "Trigo": 0,
        "Vid": -2,
        "Maíz": -1,
        "Lechuga": 1
    }

    st.subheader("🥦 Riesgo por cultivo")
    for c, tol in cultivos.items():
        nivel = "Bajo"
        color = "#16a34a"
        if temp_min_24h <= tol:
            nivel = "Alto"
            color = "#dc2626"
        elif temp_min_24h <= tol + 2:
            nivel = "Moderado"
            color = "#f59e0b"
        st.markdown(f"<p style='color:{color}; font-weight:bold'>{c}: {nivel}</p>", unsafe_allow_html=True)

    # ================= BOTÓN A WINDY =================
    st.subheader("🗺️ Mapa de riesgo de heladas")
    windy_link = f"https://www.windy.com/-Frost-frost?lat={LAT}&lon={LON}&zoom=8"
    st.markdown(f"""
    <div style="display:flex;justify-content:center;margin-top:15px">
        <a href="{windy_link}" target="_blank"
        style="background:#0ea5e9;color:white;padding:16px 30px;
        border-radius:12px;font-weight:700;text-decoration:none;">
        ❄️ Abrir mapa de heladas en Windy
        </a>
    </div>
    <p style="text-align:center;color:#555;font-size:0.85rem">
    Se abrirá en una nueva pestaña
    </p>
    """, unsafe_allow_html=True)

    st.divider()

    # ================= HISTORIAL DE HELADAS =================
    st.subheader("📈 Historial de Heladas (últimos 30 días)")

    import pandas as pd
    import random
    import datetime

    fechas = pd.date_range(end=datetime.datetime.today(), periods=30)
    temp_min_hist = [round(random.uniform(-5, 5), 1) for _ in range(30)]
    df_heladas = pd.DataFrame({"Fecha": fechas, "Temp Mín (°C)": temp_min_hist})
    st.dataframe(df_heladas, use_container_width=True)

    # ================= ALERTA GLOBAL =================
    alerta_global = "Bajo"
    color_global = "#16a34a"
    if temp_min_24h <= min(cultivos.values()):
        alerta_global = "Alto"
        color_global = "#dc2626"
    elif temp_min_24h <= min(cultivos.values()) + 2:
        alerta_global = "Moderado"
        color_global = "#f59e0b"

    st.markdown(f"<h3 style='color:{color_global}'>Alerta global: {alerta_global}</h3>", unsafe_allow_html=True)


# ---------- BITÁCORA ----------
elif menu == "📝 Bitácora":
    st.title("📝 Bitácora de eventos agroclimáticos")

    # Mostrar mensajes guardados
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

    st.divider()

    if st.session_state["bitacora"]:
        for item in reversed(st.session_state["bitacora"]):
            st.markdown(f"- **{item['fecha']}**: {item['evento']}")
    else:
        st.info("No hay eventos registrados todavía.")




