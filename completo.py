import streamlit as st
from google import genai

api_key = st.secrets.get("GOOGLE_API_KEY", None)
st.write("Key cargada:", api_key is not None)  # debe mostrar True
st.write("Primeros 8 chars:", api_key[:8] if api_key else "NADA")

client = genai.Client(api_key=api_key)
import requests  # <--- IMPORTANTE: Subí esto aquí
import json
import os
import math
import datetime
import pandas as pd
import plotly.express as px
import urllib.parse
import base64
import datetime
st.markdown("""
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="AgroGuardian">
    <meta name="theme-color" content="#2d6a2d">
    <link rel="apple-touch-icon" href="https://raw.githubusercontent.com/ecotrufas1000/agroguardian-app/main/logo1.png">
    <script>
        if ('serviceWorker' in navigator) {
            const manifest = {
                name: 'AgroGuardian',
                short_name: 'AgroGuardian',
                description: 'Diagnóstico agrícola inteligente',
                start_url: '/',
                display: 'standalone',
                background_color: '#0d2b0d',
                theme_color: '#2d6a2d',
                icons: [{
                    src: 'https://raw.githubusercontent.com/ecotrufas1000/agroguardian-app/main/logo1.png',
                    sizes: '192x192',
                    type: 'image/png'
                },
                {
                    src: 'https://raw.githubusercontent.com/ecotrufas1000/agroguardian-app/main/logo1.png',
                    sizes: '512x512',
                    type: 'image/png'
                }]
            };
            const blob = new Blob([JSON.stringify(manifest)], {type: 'application/json'});
            const manifestURL = URL.createObjectURL(blob);
            document.querySelector('link[rel="manifest"]') 
                ? document.querySelector('link[rel="manifest"]').href = manifestURL
                : (() => { const l = document.createElement('link'); l.rel='manifest'; l.href=manifestURL; document.head.appendChild(l); })();
        }
    </script>
""", unsafe_allow_html=True)
from io import BytesIO
from supabase import create_client
from streamlit_folium import folium_static
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
def generar_pdf(texto_analisis, nombre_imagen="muestra"):
     if not texto_analisis:                        # ✅ agregá estas dos líneas
         texto_analisis = "Sin contenido."         # ✅    
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from datetime import datetime
import io
import io
from datetime import datetime
# (Asegúrate de tener todas las importaciones de reportlab aquí)

def generar_pdf(texto_analisis, nombre_imagen):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    # Estilos personalizados
    estilo_titulo = ParagraphStyle(
        'Titulo',
        parent=styles['Title'],
        fontSize=22,
        textColor=colors.HexColor('#2d6a2d'),
        spaceAfter=6
    )
    estilo_subtitulo = ParagraphStyle(
        'Subtitulo',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#555555'),
        spaceAfter=4
    )
    estilo_cuerpo = ParagraphStyle(
        'Cuerpo',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        spaceAfter=8
    )
    estilo_footer = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=1  # centrado
    )

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    story = []

    # Encabezado con logo
    from reportlab.platypus import Image as RLImage, Table, TableStyle
    import urllib.request
    import io as io_module

    try:
        logo_url = "https://raw.githubusercontent.com/ecotrufas1000/agroguardian-app/main/logo1.png"
        logo_bytes = urllib.request.urlopen(logo_url).read()
        logo_buffer = io_module.BytesIO(logo_bytes)
        logo = RLImage(logo_buffer, width=40, height=40)
        titulo_texto = Paragraph("AgroGuardian", estilo_titulo)
        tabla_header = Table([[logo, titulo_texto]], colWidths=[50, 400])
        tabla_header.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ]))
        story.append(tabla_header)
    except:
        story.append(Paragraph("AgroGuardian", estilo_titulo))
    # ✅ Esto va FUERA del try/except, siempre se ejecuta
    story.append(Paragraph("Informe de Diagnóstico Agronómico", estilo_subtitulo))
    story.append(Paragraph(f"Fecha: {fecha}", estilo_subtitulo))
    story.append(Paragraph(f"Muestra: {nombre_imagen}", estilo_subtitulo))
    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2d6a2d')))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("Resultado del Análisis", styles['Heading2']))
    story.append(Spacer(1, 0.2*cm))

    for parrafo in texto_analisis.split('\n'):
        if parrafo.strip():
            parrafo_limpio = parrafo.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(parrafo_limpio, estilo_cuerpo))

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Generado por AgroGuardian · Diagnóstico asistido por IA · Solo orientativo", estilo_footer))

    doc.build(story)
    buffer.seek(0)
    return buffer
# Fuera de la función, inicializamos otras variables
client = None

try:
    if "GOOGLE_API_KEY" in st.secrets:
        client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"Error al configurar el cliente: {e}")
st.set_page_config(layout="wide", page_title="Monitor Agrícola")
st.markdown("""
<style>
    /* 1. Color de fondo de la página */
    .stApp {
        background-color: #f8f9fa;
    }

    /* 2. Personalizar TODOS los botones */
    div.stButton > button:first-child {
        background-color: #2e7d32; /* Verde Agro */
        color: white;
        border-radius: 10px;
        border: none;
        transition: 0.3s;
    }

    /* Efecto al pasar el mouse */
    div.stButton > button:first-child:hover {
        background-color: #1b5e20;
        border: none;
        color: white;
    }

    /* 3. Personalizar el botón de descarga */
    .stDownloadButton > button {
        background-color: #0277bd !important;
        color: white !important;
    }

    /* 4. Quitar márgenes de la app para que el mapa respire */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
    }

    /* 5. El mapa ocupa el máximo espacio posible */
    iframe {
        width: 100% !important;
        height: 85vh !important; /* 85% de la altura de la pantalla del celular */
        border: none !important;
    }

    /* 6. Ocultar atribuciones y marcas de agua */
    .leaflet-control-attribution {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)
# ==========================================================
# FUNCIONES DE APOYO (Ahora sí, debajo de los imports)
# ==========================================================
def get_sentinel_token():
    try:
        cid = st.secrets.get("SENTINEL_CLIENT_ID")
        csec = st.secrets.get("SENTINEL_CLIENT_SECRET")

        #st.write("CID existe:", bool(cid))
        #st.write("SECRET existe:", bool(csec))

        url = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"

        r = requests.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(cid, csec)
        )

        #st.write("Status code:", r.status_code)
        #st.write("Server response:", r.text)

        if r.status_code == 200:
            return r.json()["access_token"]
        else:
            return None

    except Exception as e:
        st.error(f"Error interno: {e}")
        return None
def get_sentinel_image(token, evalscript, lat, lon, zoom=0.01):
    url = "https://services.sentinel-hub.com/api/v1/process"
    bbox = [lon - zoom, lat - zoom, lon + zoom, lat + zoom]
    payload = {
        "input": {
            "bounds": {"bbox": bbox, "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}},
            "data": [{"type": "sentinel-2-l2a", "dataFilter": {"mosaickingOrder": "leastCC"}}]
        },
        "output": {"width": 512, "height": 512, "responses": [{"identifier": "default", "format": {"type": "image/png"}}]},
        "evalscript": evalscript
    }
    headers = {"Authorization": f"Bearer {token}", "Accept": "image/png"}
    r = requests.post(url, headers=headers, json=payload)
    return r.content if r.status_code == 200 else None
# ==========================================================
# 1. FUNCIONES DE APOYO (Calculos y Clima)
# ==========================================================
def grados_a_direccion(grados):
    try:
        val = int((grados / 22.5) + 0.5)
        direcciones = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
        return direcciones[(val % 16)]
    except: return "N/A"

def generar_link_whatsapp(tarea, lote, temp, viento, nota):
    texto = f"📝 *Reporte AgroGuardian Pro*\n\n✅ *Tarea:* {tarea}\n📍 *Lote:* {lote}\n🌡️ *Condiciones:* {temp}°C | 💨 {viento} km/h\n"
    if nota: texto += f"📋 *Notas:* {nota}\n"
    return f"https://wa.me/?text={urllib.parse.quote(texto)}"

def obtener_clima_completo(lat, lon):
    if not lat or not lon: return None
    try:
        API_KEY = st.secrets["OPENWEATHER_API_KEY"]
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
        r = requests.get(url).json()
        if r.get("main"):
            t, h = r["main"]["temp"], r["main"]["humidity"]
            a, b = 17.27, 237.7
            alpha = ((a * t) / (b + t)) + math.log(h/100.0)
            rocio = (b * alpha) / (a - alpha)
            return {
                "temp": t, "hum": h, "v_vel": round(r["wind"]["speed"] * 3.6, 1),
                "v_dir": r["wind"].get("deg", 0), "rocio": round(rocio, 1),
                "presion": r["main"]["pressure"], "localidad": r.get("name", "Zona Rural")
            }
    except: return None

# ==========================================================
# 2. CONFIGURACIÓN Y ESTILO (Terminal Dark)
# ==========================================================
#st.set_page_config(page_title="AgroGuardian Pro", layout="wide", page_icon="🛰️")
st.set_page_config(
    page_title="AgroGuardian",
    page_icon="🌿",
    layout="wide"
)

st.markdown("""
    <style>
        .stApp { background-color: #0d1117 !important; color: #00ffc3 !important; }
        [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
        h1, h2, h3, p, label { color: #00ffc3 !important; font-family: 'Courier New', monospace !important; }
        [data-testid="stMetric"] { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
        iframe[title="streamlit_js_eval.streamlit_js_eval"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# ==========================================================
# 3. CONEXIÓN BASE DE DATOS
# ==========================================================
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("🚨 Error de conexión con Supabase.")
    st.stop()

# ==========================================================
# 4. SIDEBAR ÚNICO (Solo una instancia de cada cosa)
# ==========================================================
with st.sidebar:
    # 1. Logo
    try:
        st.image("logo1.png", use_container_width=True)
    except:
        st.markdown("<h2 style='text-align:center;'>AGROGUARDIAN</h2>", unsafe_allow_html=True)
    
    st.markdown("<p style='text-align:center; font-size:10px; opacity:0.7;'>PRECISION LAB v2.6</p>", unsafe_allow_html=True)
    st.divider()

    # 2. El Menú de Radio (ESTE ES EL ÚNICO QUE DEBE EXISTIR)
    menu = st.radio(
        "MENÚ DE CONTROL", 
        ["📊 Monitoreo Total", "🌧️ Pluviómetro", "💧 Balance Hídrico", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora", "🛰️ Índices Satelitales", "🔍 Diagnóstico IA"],
        key="menu_principal"
    )
    st.divider()

# ===============================
# UBICACIÓN: GPS AUTOMÁTICO + MANUAL
# ===============================
# ==========================================================
# GPS automático con fallback a ubicación manual
# ==========================================================
# SECCIÓN GPS: Pon esto ANTES de la lógica del Menú
# ==========================================================
# ==========================================================
# SECCIÓN GPS: Prioridad Selección Manual
# ==========================================================
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

# 1. Inicializar variables de estado si no existen
if 'lat' not in st.session_state:
    st.session_state.lat = -34.59
if 'lon' not in st.session_state:
    st.session_state.lon = -58.50
if 'modo_gps' not in st.session_state:
    st.session_state.modo_gps = True  # Por defecto empieza en automático

# 2. Intentar obtener ubicación automática (siempre corre de fondo)
loc = streamlit_js_eval(js_expressions="""
new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
        (pos) => resolve({latitude: pos.coords.latitude, longitude: pos.coords.longitude}),
        (err) => resolve({error: err.message}),
        {enableHighAccuracy: true, timeout: 5000}
    )
})
""", key='get_loc_auto')

# 3. Detectar si hay GPS real disponible
gps_disponible = False
if loc and isinstance(loc, dict) and 'latitude' in loc:
    lat_auto, lon_auto = loc['latitude'], loc['longitude']
    gps_disponible = True
else:
    lat_auto, lon_auto = None, None

# 4. LÓGICA DE DECISIÓN: ¿Qué coordenadas usamos?
if st.session_state.modo_gps and gps_disponible:
    # Si el modo GPS está activo y hay señal, mandan los satélites
    st.session_state.lat = lat_auto
    st.session_state.lon = lon_auto
    gps_color, man_color = "#00ffc3", "#222" # Verde el GPS
    g_text, m_text = "#000", "#666"
else:
    # Si apagamos el GPS o no hay señal, manda lo manual guardado en lat/lon
    gps_color, man_color = "#222", "#00ffc3" # Verde lo Manual
    g_text, m_text = "#666", "#000"

# 5. RENDER VISUAL DE PASTILLAS
st.markdown(f"""
<div style='display:flex; gap:12px; margin-bottom:12px;'>
    <div style='padding:10px; border-radius:14px; font-weight:bold; background:{gps_color}; color:{g_text}; flex:1; text-align:center;'>
        🛰️ GPS Automático<br>{"Activo" if gps_disponible else "Buscando..."}
    </div>
    <div style='padding:10px; border-radius:14px; font-weight:bold; background:{man_color}; color:{m_text}; flex:1; text-align:center;'>
        📍 Ubicación Manual<br>{st.session_state.lat:.4f} | {st.session_state.lon:.4f}
    </div>
</div>
""", unsafe_allow_html=True)

# 6. EXPANDER PARA CONTROL TOTAL
with st.expander("⚙️ Configurar Ubicación del Lote"):
    c1, c2 = st.columns(2)
    new_lat = c1.number_input("Latitud", value=st.session_state.lat, format="%.6f")
    new_lon = c2.number_input("Longitud", value=st.session_state.lon, format="%.6f")
    
    col_btn1, col_btn2 = st.columns(2)
    
    if col_btn1.button("📍 USAR ESTA UBICACIÓN MANUAL", use_container_width=True):
        st.session_state.modo_gps = False  # Apagamos el GPS automático
        st.session_state.lat = new_lat
        st.session_state.lon = new_lon
        st.success("Prioridad cambiada a Manual")
        st.rerun()
        
    if col_btn2.button("🛰️ VOLVER A GPS AUTO", use_container_width=True):
        st.session_state.modo_gps = True   # Volvemos a encender el GPS
        st.rerun()

st.divider()
# 5. LÓGICA DE DATOS GLOBAL
# ==========================================================
LAT = st.session_state.get('lat')
LON = st.session_state.get('lon')
clima = obtener_clima_completo(LAT, LON)

if clima:
    st.session_state.clima_data = clima


if menu == "📊 Monitoreo Total":
    st.header("📊 Tablero de Control")
    
    if clima:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric("Temperatura", f"{clima['temp']} °C")
        with col2: st.metric("Humedad Rel.", f"{clima['hum']} %")
        with col3: st.metric("Pto. de Rocío", f"{clima['rocio']} °C")
        with col4: st.metric("Viento", f"{clima['v_vel']} km/h")
        with col4: st.metric("Presion", f"{clima['presion']} hPa") 
        st.divider() # <--- Estaba mal indentado antes
        c_a1, c_a2 = st.columns(2)
        
        with c_a1:
            delta_t = round(clima['temp'] - clima['rocio'], 1)
            st.markdown(f"**Delta T (Pulverización):** `{delta_t}`")
            if 2 <= delta_t <= 8: 
                st.success("✅ CONDICIONES ÓPTIMAS")
            else: 
                st.warning("⚠️ PRECAUCIÓN: Delta T fuera de rango")
        
        with c_a2:
            # Ahora usamos la función que definimos arriba
            dir_texto = grados_a_direccion(clima['v_dir'])
            st.markdown(f"**Dirección:** `{dir_texto}` ({clima['v_dir']}°)")
            
            # Mantenemos tus flechas visuales
            if 315 <= clima['v_dir'] or clima['v_dir'] <= 45: st.info("⬆️ Viento Norte")
            elif 135 <= clima['v_dir'] <= 225: st.info("⬇️ Viento Sur")
            else: st.info("➡️ Viento Lateral")
            
    else:
        st.info("📍 Vinculá el GPS para activar el monitoreo en tiempo real.")
elif menu == "🌧️ Pluviómetro":
    st.header("🌧️ Pluviómetro Digital")

    try:
        res = supabase.table("registros_lluvia").select("*").execute()

        if res.data and len(res.data) > 0:
            df = pd.DataFrame(res.data)
            df['fecha'] = pd.to_datetime(df['fecha'], format='mixed', utc=True)
            df['mm'] = pd.to_numeric(df['mm'], errors='coerce').fillna(0)
            from datetime import datetime, timezone
            hoy = datetime.now(timezone.utc)

            # --- MÉTRICAS RÁPIDAS ---
            df_mes = df[(df['fecha'].dt.month == hoy.month) & (df['fecha'].dt.year == hoy.year)].copy()
            df_año = df[df['fecha'].dt.year == hoy.year].copy()
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💧 Este Mes", f"{df_mes['mm'].sum():.1f} mm")
            c2.metric("📆 Acum. Anual", f"{df_año['mm'].sum():.1f} mm")
            c3.metric("⚡ Máx. Día", f"{df_mes['mm'].max() if not df_mes.empty else 0:.1f} mm")
            c4.metric("📊 Registros", f"{len(df)} eventos")

            # --- BOTÓN DE WHATSAPP CON TABLA DETALLADA ---
            st.divider()
            ultimos_registros = df.sort_values('fecha', ascending=False).head(10)
            detalle_tabla = ""
            for i, row in ultimos_registros.iterrows():
                fecha_str = row['fecha'].strftime('%d/%m')
                detalle_tabla += f"📍 {fecha_str}: {row['mm']:.1f} mm\n"

            mensaje_wa = (
                f"🌱 *REPORTE AGROGUARDIAN*\n"
                f"📅 Fecha: {hoy.strftime('%d/%m/%Y')}\n"
                f"--------------------------------\n"
                f"💧 *RESUMEN:* \n"
                f"• Mes: {df_mes['mm'].sum():.1f} mm\n"
                f"• Año: {df_año['mm'].sum():.1f} mm\n"
                f"--------------------------------\n"
                f"📋 *ÚLTIMOS REGISTROS:* \n"
                f"{detalle_tabla}"
                f"--------------------------------\n"
                f"🛰️ _Precision Lab v2.6_"
            )
            
            import urllib.parse
            mensaje_url = urllib.parse.quote(mensaje_wa)
            wa_url = f"https://wa.me/?text={mensaje_url}"

            st.markdown(f"""
                <a href="{wa_url}" target="_blank" style="text-decoration: none;">
                    <div style="
                        background-color: #25D366;
                        color: white;
                        padding: 15px;
                        border-radius: 12px;
                        text-align: center;
                        font-weight: bold;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        gap: 12px;
                        box-shadow: 0px 6px 15px rgba(0,0,0,0.4);
                    ">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="25px">
                        ENVIAR REPORTE + TABLA DIARIA
                    </div>
                </a>
            """, unsafe_allow_html=True)
            st.write("")
            st.divider()
            
            # --- GRÁFICOS ---
            estilo_grafico = dict(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#00ffc3"),
                height=350,
                margin=dict(l=10, r=10, t=30, b=20)
            )

            st.subheader(f"📅 Detalle Diario — {hoy.strftime('%B %Y')}")
            df_mes['dia'] = df_mes['fecha'].dt.day
            df_dia = df_mes.groupby('dia')['mm'].sum().reindex(range(1, 32), fill_value=0).reset_index()
            fig1 = px.bar(df_dia, x='dia', y='mm', template="plotly_dark")
            fig1.update_traces(marker_color='#1f77b4')
            fig1.update_layout(**estilo_grafico)
            st.plotly_chart(fig1, use_container_width=True, config={'staticPlot': True})

            st.subheader(f"📊 Acumulado Mensual — Año {hoy.year}")
            meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            mensual = df_año.groupby(df_año['fecha'].dt.month)['mm'].sum().reindex(range(1, 13), fill_value=0)
            df_anual = pd.DataFrame({'Mes': meses_nombres, 'Prec_mm': mensual.values})
            fig2 = px.bar(df_anual, x='Mes', y='Prec_mm', template="plotly_dark",
                          text_auto='.1f', title="Distribución de Lluvias por Mes")
            fig2.update_traces(marker_color='#00ffc3', textposition="outside")
            fig2.update_layout(**estilo_grafico)
            st.plotly_chart(fig2, use_container_width=True, config={'staticPlot': True})

            st.divider()

            # --- PLANILLA EXCEL ---
            st.subheader("📂 Base de Datos Histórica")
            with st.expander("🔍 VER PLANILLA Y EXPORTAR"):
                df_display = df.copy()
                df_display['fecha'] = df_display['fecha'].dt.tz_localize(None)
                df_display = df_display.sort_values('fecha', ascending=False)
                st.dataframe(df_display[['fecha', 'lote', 'mm']], use_container_width=True)

                import io
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_display.to_excel(writer, index=False, sheet_name='Registros_Lluvia')
                    workbook  = writer.book
                    worksheet = writer.sheets['Registros_Lluvia']
                    for i, col in enumerate(df_display.columns):
                        column_len = max(df_display[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, column_len)
                excel_data = output.getvalue()

                st.markdown("""
                    <style>
                    div.stDownloadButton > button {
                        background-color: #00ffc3 !important;
                        color: #000000 !important;
                        border: 2px solid #00ffc3 !important;
                        border-radius: 8px !important;
                        padding: 10px 20px !important;
                        font-weight: bold !important;
                        width: 100% !important;
                    }
                    div.stDownloadButton > button:hover,
                    div.stDownloadButton > button:active,
                    div.stDownloadButton > button:focus {
                        background-color: #0e1117 !important;
                        color: #00ffc3 !important;
                        border: 2px solid #00ffc3 !important;
                    }
                    </style>
                """, unsafe_allow_html=True)

                st.download_button(
                    label="📥 DESCARGAR PLANILLA EXCEL (.xlsx)",
                    data=excel_data,
                    file_name=f'Lluvias_AgroGuardian_{hoy.strftime("%Y-%m-%d")}.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )

            # --- GESTIÓN DE REGISTROS ---
            st.divider()
            st.subheader("📂 Gestión de Registros Históricos")
            with st.expander("✏️ Ver y editar registros", expanded=False):  # ✅ expanded=False = oculto
                st.info("💡 Hacé doble clic en los 'mm' para corregir o selecciona una fila y pulsá 'Suprimir' para borrar.")
                df_editable = df.copy().sort_values('fecha', ascending=False)
                    edited_df = st.data_editor(
                    df_editable[['id', 'fecha', 'lote', 'mm']],
                    key="editor_lluvias",
                    num_rows="dynamic",
                    use_container_width=True,
                    disabled=["id", "fecha"],
                    column_config={
                        "mm": st.column_config.NumberColumn("Milímetros", format="%.1f mm", min_value=0),
                        "fecha": st.column_config.DatetimeColumn("Fecha de Registro", format="DD/MM/YYYY HH:mm"),
                        "lote": "Lote/Identificación",
                        "id": None
                    }
                )

                c_save1, c_save2 = st.columns([1, 4])
            with c_save1:
                if st.button("💾 GUARDAR CAMBIOS"):
                    try:
                        ids_originales = set(df['id'].tolist())
                        ids_actuales = set(edited_df['id'].dropna().tolist())
                        ids_a_borrar = list(ids_originales - ids_actuales)
                        for id_b in ids_a_borrar:
                            supabase.table("registros_lluvia").delete().eq("id", id_b).execute()
                        for index, row in edited_df.iterrows():
                            if pd.notnull(row['id']):
                                supabase.table("registros_lluvia").update({
                                    "mm": row['mm'],
                                    "lote": row['lote']
                                }).eq("id", row['id']).execute()
                        st.success("✅ ¡Base de Datos sincronizada!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")

            # --- ✅ REGISTRO AUTOMÁTICO SATELITAL ---
            st.divider()
            st.markdown("### 🛰️ Registro Automático desde Satélite")
            col_auto1, col_auto2 = st.columns([2, 1])

            with col_auto1:
                st.caption("Obtiene precipitaciones desde Open-Meteo usando tu ubicación GPS. Sin costo, sin límites.")

            with col_auto2:
                if st.button("📡 REGISTRAR HOY", type="primary"):
                    try:
                        import requests
                        from datetime import date
                        lat_auto = LAT if LAT else -38.29
                        lon_auto = LON if LON else -57.55
                        hoy_fecha = date.today().isoformat()
                        url_meteo = (
                            f"https://api.open-meteo.com/v1/forecast?"
                            f"latitude={lat_auto}&longitude={lon_auto}"
                            f"&daily=precipitation_sum"
                            f"&timezone=America/Argentina/Buenos_Aires"
                            f"&start_date={hoy_fecha}&end_date={hoy_fecha}"
                        )
                        r = requests.get(url_meteo).json()
                        mm_hoy = r['daily']['precipitation_sum'][0] or 0.0
                        supabase.table("registros_lluvia").insert({
                            "fecha": hoy_fecha,
                            "mm": mm_hoy,
                            "lote": "🛰️ Automático (Open-Meteo)"
                        }).execute()
                        st.success(f"✅ Registrado: {mm_hoy:.1f} mm para hoy")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

            if st.button("📅 IMPORTAR ÚLTIMOS 7 DÍAS"):
                try:
                    import requests
                    from datetime import date, timedelta
                    lat_auto = LAT if LAT else -38.29
                    lon_auto = LON if LON else -57.55
                    fecha_fin = date.today().isoformat()
                    fecha_ini = (date.today() - timedelta(days=7)).isoformat()
                    url_meteo = (
                        f"https://api.open-meteo.com/v1/forecast?"
                        f"latitude={lat_auto}&longitude={lon_auto}"
                        f"&daily=precipitation_sum"
                        f"&timezone=America/Argentina/Buenos_Aires"
                        f"&start_date={fecha_ini}&end_date={fecha_fin}"
                    )
                    r = requests.get(url_meteo).json()
                    fechas = r['daily']['time']
                    lluvias = r['daily']['precipitation_sum']
                    registros = 0
                    for fecha, mm in zip(fechas, lluvias):
                        if mm and mm > 0:
                            supabase.table("registros_lluvia").insert({
                                "fecha": fecha,
                                "mm": mm,
                                "lote": "🛰️ Automático (Open-Meteo)"
                            }).execute()
                            registros += 1
                    st.success(f"✅ Importados {registros} días con lluvia")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        else:
            st.info("🛰️ No hay registros de lluvia cargados todavía.")

    except Exception as e:
        st.error(f"Error al procesar los datos de lluvia: {e}")                        
elif menu == "💧 Balance Hídrico":
    import folium
    from streamlit_folium import folium_static
    st.markdown("### Evapotranspiracion 💧 Blanney-Criddle")
    try:
        lat = LAT if LAT else -38.29
        lon = LON if LON else -57.55
        temp_media = st.session_state.clima_data['temp'] if 'clima_data' in st.session_state else 25.0
        doy = datetime.now().timetuple().tm_yday
        delta = 0.409 * math.sin((2 * math.pi * doy / 365) - 1.39)
        ws = math.acos(max(-1, min(1, -math.tan(math.radians(lat)) * math.tan(delta))))
        eto_diaria = ((24/math.pi)*ws / 4380) * 100 * (0.46 * temp_media + 8)
        try:
            url_cop = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=soil_moisture_28_to_100cm&models=ecmwf_ifs&forecast_days=1"
            res_cop = requests.get(url_cop).json()
            hum_profunda = res_cop['hourly']['soil_moisture_28_to_100cm'][0]
        except:
            hum_profunda = 0.0
        # Conversión m³/m³ a mm: perfil 28-100cm = 72cm = 720mm
        hum_perfil_mm = hum_profunda * 720
        kc = st.slider("Kc del Cultivo", 0.3, 1.2, 0.8)
        etc = eto_diaria * kc
        c1, c2, c3 = st.columns(3)
        c1.metric("ETo (Demanda)", f"{eto_diaria:.2f} mm")
        c2.metric("ETc (Consumo)", f"{etc:.2f} mm")
        c3.metric("Humedad Perfil", f"{hum_perfil_mm:.1f} mm", help="Agua en perfil 28-100cm")
        st.divider()
        # --- Mapa NASA GIBS ---
        # --- Mapa SEPA INTA ---
        st.markdown("### 🌱 Agua Útil en el Suelo - SEPA/INTA")
        st.markdown("""
        <div style="background-color:#111; padding:20px; border-radius:10px; text-align:center;">
            <p style="color:#00ffc3; font-family:monospace; font-size:14px; margin-bottom:10px;">
                🛰️ Mapas de Agua Útil en Suelo — SEPA/INTA
            </p>
            <p style="color:#aaa; font-family:monospace; font-size:12px; margin-bottom:15px;">
                Actualización cada 10 días | Balance hídrico satelital + estaciones INTA/SMN
            </p>
            <div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap;">
                <a href="https://sepa.inta.gob.ar/productos/agua_en_suelo/pj_10d/" target="_blank"
                   style="background-color:#00ffc3; color:#000; padding:12px 24px; 
                          border-radius:8px; font-family:monospace; font-weight:bold; 
                          text-decoration:none; font-size:14px;">
                    🌱 % Agua Útil (0-2m)
                </a>
                <a href="https://sepa.inta.gob.ar/productos/agua_en_suelo/ad_10d/" target="_blank"
                   style="background-color:#00b4d8; color:#000; padding:12px 24px; 
                          border-radius:8px; font-family:monospace; font-weight:bold; 
                          text-decoration:none; font-size:14px;">
                    💧 Agua Disponible (mm)
                </a>
            </div>
            <p style="color:#888; font-size:11px; margin-top:12px; font-family:monospace;">
                📡 Mismo producto que usa el SMN | Cubre región pampeana y NOA/NEA
            </p>
        </div>
        """, unsafe_allow_html=True)
        
       
    except Exception as e:
        st.error(f"Error en Balance Hídrico: {e}")

elif menu == "⛈️ Radar Granizo":
    st.header("⛈️ Monitor de Tormentas y Granizo")

    if LAT and LON and clima:
        c1, c2, c3 = st.columns(3)

        hum = clima['hum']
        temp = clima['temp']
        presion = clima['presion']
        rocio = clima['rocio']

        with c1:
            riesgo = "ALTO" if hum > 80 and temp > 25 else "MEDIO" if hum > 60 else "BAJO"
            st.metric("Riesgo de Inestabilidad", riesgo, delta="Basado en Hum/Temp")

        with c2:
            st.metric("Presión Atmosférica", f"{presion} hPa")

        with c3:
            st.metric("Punto de Rocío", f"{rocio} °C", help="A mayor punto de rocío, más combustible para la tormenta")

        st.divider()

        # Selector de capa nativo
        capa = st.radio("Seleccionar Capa del Sensor:", ["Radar", "Rayos", "Nubes"], index=0)
        vistas = {"Radar": "radar", "Rayos": "thunder", "Nubes": "satellite"}

        st.markdown(f"### 🛰️ Sensor Activo: {capa}")
        url_windy = f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&overlay={vistas[capa]}&product=radar&menu=&message=true&marker=true&calendar=now&pressure=true&type=map&location=coordinates&detail=true&metricWind=km%2Fh&metricTemp=%C2%B0C&radarRange=-1"
        st.components.v1.iframe(url_windy, height=600)

        with st.expander("ℹ️ ¿Cómo leer el radar?"):
            st.write("""
            - **Colores Verdes/Azules:** Lluvia ligera o moderada.
            - **Colores Rojos/Amarillos:** Tormentas fuertes, posible granizo pequeño.
            - **Colores Púrpura/Blanco:** Celdas de granizo pesado o tormentas severas.
            - **Capa de Rayos:** Las cruces brillantes indican actividad eléctrica en tiempo real.
            """)
    else:
        st.warning("📍 Se requiere vincular el GPS en el panel lateral para centrar el radar en tu lote.")
elif menu == "❄️ Análisis de Heladas":
    st.markdown("<h2 style='font-size: 24px;'>❄️ Heladas Agrometeorológicas</h2>", unsafe_allow_html=True)
    
    # 1. Clima en tiempo real
    if clima:
        c1, c2 = st.columns(2)
        with c1: st.metric("Temp. Actual", f"{clima['temp']}°C")
        with c2:
            if clima['temp'] < 3: st.error("⚠️ Riesgo de Helada")
            else: st.success("✅ Sin riesgo")

        # --- ANÁLISIS DE RIESGO AGROMETEREOLÓGICO ---
        st.markdown("<h3 style='font-size: 20px;'>🌡️ Análisis de Riesgo Actual</h3>", unsafe_allow_html=True)
        
        temp = clima['temp']
        rocio = clima['rocio']
        viento = clima['v_vel']
        hum = clima['hum']
        diferencia_rocio = temp - rocio
        puntos = 0
        factores = []

        if temp <= 0:
            puntos += 4
            factores.append("🔴 Temperatura bajo cero — helada en curso")
        elif temp <= 2:
            puntos += 3
            factores.append("🟠 Temperatura crítica (0-2°C) — riesgo muy alto")
        elif temp <= 4:
            puntos += 2
            factores.append("🟡 Temperatura de alerta (2-4°C) — riesgo moderado")
        elif temp <= 7:
            puntos += 1
            factores.append("🟢 Temperatura baja (4-7°C) — riesgo leve")

        if diferencia_rocio < 2:
            puntos += 3
            factores.append("🔴 Punto de rocío muy cercano — inversión térmica probable")
        elif diferencia_rocio < 4:
            puntos += 2
            factores.append("🟡 Diferencia temp-rocío baja — condensación posible")
        elif diferencia_rocio < 6:
            puntos += 1
            factores.append("🟢 Diferencia temp-rocío moderada")

        if viento < 5:
            puntos += 2
            factores.append("🔴 Viento calmo — favorece inversión térmica y helada radiativa")
        elif viento < 10:
            puntos += 1
            factores.append("🟡 Viento leve — mezcla de aire insuficiente")
        else:
            factores.append("🟢 Viento suficiente — reduce riesgo de helada radiativa")

        if hum > 85 and temp < 5:
            puntos += 2
            factores.append("🔴 Alta humedad con temperatura baja — riesgo de escarcha")
        elif hum > 70 and temp < 7:
            puntos += 1
            factores.append("🟡 Humedad elevada con temperatura baja")

        if puntos >= 7:
            nivel = "🚨 RIESGO EXTREMO"
            color = "error"
            consejo = "Activar sistemas de protección inmediatamente. Helada inminente o en curso."
        elif puntos >= 5:
            nivel = "🔴 RIESGO ALTO"
            color = "error"
            consejo = "Preparar sistemas de protección. Alta probabilidad de helada esta noche."
        elif puntos >= 3:
            nivel = "🟡 RIESGO MODERADO"
            color = "warning"
            consejo = "Monitorear cada 30 minutos. Posibilidad de helada en horas nocturnas."
        elif puntos >= 1:
            nivel = "🟢 RIESGO BAJO"
            color = "success"
            consejo = "Condiciones desfavorables para helada. Mantener vigilancia."
        else:
            nivel = "✅ SIN RIESGO"
            color = "success"
            consejo = "Sin condiciones de helada en las próximas horas."

        if color == "error":
            st.error(f"**{nivel}** — {consejo}")
        elif color == "warning":
            st.warning(f"**{nivel}** — {consejo}")
        else:
            st.success(f"**{nivel}** — {consejo}")

        with st.expander("🔍 Ver análisis detallado de factores"):
            for f in factores:
                st.markdown(f"- {f}")
            st.caption(f"Puntaje de riesgo: {puntos}/11 | Temp: {temp}°C | Rocío: {rocio}°C | Viento: {viento} km/h | Humedad: {hum}%")

    st.divider()

    try:
        # 2. Carga de datos desde Supabase
        res_h = supabase.table("registros_heladas").select("*").execute()
        df_h = pd.DataFrame(columns=['id', 'Fecha', 'Intensidad', 'Duracion'])

        if res_h.data:
            df_temp = pd.DataFrame(res_h.data)
            if 'Fecha' in df_temp.columns:
                df_temp['Fecha'] = pd.to_datetime(df_temp['Fecha'], errors='coerce')
                df_temp = df_temp.dropna(subset=['Fecha'])
                if not df_temp.empty:
                    df_h = df_temp
            
        from datetime import datetime, timezone
        hoy = datetime.now(timezone.utc)
        if not df_h.empty and pd.api.types.is_datetime64_any_dtype(df_h['Fecha']):
            df_h_anio = df_h[df_h['Fecha'].dt.year == hoy.year].copy()
            
            if not df_h_anio.empty:
                df_h_anio = df_h_anio.sort_values('Fecha')
                primera = df_h_anio.iloc[0]['Fecha']
                ultima = df_h_anio.iloc[-1]['Fecha']
                
                m1, m2, m3 = st.columns(3)
                m1.metric("🧊 1° Helada", primera.strftime('%d/%m'))
                m2.metric("🔥 Últ. Helada", ultima.strftime('%d/%m'))
                m3.metric("📅 Días Críticos", (ultima - primera).days)

                st.markdown("<h3 style='font-size: 20px;'>📊 Resumen del Ciclo</h3>", unsafe_allow_html=True)
                fuerte = df_h_anio.sort_values('Intensidad').iloc[0]
                st.info(f"❄️ **Más intensa:** {fuerte['Intensidad']}°C ({fuerte['Fecha'].strftime('%d/%m')}) | ⏳ **Total Horas Frío:** {df_h_anio['Duracion'].sum():.1f} hs")
            else:
                st.warning(f"No hay registros para el año {hoy.year}")
        else:
            st.info("A la espera de los primeros registros de heladas...")

        st.divider()
        with st.expander("➕ Registrar Nueva Helada", expanded=True):
            with st.form("form_helada", clear_on_submit=True):
                f_col1, f_col2, f_col3 = st.columns(3)
                with f_col1:
                    nueva_fecha = st.date_input("Fecha", value=datetime.now())
                with f_col2:
                    nueva_int = st.text_input("Temp. (°C)", placeholder="-2.5")
                with f_col3:
                    nueva_dur = st.number_input("Horas", min_value=0.0, step=0.5)
                submitted = st.form_submit_button("Añadir a Bitácora")

        if submitted:
            try:
                val_int = float(nueva_int.replace(',', '.'))
                datos_nuevos = {"Fecha": nueva_fecha.isoformat(), "Intensidad": val_int, "Duracion": nueva_dur}
                supabase.table("registros_heladas").insert(datos_nuevos).execute()
                st.success("✅ ¡Registrada!")
                st.rerun()
            except ValueError:
                st.error("❌ Escribí la temperatura con números (ej: -3.5)")

        with st.expander("📋 Ver Historial de Registros", expanded=False):
            st.info("Para borrar: Seleccioná la fila y tocá la papelera 🗑️ arriba de la tabla.")
            df_display = df_h[['id', 'Fecha', 'Intensidad', 'Duracion']].sort_values('Fecha', ascending=False)
            edited_h = st.data_editor(
                df_display,
                key="visor_heladas",
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "Fecha": st.column_config.DatetimeColumn("Fecha", format="DD/MM/YYYY"),
                    "Intensidad": st.column_config.NumberColumn("Temp °C", format="%.1f"),
                    "Duracion": None,
                    "id": None 
                }
            )
            if len(edited_h) < len(df_display):
                ids_originales = set(df_display['id'].dropna().tolist())
                ids_actuales = set(edited_h['id'].dropna().tolist())
                ids_a_borrar = ids_originales - ids_actuales
                for id_b in ids_a_borrar:
                    supabase.table("registros_heladas").delete().eq("id", id_b).execute()
                st.rerun()

    except Exception as e:
        st.error(f"Error en el módulo: {e}")
elif menu == "📝 Bitácora":
    st.header("📝 Cuaderno de Campo Digital")
    
    with st.form("nueva_nota", clear_on_submit=False):
        st.subheader("Registrar Evento o Tarea")
        c1, c2 = st.columns(2)
        
        with c1:
            # Agregamos Helada y Granizo al listado
            tarea = st.selectbox("Evento/Tarea", [
                "Fumigación", "Siembra", "Cosecha", 
                "Fertilización", "Monitoreo", 
                "❄️ Helada", "☄️ Granizo", "Otro"
            ])
            lote = st.text_input("Lote", placeholder="Ej: Lote Norte")
        
        with c2:
            # Si es Helada o Granizo, sugerimos poner la intensidad en la nota
            if tarea == "❄️ Helada":
                detalle_extra = st.selectbox("Intensidad de Helada", ["Leve (0° a -2°)", "Moderada (-2° a -4°)", "Fuerte (<-4°)"])
            elif tarea == "☄️ Granizo":
                detalle_extra = st.selectbox("Tamaño del Granizo", ["Pequeno (Arroz)", "Mediano (Uva)", "Grande (Huevo)"])
            else:
                detalle_extra = ""
                
            nota_adicional = st.text_area("Observaciones del evento", placeholder="Describa daños visibles o detalles...")

        btn_guardar = st.form_submit_button("💾 GUARDAR Y GENERAR REPORTE")
        
        if btn_guardar:
            if lote and tarea:
                try:
                    t_act = clima['temp'] if clima else 0
                    v_act = clima['v_vel'] if clima else 0
                    
                    # Combinamos la nota con el detalle de intensidad si existe
                    nota_final = f"[{detalle_extra}] {nota_adicional}" if detalle_extra else nota_adicional
                    
                    datos = {
                        "tarea": tarea, 
                        "lote": lote, 
                        "nota": nota_final, 
                        "clima_temp": t_act, 
                        "clima_viento": v_act
                    }
                    
                    supabase.table("bitacora").insert(datos).execute()
                    st.success(f"✅ ¡{tarea} registrada con éxito!")
                    
                    # Generar reporte para WhatsApp
                    link_wa = generar_link_whatsapp(tarea, lote, t_act, v_act, nota_final)
                    
                    st.markdown(f"""
                        <a href="{link_wa}" target="_blank" style="text-decoration: none;">
                            <div style="background-color: #25D366; color: white; padding: 15px; text-align: center; border-radius: 10px; font-weight: bold; font-size: 18px; margin-top: 20px;">
                                📲 INFORMAR SINIESTRO/EVENTO POR WA
                            </div>
                        </a>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("⚠️ Completá Lote y Evento.")

    st.divider()  
    
    # --- HISTORIAL DE ACTIVIDADES (Cierre del bloque) ---
    st.divider()
    
    # Creamos UN SOLO expander para todo el historial
    with st.expander("📂 VER HISTORIAL COMPLETO DE ACTIVIDADES"):
        try:
            res = supabase.table("bitacora").select("*").order("fecha", desc=True).execute()
            
            if res.data:
                # Si querés que adentro sea una tabla (más compacto):
                df_bit = pd.DataFrame(res.data)
                df_bit['fecha'] = pd.to_datetime(df_bit['fecha']).dt.strftime('%d/%m/%Y %H:%M')
                
                st.dataframe(
                    df_bit[['fecha', 'tarea', 'lote', 'clima_temp', 'clima_viento', 'nota']],
                    use_container_width=True,
                    column_config={
                        "clima_temp": st.column_config.NumberColumn("Temp (°C)", format="%.1f"),
                        "clima_viento": st.column_config.NumberColumn("Viento (km/h)", format="%.1f")
                    }
                )
                
                # O si preferís las tarjetas que te pasé antes, 
                # simplemente ponés el bucle for aquí adentro.
                
            else:
                st.info("No hay registros cargados.")
        except Exception as e:
            st.error(f"Error al cargar: {e}")

# Aquí termina la Bitácora
# ==========================================================
# ==========================================================
# SECCIÓN: 🛰️ ÍNDICES SATELITALES (VERSIÓN FINAL CORREGIDA)
# --- SECCIÓN: 🛰️ ÍNDICES SATELITALES ---
elif menu == "🛰️ Índices Satelitales":
    import geopandas as gpd
    import os
    import folium
    import streamlit as st
    import streamlit.components.v1 as components
    from datetime import datetime

    # --- TRUCO CSS: Ocultar la barra de atribución de Folium ---
    st.markdown("""
        <style>
        .leaflet-control-attribution { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    st.header("🛰️ Monitor Satelital Dinámico")

    INSTANCE_ID = "95f18ee6-a5c6-4c82-b286-f0641c20410d" 
    
    @st.cache_data
    def cargar_limites_argentina():
        ruta_gpkg = "gadm41_AGR_2.gpkg" 
        if os.path.exists(ruta_gpkg):
            return gpd.read_file(ruta_gpkg, engine="pyogrio")
        return None

    gdf_argentina = cargar_limites_argentina()

    if gdf_argentina is not None:
        col_prov = "NAME_1"
        col_depto = "NAME_2"

        c1, c2, c3 = st.columns([1, 1, 1])
        st.markdown("""
            <style>
            /* Evita que el teclado se abra en los selectbox */
            div[data-baseweb="select"] input {
                caret-color: transparent !important;
                pointer-events: none !important;
            }
            </style>
        """, unsafe_allow_html=True)
        with c1:
            provincias = sorted(gdf_argentina[col_prov].unique())
            prov_sel = st.selectbox("Provincia:", ["Seleccionar..."] + provincias)
        with c2:
            if prov_sel != "Seleccionar...":
                deptos = sorted(gdf_argentina[gdf_argentina[col_prov] == prov_sel][col_depto].unique())
                depto_sel = st.selectbox("Departamento:", ["Seleccionar..."] + deptos)
            else:
                depto_sel = st.selectbox("Departamento:", ["Esperando..."], disabled=True)
        with c3:
            indice_sel = st.selectbox("Capa / Índice:", ["NDVI", "NDWI", "TRUE-COLOR"])

        if prov_sel != "Seleccionar..." and depto_sel != "Seleccionar...":
            with st.spinner(f"Calculando {indice_sel}..."):
                gdf_loc = gdf_argentina[(gdf_argentina[col_prov] == prov_sel) & (gdf_argentina[col_depto] == depto_sel)]
                centro = gdf_loc.geometry.centroid.iloc[0]

                # Mapa base optimizado para tamaño completo y móvil
                m = folium.Map(
                    location=[centro.y, centro.x],
                    zoom_start=13, # Subimos a 13 para que el lote se vea más grande de entrada
                    tiles='OpenStreetMap',
                    attr=' ',
                    height='100%', # <--- ESTO fuerzo el alto al máximo
                    width='100%'   # <--- ESTO fuerzo el ancho al máximo
                )
                # Capa WMS
                folium.WmsTileLayer(
                    url=f"https://services.sentinel-hub.com/ogc/wms/{INSTANCE_ID}",
                    layers=indice_sel,
                    name=f"Sentinel-2 {indice_sel}",
                    fmt="image/png",
                    transparent=True,
                    overlay=True,
                    opacity=1.0,
                    zindex=1000,
                    version="1.1.1",
                    maxcc=100, 
                    time="2023-01-01/2026-03-04",
                    attr=' ' # Intentamos limpiar la atribución de la capa también
                ).add_to(m)

                folium.GeoJson(gdf_loc, style_function=lambda x: {'fillColor': 'transparent', 'color': 'black', 'weight': 2}).add_to(m)

                m.fit_bounds(gdf_loc.total_bounds.tolist())
                #components.html(m._repr_html_(), height=900)
                components.html(
                    m.get_root().render(),
                    height=1000,
                    width=None
                )
                # --- SECCIÓN DE LEYENDAS DINÁMICAS ---
                st.write("---")
                
                if indice_sel == "NDVI":
                    st.subheader("🍃 Análisis de Vigor Vegetal (NDVI)")
                    st.markdown("""
                    El **NDVI** mide la salud de la vegetación:
                    * 🟩 **Verde Oscuro:** Cultivo muy sano o bosque denso (máximo vigor).
                    * 🟩 **Verde Claro:** Vegetación en crecimiento o pasturas.
                    * 🟨 **Amarillo/Marrón:** Suelo desnudo, rastrojo o cultivo estresado.
                    * 🟥 **Rojo/Blanco:** Zonas sin vegetación o agua.
                    """)
                    
                elif indice_sel == "NDWI":
                    st.subheader("💧 Monitor de Humedad y Agua (NDWI)")
                    st.markdown("""
                    El **NDWI** resalta la presencia de agua líquida:
                    * 🟦 **Azul Oscuro:** Cuerpos de agua claros (lagunas, canales).
                    * 🔷 **Celeste:** Suelo muy húmedo, barro o vegetación inundada.
                    * ⬜ **Blanco:** Suelo seco, cultivos o zonas urbanas.
                    """)
                    
                elif indice_sel == "TRUE-COLOR":
                    st.subheader("📸 Fotografía Satelital Real (True Color)")
                    st.markdown("""
                    Esta es una composición de color natural (RGB):
                    * 🌿 **Verdes:** Cultivos activos y montes.
                    * 🪵 **Marrones/Grises:** Lotes preparados para siembra o rastrojo.
                    * ⚫ **Oscuros:** Agua profunda o sombras de nubes.
                    * ☁️ **Blanco Brillante:** Nubes o construcciones.
                    """)
                    # --- GENERAR REPORTE DE DESCARGA ---
                fecha_reporte = datetime.now().strftime('%d/%m/%Y')
                
                # Preparamos el contenido del reporte
                texto_reporte = f"""
                📊 INFORME DE MONITOREO SATELITAL
                ---------------------------------
                📍 Ubicación: {depto_sel}, {prov_sel}
                📅 Fecha de Consulta: {fecha_reporte}
                🛰️ Capa Analizada: {indice_sel}
                ---------------------------------
                Notas: 
                - Este reporte confirma la visualización de 
                  datos Sentinel-2 L2A procesados para {depto_sel}.
                - El índice {indice_sel} fue generado dinámicamente.
                """

                # Creamos el botón de descarga
                st.download_button(
                    label=f"📥 Descargar Reporte {depto_sel}",
                    data=texto_reporte,
                    file_name=f"Reporte_{depto_sel}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                )
#==========================================================
# SECCIÓN: DIAGNÓSTICO IA (PLAGAS Y ENFERMEDADES)
# SECCIÓN: DIAGNÓSTICO IA (PLAGAS Y ENFERMEDADES)
# SECCIÓN: DIAGNÓSTICO IA (PLAGAS Y ENFERMEDADES)
# SECCIÓN: DIAGNÓSTICO IA (PLAGAS Y ENFERMEDADES)
# SECCIÓN: DIAGNÓSTICO IA (PLAGAS Y ENFERMEDADES)
# --- 1. CONFIGURACIÓN AL INICIO DEL ARCHIVO (Fuera de cualquier IF) ---
# SECCIÓN: DIAGNÓSTICO IA (PLAGAS Y ENFERMEDADES)
# --- 1. CONFIGURACIÓN AL INICIO DEL ARCHIVO (Fuera de cualquier IF) ---
#import google.generativeai as genai
#from PIL import Image
# SECCIÓN: DIAGNÓSTICO IA (PLAGAS Y ENFERMEDADES)
# --- 1. CONFIGURACIÓN AL INICIO DEL ARCHIVO (Fuera de cualquier IF) ---
# --- 2. SECCIÓN DEL MENÚ ---
if menu == "🔍 Diagnóstico IA":
    st.header("🔍 Laboratorio Móvil")
    
    # Verificamos que el cliente esté listo
    if client is None:
        st.error("🚨 La IA no está configurada correctamente. Revisa la conexión con Google GenAI.")
        st.stop()

    # 1. Inicializar session state para que el resultado no se borre
    if "resultado_analisis" not in st.session_state:
        st.session_state.resultado_analisis = None

    # 2. Selección de foto
    tab_cam, tab_gal = st.tabs(["📸 Cámara", "📁 Galería"])

    with tab_cam:
        img_camera = st.camera_input("Capturar síntoma")
    with tab_gal:
        img_upload = st.file_uploader("Subir foto", type=['jpg', 'jpeg', 'png'])

    # Elegir la imagen disponible
    foto_final = img_camera if img_camera else img_upload

    if foto_final:
        # Mostramos la imagen
        st.image(foto_final, caption="Muestra seleccionada", width='stretch')
        
        # 3. Botón de analizar (dentro del bloque de foto_final)
        if st.button("ANALIZAR", type="primary"):
            with st.status("Analizando...", expanded=True) as status:
                try:
                    from PIL import Image
                    import io

                    foto_final.seek(0)
                    imagen_bytes = foto_final.read()
                    imagen_pil = Image.open(io.BytesIO(imagen_bytes))

                    prompt = "Sos un agrónomo experto. Identificá plaga/enfermedad y sugerí tratamiento."

                    # Lógica de reintentos
                    for intento in range(3):
                        try:
                            response = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=[imagen_pil, prompt]
                            )
                            break
                        except Exception as e:
                            if "429" in str(e) and intento < 2:
                                st.warning(f"Límite de API, reintentando... ({intento+1}/3)")
                                import time
                                time.sleep(5)
                            else:
                                raise e

                    # Extraer texto de la respuesta
                    texto = ""
                    try:
                        texto = response.text
                    except:
                        try:
                            texto = response.candidates[0].content.parts[0].text
                        except:
                            texto = "⚠️ No se pudo extraer el texto."

                    # Guardar en session_state para persistencia
                    st.session_state.resultado_analisis = texto
                    status.update(label="✅ Análisis Completo", state="complete")

                except Exception as e:
                    st.error(f"Error en el análisis: {e}")
                    status.update(label="❌ Error", state="error")

    # 4. Mostrar resultado y botón de descarga
    if st.session_state.resultado_analisis:
        st.markdown("### 📋 Resultado del Análisis")
        st.markdown(st.session_state.resultado_analisis)

        # Nombre de archivo con fecha
        from datetime import datetime
        fecha_archivo = datetime.now().strftime("%Y%m%d_%H%M")
        nombre_archivo = f"diagnostico_agroguardian_{fecha_archivo}.pdf"

        # Nombre de imagen seguro
        nombre_img = foto_final.name if foto_final and hasattr(foto_final, 'name') else "imagen"

        # Generar PDF
        pdf_buffer = generar_pdf(
            st.session_state.resultado_analisis,
            nombre_imagen=nombre_img
        )

        st.download_button(
            label="📄 Descargar Informe PDF",
            data=pdf_buffer,
            file_name=nombre_archivo,
            mime="application/pdf"
        )

    st.divider()
    if st.button("🔄 REINICIAR"):
        st.session_state.resultado_analisis = None
        st.rerun()
