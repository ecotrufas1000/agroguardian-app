import streamlit as st
from supabase import create_client
from streamlit_folium import folium_static
import folium
import requests
import json
import math
import os 
import streamlit as st
# CSS para ocultar TODO lo que marcaste en amarillo
st.markdown("""
    <style>
        /* 1. Oculta el Header (GitHub y menú superior) */
        [data-testid="stHeader"] {display: none !important;}
        
        /* 2. Oculta el Footer (Made with Streamlit) */
        footer {visibility: hidden !important;}

        /* 3. ELIMINA LO QUE MARCASTE ABAJO A LA DERECHA */
        /* Esto quita el botón de 'Manage app' y el estado del servidor */
        [data-testid="stStatusWidget"] {display: none !important;}
        .stStatusWidget {display: none !important;}
        
        /* 4. Limpieza extra de márgenes */
        .block-container {padding-top: 0rem !important; padding-bottom: 0rem !important;}
    </style>
""", unsafe_allow_html=True)
# ==========================================================
# 1. CONEXIÓN A DATOS (MOTOR) - ESTO VA PRIMERO
# ==========================================================
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase = create_client(url, key)

# Conexión a Clima
API_KEY = st.secrets["OPENWEATHER_API_KEY"]
BITACORA_JSON = "bitacora.json"

# ==========================================================
# 2. OBTENCIÓN DE UBICACIÓN (ARRANQUE)
# ==========================================================
def obtener_posicion_dinamica():
    try:
        # Buscamos el último registro que tenga coordenadas válidas
        res = supabase.table("registros_lluvia").select("lat, lon").order("id", desc=True).limit(1).execute()
        
        if res.data and res.data[0].get('lat'):
            return float(res.data[0]['lat']), float(res.data[0]['lon'])
    except Exception as e:
        # Si algo falla, no bloqueamos la app
        pass
    
    # Ubicación fija por defecto (Respaldo)
    return -38.298, -58.208 

# Asignamos las variables que usará el mapa y el clima
LAT, LON = obtener_posicion_dinamica()
BITACORA_JSON = "bitacora.json" # Definimos la variable para que no de error al final

# ==========================================================
# 2. CONFIGURACIÓN DE PÁGINA (Debe ir antes de cualquier st.markdown)
# ==========================================================
st.set_page_config(
    page_title="AgroGuardian Pro", 
    layout="wide", 
    initial_sidebar_state="expanded",
    page_icon="🛰️"
)

# 3. Inyección de CSS para estética "Dark Terminal"
st.markdown("""
    <style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    [data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363d; }
    h1, h2, h3, p { color: #00ffc3 !important; font-family: 'Courier New', monospace; }
    .terminal-header {
        background-color: #161b22;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #00ffc3;
        font-family: 'Courier New', monospace;
        color: #00ffc3;
        margin-bottom: 20px;
    }
    [data-testid="stMetricValue"] { color: #00ffc3 !important; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #21262d; color: #00ffc3; border: 1px solid #30363d; }
    .stButton>button:hover { border-color: #00ffc3; box-shadow: 0px 0px 10px #00ffc3; }
    </style>
    """, unsafe_allow_html=True)
# 2. Inyección de CSS para estética "Dark Terminal"
st.markdown("""
    <style>
    /* Fondo principal y de barra lateral */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    [data-testid="stSidebar"] {
        background-color: #010409;
        border-right: 1px solid #30363d;
    }
    
    /* Estética de títulos y cabeceras */
    h1, h2, h3, p {
        color: #00ffc3 !important;
        font-family: 'Courier New', Courier, monospace;
    }

    /* Estilo para el encabezado tipo Terminal */
    .terminal-header {
        background-color: #161b22;
        padding: 15px;
        border-radius: 5px;
        border-left: 5px solid #00ffc3;
        font-family: 'Courier New', Courier, monospace;
        color: #00ffc3;
        margin-bottom: 20px;
    }

    /* Personalización de métricas */
    [data-testid="stMetricValue"] {
        color: #00ffc3 !important;
        font-family: 'Courier New', monospace;
    }
    
    /* Botones estilo neón */
    .stButton>button {
        background-color: #21262d;
        color: #00ffc3;
        border: 1px solid #30363d;
        border-radius: 5px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        border-color: #00ffc3;
        box-shadow: 0px 0px 10px #00ffc3;
        color: #00ffc3;
    }
    
    /* Líneas separadoras */
    hr {
        border: 0;
        height: 1px;
        background: #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================================
# 3. FUNCIONES CIENTÍFICAS
# ==========================================================
def obtener_direccion_viento(grados):
    val = int((grados / 22.5) + 0.5)
    direcciones = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                   "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
    return direcciones[val % 16]

def calcular_punto_rocio(T, HR):
    a, b = 17.27, 237.7
    alpha = ((a * T) / (b + T)) + math.log(HR/100.0)
    return round((b * alpha) / (a - alpha), 1)

def calcular_gdc_diario(t_max, t_min, t_base=10):
    return max(0, ((max(t_max, t_base) + max(t_min, t_base)) / 2) - t_base)

def cargar_memoria():
    if os.path.exists("memoria_lotes.json"):
        with open("memoria_lotes.json", "r", encoding="utf-8") as f:
            full_data = json.load(f)
            if full_data:
                first_key = list(full_data.keys())[0]
                return full_data.get(first_key, {})
    return {}

@st.cache_data(ttl=600)
def traer_datos(lat, lon):
    try:
        return requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
        ).json()
    except:
        return None

# ==========================================================
# 4. CARGA DE DATOS
# ==========================================================
datos_memoria = cargar_memoria()
r_raw = traer_datos(LAT, LON)

if not r_raw:
    st.error("🚨 ERROR: No se detecta respuesta meteorológica.")
    st.stop()

clima = {
    "temp": r_raw["main"]["temp"],
    "t_max": r_raw["main"]["temp_max"],
    "t_min": r_raw["main"]["temp_min"],
    "hum": r_raw["main"]["humidity"],
    "v_vel": round(r_raw["wind"]["speed"] * 3.6, 1),
    "v_dir": r_raw["wind"]["deg"],
    "desc": r_raw["weather"][0]["description"].capitalize(),
    "presion": r_raw["main"].get("pressure", 1013.2)
}

t_dp = calcular_punto_rocio(clima['temp'], clima['hum'])
gdc_hoy = calcular_gdc_diario(clima['t_max'], clima['t_min'])
v_rumbo = obtener_direccion_viento(clima['v_dir'])

# ==========================================================
# 5. SIDEBAR
# ==========================================================
with st.sidebar:
    st.markdown("## AG-TERMINAL v2.6")
    menu = st.radio(
        "SISTEMAS",
        [
            "📊 Monitoreo Total",
            "💧 Balance Hídrico",
            "🌧️ Pluviómetro",
            "⛈️ Radar Granizo",
            "❄️ Análisis de Heladas",
            "📝 Bitácora"
        ]
    )
    if st.button("🔄 RE-SCAN"):
        st.rerun()

# ==========================================================
# 6. PÁGINAS
# ==========================================================

# -------------------------
# MONITOREO
# -------------------------
if menu == "📊 Monitoreo Total":

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("TEMPERATURA", f"{clima['temp']}°C")
    c2.metric("PTO. ROCÍO", f"{t_dp}°C")
    c3.metric("GDC (B10)", f"{gdc_hoy:.1f}")
    c4.metric("HUMEDAD", f"{clima['hum']}%")
    c5.metric("VIENTO", f"{clima['v_vel']} km/h", v_rumbo)

    st.divider()

    col_map, col_wind = st.columns([2,1])

    with col_map:
        m = folium.Map(location=[LAT, LON], zoom_start=15)
        folium.TileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri'
        ).add_to(m)
        folium_static(m, width=700, height=400)

    with col_wind:
        st.metric("Dirección", f"{clima['v_dir']}°", v_rumbo)

# -------------------------
# HELADAS
# -------------------------
elif menu == "❄️ Análisis de Heladas":

    dif = 3.5 if clima['v_vel'] < 5 else 1.2
    st.metric("Temp. Suelo (Est.)", f"{round(clima['temp'] - dif, 1)}°C")

    if t_dp <= 0:
        st.error(f"HELADA NEGRA: Punto de rocío {t_dp}°C")
    elif clima['temp'] < 3:
        st.warning("RIESGO DE HELADA BLANCA")
    else:
        st.success("Sin riesgo inmediato")

# PLUVIÓMETRO (Versión Pro con Supabase)
# -------------------------
elif menu == "🌧️ Pluviómetro":
    st.markdown('<p style="color:#00ffc3; font-size:20px; font-weight:bold; font-family:monospace;">Hydraulic Records // Pluviometer Data</p>', unsafe_allow_html=True)
    
    try:
        import pandas as pd
        import plotly.express as px
        import datetime

        # 1. Recuperar datos
        res = supabase.table("registros_lluvia").select("*").order("fecha", desc=False).execute()
        
        if not res.data:
            st.info("📍 No hay registros de lluvia.")
        else:
            df = pd.DataFrame(res.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['mm'] = pd.to_numeric(df['mm'], errors='coerce')
            df['mes_nombre'] = df['fecha'].dt.strftime('%b %Y')
            df['mes_idx'] = df['fecha'].dt.to_period('M').astype(str)

            # --- MÉTRICAS ---
            hoy = datetime.datetime.now()
            mes_actual_str = hoy.strftime("%Y-%m")
            total_mes = df[df['fecha'].dt.strftime("%Y-%m") == mes_actual_str]['mm'].sum()
            total_año = df[df['fecha'].dt.year == hoy.year]['mm'].sum()

            c1, c2, c3 = st.columns(3)
            c1.metric("ESTE MES", f"{total_mes:.1f} mm")
            c2.metric("TOTAL ANUAL", f"{total_año:.1f} mm")
            c3.metric("REGISTROS", f"{len(df)}")

            st.divider()

            # --- GRÁFICO 1: DIARIO (MES EN CURSO) ---
            st.subheader(f"📅 Detalle Diario: {hoy.strftime('%B %Y')}")
            
            # 1. Determinar cuántos días tiene el mes actual
            import calendar
            ultimo_dia = calendar.monthrange(hoy.year, hoy.month)[1]
            dias_del_mes = list(range(1, ultimo_dia + 1))
            
            # 2. Filtrar datos del mes actual y agrupar por día
            df['dia_num'] = df['fecha'].dt.day
            resumen_diario = df[df['mes_idx'] == mes_actual_str].groupby('dia_num')['mm'].sum().reset_index()
            
            # 3. Crear DataFrame base con todos los días del mes
            df_mes_completo = pd.DataFrame({'dia_num': dias_del_mes})
            df_diario_final = pd.merge(df_mes_completo, resumen_diario, on='dia_num', how='left').fillna(0)
            
            # 4. Configurar el Gráfico Diario
            fig_diario = px.bar(
                df_diario_final, 
                x='dia_num', 
                y='mm',
                title="Lluvias por día",
                text_auto='.0f',
                template="plotly_dark"
            )
            
            # 5. Estética idéntica al Anual
            fig_diario.update_traces(
                marker_color='#3d5afe', # Mismo azul que el anual
                opacity=0.8,
                width=0.6 # Ancho estilizado
            )
            
            fig_diario.update_layout(
                xaxis=dict(
                    tickmode='array', # Cambiamos a modo array para elegir exacto qué mostrar
                    tickvals=[1, 5, 10, 15, 20, 25, ultimo_dia], # Mostramos los hitos y el último día
                    ticktext=['1', '5', '10', '15', '20', '25', str(ultimo_dia)],
                    title="Día del Mes",
                    tickangle=0,
                    tickfont=dict(size=12, color='#00ffc3') # Un toque de color para que resalten
                ),
                yaxis=dict(
                    range=[0, max(df_diario_final['mm'].max() * 1.3, 30)],
                    title="Milímetros",
                    gridcolor='#30363d'
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                bargap=0.2 # Reducimos un poco el gap para que las barras no sean hilos
            )
            
            st.plotly_chart(fig_diario, use_container_width=True, config={'staticPlot': True})
            st.divider()
# --- GRÁFICO 2: MENSUAL (TODO EL AÑO) ---
            st.subheader("📊 Acumulados Mensuales")
            
            # 1. Nombres y lista de base
            meses_letras = ['E', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
            
            # 2. Agrupar datos por mes de los registros actuales
            df['mes_num'] = df['fecha'].dt.month
            resumen_anual = df[df['fecha'].dt.year == hoy.year].groupby('mes_num')['mm'].sum().reset_index()
            
            # 3. Crear DataFrame con los 12 meses (asegurando que todos existan)
            df_doce = pd.DataFrame({'mes_num': range(1, 13), 'letra': meses_letras})
            df_final = pd.merge(df_doce, resumen_anual, on='mes_num', how='left').fillna(0)
            
            # 4. Configurar el Gráfico
            fig_mensual = px.bar(
                df_final, 
                x='mes_num', # Usamos el número para el eje X internamente
                y='mm',
                title=f"Acumulado Mensual {hoy.year}",
                text_auto='.0f',
                template="plotly_dark"
            )
            
            # 5. El Truco: Cambiamos las etiquetas del eje X (números por letras)
            fig_mensual.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=list(range(1, 13)),
                    ticktext=meses_letras, # Aquí le decimos que muestre las letras
                    title="Mes"
                ),
                yaxis=dict(
                    range=[0, max(df_final['mm'].max() * 1.3, 50)], # Siempre desde 0
                    title="Milímetros",
                    gridcolor='#30363d'
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                bargap=0.4
            )
            
            fig_mensual.update_traces(
                marker_color='#3d5afe', 
                opacity=0.8,
                width=0.6
            )
            
            st.plotly_chart(fig_mensual, use_container_width=True, config={'staticPlot': True})
            # Tabla oculta por si querés ver los números exactos
            with st.expander("📝 Ver todos los registros (Historial completo)"):
                st.dataframe(df[['fecha', 'lote', 'mm']].sort_values('fecha', ascending=False), use_container_width=True)
            
    except Exception as e:
        st.error(f"Error al procesar gráficos: {e}")

# -------------------------
# BALANCE HÍDRICO
# -------------------------
elif menu == "💧 Balance Hídrico":

    kc = st.slider("Kc del Cultivo", 0.3, 1.2, 0.8)
    st.metric("ETc", f"{round(4.8 * kc, 2)} mm/día")

# -------------------------
# RADAR GRANIZO
# -------------------------
elif menu == "⛈️ Radar Granizo":

    c1, c2, c3 = st.columns(3)
    c1.metric("PRESIÓN", f"{clima['presion']} hPa")
    c2.metric("HUMEDAD", f"{clima['hum']}%")
    c3.metric("ESTADO", "ONLINE")

    windy_url = f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&overlay=radar"
    st.components.v1.iframe(windy_url, height=600)

    if clima['presion'] < 1010 and clima['hum'] > 80:
        st.error("⚠️ Condiciones favorables para granizo")

# -------------------------
# BITÁCORA
# -------------------------
elif menu == "📝 Bitácora":

    if os.path.exists(BITACORA_JSON):
        with open(BITACORA_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            for uid, eventos in data.items():
                for e in reversed(eventos[-15:]):
                    st.write(f"{e['fecha']} - {e['lote']} → {e['detalle']}")
                    import datetime
import datetime

# --- PIE DE PÁGINA PROFESIONAL ---
st.sidebar.markdown("---")

# Agrupamos Indicador y Fecha en una sola columna para ahorrar espacio
col1, col2 = st.sidebar.columns([1, 3])
with col1:
    st.markdown(
        """<div style='height: 12px; width: 12px; background-color: #4eff4e; border-radius: 50%; margin-top: 5px; box-shadow: 0 0 5px #4eff4e;'></div>""", 
        unsafe_allow_html=True
    )
with col2:
    st.markdown("<span style='color: #4eff4e; font-family: monospace; font-size: 14px;'>SYS ONLINE</span>", unsafe_allow_html=True)

# Fecha de sincronización
fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
st.sidebar.caption(f"📅 Sincro: {fecha_actual}")

st.sidebar.write("") # Espacio en blanco

# BOTÓN DE SOPORTE (Usando la función oficial de Streamlit para que no falle)
numero_soporte = "5491100000000"  # <-- CAMBIÁ ESTE NÚMERO
texto_wa = "Hola! Necesito asistencia técnica con AgroGuardian."
url_wa = f"https://wa.me/{numero_soporte}?text={texto_wa.replace(' ', '%20')}"

st.sidebar.link_button("🆘 SOPORTE TÉCNICO", url_wa, use_container_width=True)

# Copyright final
st.sidebar.markdown(
    """
    <div style='font-family: monospace; font-size: 10px; color: gray; text-align: center; margin-top: 20px;'>
        © 2026 AGRO-GUARDIAN TERMINAL<br>
        V 2.6.0
    </div>
    """, 
    unsafe_allow_html=True
)
