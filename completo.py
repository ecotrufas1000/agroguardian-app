import streamlit as st
from streamlit_folium import folium_static
import folium
import requests
import pandas as pd
import json
import os
import datetime

# === CONFIGURACIÓN Y ESTILO COMPACTO ===
st.set_page_config(page_title="AgroGuardian Pro", layout="wide", page_icon="🚜")

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
    st.title("AgroGuardian Pro")
    menu = st.radio("SECCIONES", ["📊 Monitoreo", "💧 Balance Hídrico", "⛈️ Granizo", "❄️ Heladas", "📝 Bitácora"])
    st.divider()
    st.caption(f"📍 {round(LAT,3)}, {round(LON,3)}")
    if st.button("🔄 ACTUALIZAR"): st.rerun()
# === 3. PÁGINA: MONITOREO ===
if menu == "📊 Monitoreo":
    # --- ENCABEZADO PROFESIONAL ---
    st.markdown("""
        <div style="background: linear-gradient(to right, #1e3d2f, #2ecc71); padding: 25px; border-radius: 15px; margin-bottom: 20px; color: white; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 2.2rem;">🚜 AgroGuardian Pro</h1>
            <p style="margin: 0; opacity: 0.9; font-size: 1.1rem; font-weight: 300;">Tu asistente profesional de monitoreo y decisiones climáticas</p>
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
    
    with c2:
        st.caption("🐮 BIENESTAR (ITH)")
        t_f = (1.8 * clima['temp']) + 32
        ith = round(t_f - (0.55 - 0.55 * (clima['hum'] / 100)) * (t_f - 58), 1)
        bg = "#2ecc71" if ith < 72 else "#f1c40f" if ith < 79 else "#e74c3c"
        st.markdown(f"<div style='background:{bg}; padding:15px; border-radius:10px; text-align:center; color:white;'><h2 style='margin:0;'>{ith}</h2><small>ESTADO ITH</small></div>", unsafe_allow_html=True)
        
        st.caption("📅 PRONÓSTICO CORTO")
        pronos = obtener_pronostico()
        for p in pronos[:3]:
            st.write(f"**{p['f']}:** {p['min']}°/{p['max']}° - {p['d']}")


# === 4. PÁGINA: BALANCE HÍDRICO ===
elif menu == "💧 Balance Hídrico":
    st.title("💧 Gestión Hídrica del Lote")

    # Sincronización Bot
    cultivo_bot, kc_bot, fecha_bot, etapa_bot = "No definido", 0.85, "Sin datos", "N/A"
    if os.path.exists('estado_lote.json'):
        try:
            with open('estado_lote.json', 'r', encoding='utf-8') as f:
                db = json.load(f)
                cultivo_bot, kc_bot = db.get("cultivo", "N/D"), db.get("kc", 0.85)
                fecha_bot, etapa_bot = db.get("ultima_actualizacion", "N/D"), db.get("etapa", "N/D")
        except: pass

    st.info(f"🔄 **Lote:** {cultivo_bot} | **Kc:** {kc_bot} | **Fase:** {etapa_bot} (Act: {fecha_bot})")
    
    with st.expander("⚙️ Configuración de Suelo"):
        col1, col2 = st.columns(2)
        cc = col1.number_input("Capacidad de Campo (mm)", 200, 400, 250)
        pm = col1.number_input("Punto Marchitez (mm)", 50, 150, 100)
        kc_web = col2.slider("Ajuste Kc", 0.1, 1.3, float(kc_bot))
        lluvia = col2.number_input("Lluvia Real (mm)", 0.0, 200.0, float(clima['lluvia_est']))

    # Cálculos
    etc = round(clima['etc'] * kc_web, 2)
    agua_hoy = min(cc, max(pm, 185.0 + lluvia - etc))
    util_pct = int(((agua_hoy - pm) / (cc - pm)) * 100)
    umbral = pm + (cc - pm) * 0.4 

    c1, c2 = st.columns([1, 2])
    with c1:
        color = "#2ecc71" if util_pct > 50 else "#f1c40f" if util_pct > 30 else "#e74c3c"
        st.markdown(f"<div style='border:2px solid #ddd;border-radius:15px;padding:20px;text-align:center;background:white;'><p style='color:#666;margin:0;'>AGUA ÚTIL</p><h1 style='color:{color};margin:0;font-size:50px;'>{util_pct}%</h1><p style='color:#888;margin:0;'>{round(agua_hoy,1)} mm</p></div>", unsafe_allow_html=True)

    with c2:
        st.write(f"💧 **Consumo (ETc):** {etc} mm/día")
        if util_pct < 40: st.error("🚨 **ALERTA DE RIEGO:** El suelo está bajo el umbral crítico.")
        else: st.success("✅ **ESTADO ÓPTIMO:** Reserva hídrica suficiente.")

    st.divider()
    st.subheader("📈 Proyección de Reserva (7 días)")
    fechas = [(datetime.datetime.now() + datetime.timedelta(days=i)).strftime('%d/%m') for i in range(7)]
    curva = []
    temp_agua = agua_hoy
    for i in range(7):
        curva.append(round(temp_agua, 1))
        temp_agua = max(pm, temp_agua - etc)
    
    df_graf = pd.DataFrame({"Día": fechas, "Reserva (mm)": curva, "Umbral Crítico": [umbral]*7}).set_index("Día")
    st.area_chart(df_graf, color=["#3498db", "#e74c3c"])

    # --- NUEVA SECCIÓN: EXPORTACIÓN CON ENCABEZADO TÉCNICO ---
    st.divider()
    st.subheader("📥 Exportar Informe Técnico")
    
    # Preparamos el contenido del reporte
    encabezado_texto = (
        f"AGROGUARDIAN PRO - REPORTE DE BALANCE HÍDRICO\n"
        f"FECHA DE REPORTE: {datetime.datetime.now().strftime('%d/%m/%Y')}\n"
        f"LOTE: {cultivo_bot}\n"
        f"ETAPA FENOLÓGICA: {etapa_bot}\n"
        f"AGUA ÚTIL ACTUAL: {util_pct}% ({round(agua_hoy, 1)} mm)\n"
        f"{'-'*40}\n"
    )
    
    # Combinamos encabezado + datos de la tabla
    csv_data = encabezado_texto + df_graf.to_csv()
    
    st.download_button(
        label="📄 DESCARGAR REPORTE PARA EXCEL",
        data=csv_data.encode('utf-8'),
        file_name=f"Reporte_Hídrico_{cultivo_bot}_{datetime.datetime.now().strftime('%d%m%Y')}.csv",
        mime='text/csv'
    )
elif menu == "⛈️ Granizo":
    st.markdown("""
        <div style="background: linear-gradient(to right, #1e293b, #475569); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
            <h1 style="color: white; margin: 0; font-size: 2rem;">⛈️ Monitor de Tormentas</h1>
            <p style="margin: 0; opacity: 0.9;">Detección de celdas de granizo y nubosidad convectiva</p>
        </div>
    """, unsafe_allow_html=True)

    # 1. CÁLCULO DE RIESGO OPERATIVO
    riesgo = 0
    if clima['presion'] < 1008: riesgo += 50
    if clima['hum'] > 80: riesgo += 30
    if clima['temp'] > 28: riesgo += 20
    
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.subheader("📊 Análisis de Riesgo")
        if riesgo >= 70:
            st.error(f"### RIESGO CRÍTICO: {riesgo}%")
            st.markdown("⚠️ **ALERTA ROJA:** Condiciones inestables. Formación de tormentas probables.")
        elif riesgo >= 40:
            st.warning(f"### RIESGO MODERADO: {riesgo}%")
            st.markdown("🟡 **AVISO:** Vigilancia meteorológica recomendada.")
        else:
            st.success(f"### RIESGO BAJO: {riesgo}%")
            st.markdown("🟢 **ESTADO VERDE:** Sin indicios de tormentas severas.")

    with c2:
        st.subheader("🛰️ Control de Radar")
        st.write("Debido a políticas de seguridad, el radar se abre en una ventana protegida externa para mayor detalle.")
        
        # LINK DINÁMICO AL RADAR
        url_radar = f"https://www.windy.com/-Weather-radar-radar?radar,{LAT},{LON},9"
        
        st.markdown(f"""
            <a href="{url_radar}" target="_blank" style="text-decoration: none;">
                <div style="
                    background-color: #4f46e5;
                    color: white;
                    padding: 20px;
                    border-radius: 12px;
                    text-align: center;
                    font-weight: bold;
                    box-shadow: 0 4px 10px rgba(79, 70, 229, 0.4);
                    border: 1px solid #6366f1;
                ">
                    🚀 ABRIR RADAR DOPPLER INTERACTIVO<br>
                    <span style="font-size: 0.8rem; font-weight: normal;">(Ubicación exacta)</span>
                </div>
            </a>
        """, unsafe_allow_html=True)

    st.divider()
    
    # 2. GUÍA DE LECTURA DE RADAR
    with st.expander("❓ ¿Cómo leer el radar en Windy?"):
        st.write("""
        * **Colores Azules/Verdes:** Lluvia débil a moderada.
        * **Colores Amarillos/Naranjas:** Tormentas eléctricas en desarrollo.
        * **Colores Púrpuras o Blancos:** **¡PELIGRO!** Alta probabilidad de granizo o lluvia torrencial.
        """)
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
    if os.path.exists('bitacora_campo.txt'):
        with open('bitacora_campo.txt', 'r', encoding='utf-8') as f:
            notas = f.readlines()
            for n in reversed(notas):
                st.info(n.strip())
    else:
        st.write("Aún no hay registros en la bitácora.")











