import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import json
import os


# ================= CONFIGURACIÓN GENERAL =================
st.set_page_config(
    page_title="AgroGuardian 24/7",
    layout="wide",
    page_icon="🚜"
)

# ================= DATOS BASE =================
LAT, LON = -38.298, -58.208
API_KEY = st.secrets.get("OPENWEATHER_API_KEY")
BITACORA_JSON = "bitacora_campo.json"

st.header("📖 Bitácora de Campo (desde Telegram)")

if os.path.exists(BITACORA_JSON):
    with open(BITACORA_JSON, "r", encoding="utf-8") as f:
        bitacora = json.load(f)

    for uid, eventos in bitacora.items():
        with st.expander(f"👤 Usuario {uid}"):
            for e in reversed(eventos[-20:]):
                st.markdown(
                    f"**{e['fecha']}** | 🌾 {e['lote']} | 🌱 {e['cultivo']}  \n"
                    f"_{e['tipo']}_ → {e['detalle']}"
                )
else:
    st.info("Aún no hay eventos registrados desde el bot.")

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

@st.cache_data(ttl=600)
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

# ================= DATOS INICIALES =================
clima = traer_datos_pro(LAT, LON)

# ================= SIDEBAR =================
with st.sidebar:
    st.markdown("""
    <div style="background:#26A69A;padding:12px;border-radius:10px;color:white;text-align:center">
        <h3> AGROGUARDIAN</h3>
        <small>Sistema activo 24/7</small>
    </div>

    
<style>
    /* Contenedor principal para asegurar que ocupen todo el ancho */
    div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 0px;
    }

    /* Menú lateral: pastillas uniformes y alineadas */
    div[role="radiogroup"] > label {
        display: flex;
        align-items: center;
        width: 100%;              /* Obliga a todas a medir lo mismo (el ancho del sidebar) */
        box-sizing: border-box;   /* Asegura que el padding no afecte el ancho total */
        padding: 2px 12px;        /* Altura baja */
        border-radius: 10px;
        margin-bottom: 8px;
        font-weight: 600;
        font-size: 14px;
        cursor: pointer;
        color: white;
        background: linear-gradient(to bottom, #a8e6a2, #4caf50);
        transition: all 0.2s ease;
    }

    /* Espaciado del texto respecto al botón circular */
    div[role="radiogroup"] > label div:first-child {
        margin-right: 10px;
    }

    /* Hover y Estado Activo */
    div[role="radiogroup"] > label:hover {
        background: linear-gradient(to bottom, #b4f0b0, #57b657);
    }

    div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(to bottom, #4caf50, #2e7d32);
    }
</style> 
 
    """, unsafe_allow_html=True)

    menu = st.radio(
        "MENÚ",
        ["📊 Monitoreo Total", "💧 Balance Hídrico", "⛈️ Radar Granizo", "❄️ Heladas", "📝 Bitácora"],
        index=0,
        label_visibility="collapsed"
    )

    if st.button("🔄 Actualizar"):
        st.rerun()

# ================= PÁGINAS =================
# ---------- MONITOREO TOTAL ----------
if menu == "📊 Monitoreo Total":
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #26A69A, #00897B);
        padding: 20px 40px;
        border-radius: 50px; /* Bordes muy redondeados tipo pastilla */
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    ">
        <h1 style="color: white; margin: 0; padding: 0; font-size: 28px;">🚜 AgroGuardian 24/7</h1>
        <p style="color: white; margin: 5px 0 0 0; opacity: 0.9; font-size: 16px;">Monitoreo Inteligente del agroclima</p>
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

# ---------- RESTO DE LAS PÁGINAS (Balance Hídrico, Radar Granizo, Heladas, Bitácora) ----------
# ... tu código existente sigue aquí, sin cambios
# Esto asegura que todo funcione igual que antes


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
    st.title("⛈️ Riesgo de granizo")

    # --- Cálculo de riesgo simple basado en clima actual ---
    riesgo = 0
    if clima["presion"] < 1010: riesgo += 30
    if clima["hum"] > 70: riesgo += 30
    if clima["temp"] > 28: riesgo += 40

    nivel = "BAJO" if riesgo < 40 else "MODERADO" if riesgo < 75 else "ALTO"
    st.metric("Riesgo agrometeorológico", nivel)

    # --- Botón a Windy ---
    windy_link = f"https://www.windy.com/-Radar-radar?radar,{LAT},{LON},8"
    st.markdown(f"""
    <div style="display:flex;justify-content:center;margin-top:15px">
        <a href="{windy_link}" target="_blank"
        style="background:#2563eb;color:white;padding:18px 34px;
        border-radius:14px;font-weight:700;text-decoration:none;">
        🌧️ Abrir mapa de granizo Windy
        </a>
    </div>
    <p style="text-align:center;color:#555;font-size:0.85rem">
    Se abre en una nueva pestaña (recomendado)
    </p>
    """, unsafe_allow_html=True)

    # --- Consejos de acción ---
    st.subheader("💡 Recomendaciones para el productor")
    if nivel == "ALTO":
        st.warning("""
        🚨 **ALTO riesgo de granizo**
        - Revisar seguros de cultivos.
        - Proteger invernaderos y coberturas.
        - Evitar tareas de campo en parcelas expuestas.
        """)
    elif nivel == "MODERADO":
        st.info("""
        ⚠️ **Riesgo moderado**
        - Vigilar radar en las próximas horas.
        - Preparar medidas preventivas.
        """)
    else:
        st.success("✅ Riesgo bajo. Condiciones estables.")
# ---------- HELADAS ----------
elif menu == "❄️ Heladas":
    st.title("❄️ Riesgo de Heladas")

    # --- Pronóstico 24-48h para temperatura mínima ---
    try:
        pronos = requests.get(
            f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es",
            timeout=5
        ).json()
        temp_min_48h = min([i["main"]["temp_min"] for i in pronos["list"][:16]])  # 16*3h=48h
    except:
        temp_min_48h = clima["temp"]

    # --- Índice de riesgo general agrometeorológico ---
    riesgo = "BAJO"
    if temp_min_48h <= 0: riesgo = "ALTO"
    elif temp_min_48h <= 2: riesgo = "MODERADO"

    st.metric("Riesgo agrometeorológico (24-48h)", riesgo, f"{temp_min_48h} °C")

    # --- Botón a mapa de temperaturas mínimas de Windy ---
    windy_link = f"https://www.windy.com/-Temperature-temperature?temp,slp,{LAT},{LON},4"
    st.markdown(f"""
    <div style="display:flex;justify-content:center;margin-top:15px">
        <a href="{windy_link}" target="_blank"
        style="background:#2563eb;color:white;padding:18px 34px;
        border-radius:14px;font-weight:700;text-decoration:none;">
        ❄️ Abrir mapa de temperatura Windy
        </a>
    </div>
    <p style="text-align:center;color:#555;font-size:0.85rem">
    Se abre en una nueva pestaña (recomendado)
    </p>
    """, unsafe_allow_html=True)

    # --- Consejos de acción ---
    st.subheader("💡 Recomendaciones para el productor")
    if riesgo == "ALTO":
        st.warning("""
        🚨 **ALTO riesgo de helada**
        - Activar sistemas de riego anti-helada.
        - Cubrir cultivos sensibles.
        - Evitar actividades de cosecha y siembra.
        """)
    elif riesgo == "MODERADO":
        st.info("""
        ⚠️ **Riesgo moderado**
        - Monitorear temperatura mínima en la madrugada.
        - Preparar medidas preventivas.
        """)
    else:
        st.success("✅ Riesgo bajo. Condiciones estables.")

    # --- HISTÓRICO + PRONÓSTICO GRÁFICO ---
    st.subheader("📈 Histórico y pronóstico de temperaturas mínimas")

    import pandas as pd
    import matplotlib.pyplot as plt

    # Histórico de 7 días (simulado o desde estación si disponible)
    fechas_hist = pd.date_range(end=pd.Timestamp.today(), periods=7)
    temps_hist = [clima["temp"] - i for i in range(7,0,-1)]  # simulado

    # Pronóstico 2 días
    fechas_fut = [pd.Timestamp.today() + pd.Timedelta(hours=3*i) for i in range(16)]
    temps_fut = [i["main"]["temp_min"] for i in pronos["list"][:16]] if "list" in pronos else [clima["temp"]]*16

    df_hist = pd.DataFrame({"Fecha": fechas_hist, "Temp_min": temps_hist})
    df_fut = pd.DataFrame({"Fecha": fechas_fut, "Temp_min": temps_fut})

    plt.figure(figsize=(10,4))
    plt.plot(df_hist["Fecha"], df_hist["Temp_min"], marker="o", label="Histórico")
    plt.plot(df_fut["Fecha"], df_fut["Temp_min"], marker="x", linestyle="--", color="red", label="Pronóstico 48h")
    plt.axhline(0, color="blue", linestyle=":", label="Cero °C")
    plt.title("Temperaturas mínimas - Histórico vs Pronóstico")
    plt.xlabel("Fecha")
    plt.ylabel("°C")
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.legend()
    st.pyplot(plt)


import json
import os
import datetime
import streamlit as st

BITACORA_JSON = "bitacora_campo.json"

# ---------- BITÁCORA ----------
if menu == "📝 Bitácora":
    st.title("📝 Bitácora de eventos agroclimáticos")

    BITACORA_JSON = os.path.join(os.path.dirname(__file__), "bitacora_campo.json")

    # Cargar bitácora desde archivo si existe
    if os.path.exists(BITACORA_JSON):
        with open(BITACORA_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    # Para simplificar, mostrar todas las entradas de todos los usuarios
    bitacora_total = []
    for chat_id, eventos in data.items():
        for e in eventos:
            bitacora_total.append({
                "fecha": e["fecha"],
                "lote": e.get("lote", "No definido"),
                "cultivo": e.get("cultivo", "No definido"),
                "detalle": e["detalle"]
            })

    # Mostrar en la app
    if bitacora_total:
        for item in reversed(bitacora_total):
            st.markdown(f"- **{item['fecha']}** | Lote: {item['lote']} | Cultivo: {item['cultivo']} | {item['detalle']}")
    else:
        st.info("No hay eventos registrados todavía.")
