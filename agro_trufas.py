import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
import json
import os
import datetime

# === CONFIGURACIÓN Y ESTILO COMPACTO ===
st.set_page_config(page_title="AgroGuardian Pro Trufas", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    .main { background-color: #f8f9f6; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; } 
    [data-testid="stMetricLabel"] { font-size: 0.75rem !important; }
    div.stMarkdown p { font-size: 0.85rem; }
    .stMetric { 
        background-color: #ffffff; padding: 8px; 
        border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
    }
    div[data-testid="stSidebar"] { background-color: #1e3d2f; }
    h1, h2, h3 { color: #1e3d2f; margin-bottom: 0.5rem; }
    </style>
    """, unsafe_allow_html=True)

# === 1. LÓGICA DE DATOS ===
API_KEY = "2762051ad62d06f1d0fe146033c1c7c8"

def cargar_ubicacion():
    if os.path.exists('usuarios.json'):
        try:
            with open('usuarios.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data:
                    ultimo_id = list(data.keys())[-1]
                    return data[ultimo_id]['lat'], data[ultimo_id]['lon']
        except: pass
    return -38.298, -58.208 

LAT, LON = cargar_ubicacion()

def obtener_datos():
    d = {"temp": 0.0, "hum": 0, "presion": 1013, "v_vel": 0.0, "v_dir": 0, "tpw": 0.0, "etc": 4.0, "lluvia_est": 0.0}
    try:
        r_ow = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=es", timeout=5).json()
        if 'main' in r_ow:
            d.update({"temp": r_ow['main']['temp'], "hum": r_ow['main']['humidity'], "presion": r_ow['main']['pressure'], 
                      "v_vel": round(r_ow['wind']['speed']*3.6, 1), "v_dir": r_ow['wind']['deg']})
        r_om = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&hourly=precipitable_water,et0_fao_evapotranspiration,precipitation&timezone=auto", timeout=5).json()
        if 'hourly' in r_om:
            d.update({"tpw": r_om['hourly']['precipitable_water'][0], "etc": r_om['hourly']['et0_fao_evapotranspiration'][0] or 4.0, "lluvia_est": r_om['hourly']['precipitation'][0]})
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

clima = obtener_datos()

# === 2. BARRA LATERAL ===
with st.sidebar:
    st.title("AgroGuardian Pro Trufas")
    menu = st.radio("SECCIONES", ["📊 Monitoreo", "💧 Balance Hídrico", "⛈️ Granizo", "❄️ Heladas", "📝 Bitácora", "🌡️Temp. del Suelo"])
    st.divider()
    st.caption(f"📍 {round(LAT,3)}, {round(LON,3)}")
    if st.button("🔄 ACTUALIZAR"): st.rerun()
# === 3. PÁGINA: MONITOREO ===
if menu == "📊 Monitoreo":
    # --- ENCABEZADO PROFESIONAL ---
    st.markdown("""
        <div style="background: linear-gradient(to right, #1e3d2f, #2ecc71); padding: 25px; border-radius: 15px; margin-bottom: 20px; color: white; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 2.2rem;"> 💎 AgroGuardian Pro Trufas</h1>
            <p style="margin: 0; opacity: 0.9; font-size: 1.1rem; font-weight: 300;">Tu asistente profesional de monitoreo y decisiones agroclimáticas</p>
        </div>
    """, unsafe_allow_html=True)

    # --- LÓGICA DE ALERTAS ---
    riesgo_granizo = 0
    if clima['presion'] < 1010: riesgo_granizo += 30
    if clima['tpw'] > 30: riesgo_granizo += 30
    if clima['v_vel'] > 25: riesgo_granizo += 20
    
    t_color = "normal" if clima['temp'] < 32 else "inverse"
    v_color = "off" if clima['v_vel'] < 18 else "normal"

    if riesgo_granizo >= 50:
        st.error(f"⚠️ **ALERTA DE TORMENTA:** El riesgo de granizo es del **{riesgo_granizo}%**. Revisa la sección de Granizo para ver el Radar.")

    # Fila de métricas
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("TEMP.", f"{clima['temp']}°C", delta="Calor" if clima['temp'] > 32 else None, delta_color=t_color)
    m2.metric("HUMEDAD", f"{clima['hum']}%")
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    m3.metric("VIENTO", f"{clima['v_vel']} km/h", delta="Fuerte" if clima['v_vel'] > 18 else None, delta_color=v_color)
    m4.metric("DIRECCIÓN", dirs[int((clima['v_dir'] + 22.5) / 45) % 8])
    m5.metric("PRECIPITACION", f"{clima['tpw']} mm")

    st.divider()
    
    # --- MAPA MULTICAPA Y BIENESTAR ---
    c1, c2 = st.columns([2, 1])
    with c1:
        st.caption("🗺️ CENTRO DE MONITOREO GEOPRESENCIAL")
        m = folium.Map(location=[LAT, LON], zoom_start=15, control_scale=True)
        
        # Capa Satelital
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri', name='Vista Satelital', overlay=False
        ).add_to(m)

        # Capa de Relieve
        folium.TileLayer(
            tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
            attr='OpenTopoMap', name='Relieve y Altura', overlay=True, opacity=0.4
        ).add_to(m)

        folium.Marker([LAT, LON], icon=folium.Icon(color="green", icon="leaf")).add_to(m)
        folium.LayerControl().add_to(m)
        folium_static(m, width=700, height=350)
        st.info("💡 Usa el icono de capas arriba a la derecha del mapa para alternar vistas.")
        
        st.caption("📅 PRONÓSTICO CORTO")
        pronos = obtener_pronostico()
        for p in pronos[:3]:
            st.write(f"**{p['f']}:** {p['min']}°/{p['max']}° - {p['d']}")


elif menu == "💧 Balance Hídrico":
    st.header("💧 Balance Hídrico Especializado - Trufera")
    st.write("Cálculo optimizado para **Roble y Encina**.")

    # Eliminamos el selectbox de cultivos y fijamos el Kc
    cultivo_seleccionado = "Roble/Encina"
    kc_fijo = 1.0  # El Kc que me pediste
    
    st.info(f"🌳 **Configuración Activa:** {cultivo_seleccionado} (Kc fijo: {kc_fijo})")

   # Cálculo de ETc (Consumo total) y Riego Técnico (50%)
    etc_trufa = round(clima['etc'] * kc_fijo, 2)
    riego_tecnico = round(etc_trufa * 0.5, 2) # REGLA DEL 50%
    
    st.info(f"🌳 **Estrategia:** Reposición del 50% de la ETc para mantener humedad.")

    if etc_trufa > clima['lluvia_est']:
        # El riego sugerido ahora es la mitad de la ETc menos lo que haya llovido
        sug_riego_final = max(0.0, riego_tecnico - clima['lluvia_est'])
        st.write(f"📢 **Sugerencia de Riego:** Aplicar **{sug_riego_final} mm** (50% de la ETc diaria).")
    st.divider()

    # --- LÓGICA DE BALANCE SIMPLIFICADA ---
    st.subheader("📊 Estado de Reservas en el Quemado")
    
    # Simulamos el balance hídrico
    balance_diario = round(clima['lluvia_est'] - etc_trufa, 2)
    
    if balance_diario >= 0:
        st.success(f"Balance hoy: +{balance_diario} mm. Las reservas se mantienen.")
    else:
        st.warning(f"Balance hoy: {balance_diario} mm. El nido está perdiendo humedad.")

    # Sugerencia de riego basada solo en Roble/Encina
    if etc_trufa > clima['lluvia_est']:
        riego_necesario = etc_trufa - clima['lluvia_est']
        st.write(f"📢 **Sugerencia:** Para reponer el consumo de hoy, aplicar **{round(riego_necesario, 1)} mm** de riego.")

  # === SECCIÓN: EXPORTACIÓN DE DATOS (VERSIÓN TRUFERA) ===
elif menu == "📊 Monitoreo": # O puedes ponerlo dentro de la sección que prefieras
    # ... (tu código de monitoreo actual) ...
    
    st.divider()
    st.subheader("📥 Exportar Datos de la Trufera")
    
    # Creamos un DataFrame con los datos actuales para descargar
    datos_export = pd.DataFrame({
        'Fecha': [datetime.now().strftime("%Y-%m-%d %H:%M")],
        'Lote/Sector': ["Trufera Principal"],
        'Especie': ["Roble/Encina"],
        'Temperatura Aire (°C)': [clima['temp']],
        'Humedad (%)': [clima['hum']],
        'Temp. Suelo Est. (°C)': [t_suelo_est if 't_suelo_est' in locals() else "N/A"],
        'ETc Diario (mm)': [etc_trufa if 'etc_trufa' in locals() else "N/A"],
        'Precipitación Est. (mm)': [clima['lluvia_est']]
    })

    # Botón de descarga
    csv = datos_export.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Descargar Reporte Técnico (CSV)",
        data=csv,
        file_name=f"reporte_trufero_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
elif menu == "⛈️ Granizo":
    st.title("⛈️ Alerta de Granizo y Tormentas")
    
    riesgo = 0
    if clima['presion'] < 1010: riesgo += 30
    if clima['hum'] > 80: riesgo += 20
    if clima['tpw'] > 30: riesgo += 30
    if clima['v_vel'] > 25: riesgo += 20
    
    color_riesgo = "#2ecc71" if riesgo < 40 else "#f1c40f" if riesgo < 70 else "#e74c3c"
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"""
            <div style="background:{color_riesgo}; padding:30px; border-radius:15px; text-align:center; color:white;">
                <h3 style="margin:0; color:white;">Probabilidad de Tormenta</h3>
                <h1 style="margin:0; font-size:80px; color:white;">{riesgo}%</h1>
            </div>
        """, unsafe_allow_html=True)
    
    with c2:
        st.subheader("📡 Monitoreo Doppler")
        st.write("Para ver ecos de granizo en tiempo real:")
        url_radar = f"https://www.windy.com/-Weather-radar-radar?radar,{LAT},{LON},9"
        
        st.markdown(f"""
            <a href="{url_radar}" target="_blank">
                <button style="width:100%; background-color:#2ecc71; color:white; padding:20px; font-size:18px; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">
                    🛰️ ABRIR RADAR DOPPLER
                </button>
            </a>
        """, unsafe_allow_html=True)

    st.divider()
    if riesgo >= 70: st.error("🚨 **AVISO URGENTE:** Riesgo extremo de granizo.")
    elif riesgo >= 40: st.warning("⚠️ **ATENCIÓN:** Atmósfera inestable.")
    else: st.success("✅ **TIEMPO ESTABLE.**")

elif menu == "❄️ Heladas":
    st.subheader("❄️ Alerta Heladas")
    for p in obtener_pronostico():
        if p['min'] < 3: st.error(f"⚠️ {p['f']}: Riesgo de helada ({p['min']}°C)")
        else: st.success(f"✅ {p['f']}: Sin riesgo ({p['min']}°C)")

elif menu == "📝 Bitácora":
    st.title("📝 Galería y Bitácora de Lotes")
    
    # --- 1. SUBIDA DE FOTOS Y NOVEDADES ---
    with st.expander("📸 Registrar Novedad en Lote", expanded=True):
        c1, c2 = st.columns([1, 1])
        with c1:
            foto = st.file_uploader("Capturar foto del lote", type=['jpg', 'png', 'jpeg'], help="Puedes sacar una foto con el celu o subir una de la galería")
        with c2:
            novedad = st.text_area("Descripción de la observación:", placeholder="Ej: Se observa presencia de oruga cogollera en manchones...")
            lote_obs = st.text_input("Lote:", value=cultivo_bot if 'cultivo_bot' in locals() else "General")
        
        if st.button("💾 GUARDAR REGISTRO"):
            if novedad:
                fecha_nota = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                linea = f"{fecha_nota} - {lote_obs}: {novedad}\n"
                with open('bitacora_campo.txt', 'a', encoding='utf-8') as f:
                    f.write(linea)
                st.success("✅ Registro guardado en la bitácora")
                # Nota: La foto se procesa aquí, pero para persistencia real 
                # necesitaríamos una base de datos. Por ahora la mostramos abajo.
            else:
                st.warning("Escribe una descripción antes de guardar.")

    st.divider()

    # --- 2. VISUALIZACIÓN DE GALERÍA (Muestra la foto actual si hay una) ---
    if foto is not None:
        st.subheader("🖼️ Última Captura de Campo")
        st.image(foto, caption=f"Observación en {lote_obs}", use_container_width=True)
        st.info(f"📌 **Nota asociada:** {novedad}")

    # --- 3. HISTORIAL DE TEXTO ---
    st.subheader("📜 Historial de Recorridas")
    if os.path.exists('bitacora_trufas.txt'):
        with open('bitacora_campo.txt', 'r', encoding='utf-8') as f:
            notas = f.readlines()
            for n in reversed(notas):
                st.info(n.strip())
    else:
        st.write("Aún no hay registros en la bitácora.")

# === SECCIÓN ESPECIALIZADA: TRUFERÍA ===
elif menu == "💎 Trufas":
    st.markdown("""
        <div style="background: linear-gradient(to right, #3d2b1e, #8e44ad); padding: 25px; border-radius: 15px; margin-bottom: 20px; color: white; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 2.2rem;">💎 AgroGuardian Pro Trufas</h1>
            <p style="margin: 0; opacity: 0.9; font-size: 1.1rem; font-weight: 300;">Gestión de Microclima y Suelo para Tuber melanosporum</p>
        </div>
    """, unsafe_allow_html=True)

elif menu == "🌡️ Temp. del Suelo":
        st.header("🌡️ Perfil Térmico del Suelo")
        
        t_10 = round(clima['temp'] * 0.82, 1)
        t_20 = round(t_10 * 0.92, 1)
        t_30 = round(t_20 * 0.95, 1)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("10 cm", f"{t_10}°C")
        with c2:
            st.metric("20 cm", f"{t_20}°C")
        with c3:
            st.metric("30 cm", f"{t_30}°C")

        st.divider() # <--- ASEGURATE QUE ESTÉ ALINEADO CON EL "with" Y EL "t_10"

        st.subheader("💧 Sugerencia de Riego (50% ETc)")
        riego_50 = round(clima['etc'] * 0.5, 1)
        
        if t_10 >= 27:
            st.error(f"Alerta: Aplicar {riego_50} mm")
        else:
            st.success(f"Normal: Mantener con {riego_50} mm")
    # --- BITÁCORA DE COSECHA ---
    st.divider()
    st.subheader("🐕 Registro de Hallazgos")
    with st.expander("📝 Cargar nueva trufa (Caza con perros)"):
        f1, f2 = st.columns(2)
        tipo = f1.selectbox("Categoría", ["Extra", "Primera", "Segunda", "Perro (marca)"])
        peso_g = f2.number_input("Peso (g)", 0, 1000, 30)
        obs = st.text_area("Ubicación / Árbol número:")
        if st.button("💾 GUARDAR REGISTRO"):
            st.balloons()
            st.success(f"Registrada trufa {tipo} de {peso_g}g. ¡Buen rinde!")






















