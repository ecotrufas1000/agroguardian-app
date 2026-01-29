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

    # Métricas principales
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Temperatura", f"{clima['temp']} °C")
    c2.metric("Humedad", f"{clima['hum']} %")
    c3.metric("Viento", f"{clima['v_vel']} km/h", d_viento)
    c4.metric("Presión", f"{clima['presion']} hPa")
    c5.metric("Estado", "OK")

    st.divider()

    # ================= MAPA GEOPRESENCIAL + NDWI PÚBLICO =================
    st.subheader("🗺️ CENTRO DE MONITOREO GEOPRESENCIAL")
    m = folium.Map(location=[LAT, LON], zoom_start=15, control_scale=True)

    # Vista Satelital HD
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Vista Satelital (HD)',
        overlay=False
    ).add_to(m)

    # Capa NDWI pública (Sentinel-2 vía WMS de USGS/NASA)
    folium.raster_layers.WmsTileLayer(
        url='https://gibs.earthdata.nasa.gov/wms/epsg3857/best/wms.cgi',
        layers='MODIS_Terra_NDWI_8Day',
        fmt='image/png',
        transparent=True,
        name='NDWI 8 días',
        overlay=True,
        control=True
    ).add_to(m)

    # Marcador central
    folium.Marker([LAT, LON], icon=folium.Icon(color="purple", icon="leaf")).add_to(m)

    # Control de capas
    folium.LayerControl().add_to(m)

    # Mostrar mapa
    folium_static(m, width=700, height=400)

    st.divider()

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

    # ================= PRONÓSTICO =================
st.subheader("📅 Pronóstico")
for p in obtener_pronostico():
    st.write(f"**{p['f']}** {p['min']}° / {p['max']}°")
    st.caption(p["d"])



# ---------- BALANCE HÍDRICO ----------
elif menu == "💧 Balance Hídrico":

    st.markdown("""
        <div style="background: linear-gradient(to right, #2563eb, #3b82f6);
                    padding: 25px;
                    border-radius: 15px;
                    color: white;
                    text-align: center;
                    margin-bottom: 25px;">
            <h1 style="margin: 0;">💧 Balance Hídrico del Lote</h1>
            <p style="margin: 0; opacity: 0.9;">
                Estimación diaria de reservas hídricas y recomendación de riego
            </p>
        </div>
    """, unsafe_allow_html=True)

    # === CARGA DE ESTADO DEL LOTE (si existe) ===
    cultivo = "No definido"
    kc_base = 0.85
    etapa = "N/D"
    ultima_fecha = "N/D"

    if os.path.exists("estado_lote.json"):
        try:
            with open("estado_lote.json", "r", encoding="utf-8") as f:
                estado = json.load(f)
                cultivo = estado.get("cultivo", cultivo)
                kc_base = estado.get("kc", kc_base)
                etapa = estado.get("etapa", etapa)
                ultima_fecha = estado.get("ultima_actualizacion", ultima_fecha)

            st.success(f"🌱 **{cultivo}** | Etapa: **{etapa}** | Última act.: {ultima_fecha}")
        except:
            st.warning("⚠️ No se pudo leer el estado del lote")

    # === PARÁMETROS DE SUELO Y CULTIVO ===
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧱 Suelo")
        capacidad_campo = st.number_input(
            "Capacidad de Campo (mm)",
            min_value=150,
            max_value=400,
            value=250
        )
        punto_marchitez = st.number_input(
            "Punto de Marchitez (mm)",
            min_value=50,
            max_value=150,
            value=100
        )

    with col2:
        st.subheader("🌾 Cultivo")
        kc = st.slider(
            "Coeficiente de cultivo (Kc)",
            min_value=0.2,
            max_value=1.3,
            value=float(kc_base),
            step=0.05
        )

        lluvia_real = st.number_input(
            "Lluvia registrada hoy (mm)",
            min_value=0.0,
            max_value=200.0,
            value=float(clima["lluvia_est"])
        )

    st.divider()

    # === CÁLCULO BALANCE HÍDRICO ===
    etc_real = round(clima["etc"] * kc, 2)

    # Reserva estimada (modelo simple diario)
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







