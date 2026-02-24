import streamlit as st
from supabase import create_client
from streamlit_folium import folium_static
import folium
import requests
import json
import os
import math
import datetime
import pandas as pd
import plotly.express as px

# ==========================================================
# 1. CONFIGURACIÓN BASE Y ESTILO TERMINAL
# ==========================================================
st.set_page_config(
    page_title="AgroGuardian Pro | Lab Terminal",
    layout="wide",
    page_icon="🛰️"
)

st.markdown("""
    <style>
        .stApp { background-color: #0d1117 !important; color: #00ffc3 !important; }
        [data-testid="stSidebar"] { background-color: #010409 !important; border-right: 1px solid #30363d; }
        
        /* FLECHA VERDE NEÓN */
        header [data-testid="stHeaderActionElements"] button, 
        [data-testid="stSidebarCollapseIcon"],
        .st-emotion-cache-6qob1r { 
            color: #00ffc3 !important; 
            fill: #00ffc3 !important;
        }

        h1, h2, h3, p, label, .stMarkdown {
            color: #00ffc3 !important;
            font-family: 'Courier New', monospace !important;
        }

        [data-testid="stMetricValue"] {
            color: #00ffc3 !important;
            text-shadow: 0px 0px 10px #00ffc3;
        }
        
        .stDataFrame, [data-testid="stTable"] { background-color: #0d1117 !important; }
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================================
# ==========================================================
# 2. CONEXIÓN Y DATOS
# ==========================================================
url = "https://ieodzygauglvdkendvmj.supabase.co"
key = "sb_publishable_YS3LTJInGQZgxw0cZmTCZw_4rFz1Oaq"
supabase = create_client(url, key)
API_KEY = st.secrets["OPENWEATHER_API_KEY"]

# --- NUEVA LÓGICA: BUSCAR GPS EN SUPABASE ---
try:
    # Traemos el último registro de la tabla configuración
    res_gps = supabase.table("configuracion").select("latitud", "longitud").order("id", desc=True).limit(1).execute()
    
    if res_gps.data:
        LAT = res_gps.data[0]['latitud']
        LON = res_gps.data[0]['longitud']
    else:
        # Coordenadas por defecto si la tabla está vacía
        LAT, LON = -38.298, -58.208 
except Exception:
    LAT, LON = -38.298, -58.208

@st.cache_data(ttl=600)
def traer_datos(lat, lon):
    try:
        res = requests.get(f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es")
        return res.json()
    except: 
        return None

# Llamada a los datos
r_raw = traer_datos(LAT, LON)

# Guardamos en session_state para que el Balance Hídrico lo use después
if r_raw:
    st.session_state.clima_data = r_raw

clima = {
    "temp": r_raw["main"]["temp"] if r_raw and "main" in r_raw else 0,
    "hum": r_raw["main"]["humidity"] if r_raw and "main" in r_raw else 0,
    "v_vel": round(r_raw["wind"]["speed"] * 3.6, 1) if r_raw and "wind" in r_raw else 0,
    "v_dir": r_raw["wind"]["deg"] if r_raw and "wind" in r_raw else 0
}# ==========================================================
# 3. SIDEBAR
# ==========================================================
with st.sidebar:
    st.markdown("## AG-TERMINAL v2.6")
    menu = st.radio(
        "SISTEMAS",
        ["📊 Monitoreo Total", "💧 Balance Hídrico", "🌧️ Pluviómetro", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora"]
    )

# ==========================================================
# 4. PÁGINAS (PLUVIÓMETRO RESTAURADO)
# ==========================================================

if menu == "📊 Monitoreo Total":
    c1, c2, c3 = st.columns(3)
    c1.metric("TEMPERATURA", f"{clima['temp']}°C")
    c2.metric("HUMEDAD", f"{clima['hum']}%")
    c3.metric("VIENTO", f"{clima['v_vel']} km/h")
    st.divider()
    m = folium.Map(location=[LAT, LON], zoom_start=15)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    folium_static(m, width=700, height=400) 
elif menu == "🌧️ Pluviómetro":
    st.markdown("### 🌧️ ANALÍTICA DE PRECIPITACIONES")
    try:
        import datetime
        import pandas as pd
        import plotly.express as px

        res = supabase.table("registros_lluvia").select("*").order("fecha", desc=False).execute()
        
        if res.data:
            df = pd.DataFrame(res.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['mm'] = pd.to_numeric(df['mm'])
            hoy = datetime.datetime.now()

            df_año_actual = df[df['fecha'].dt.year == hoy.year].copy()
            mensual_sum = df_año_actual.groupby(df_año_actual['fecha'].dt.month)['mm'].sum().reindex(range(1, 13), fill_value=0)
            
            acum_mes = mensual_sum[hoy.month]
            acum_año = mensual_sum.sum()

            df_mes_actual = df[(df['fecha'].dt.month == hoy.month) & (df['fecha'].dt.year == hoy.year)].copy()
            df_mes_actual['dia'] = df_mes_actual['fecha'].dt.day
            df_dia_fijo = df_mes_actual.groupby('dia')['mm'].sum().reindex(range(1, 32), fill_value=0).reset_index()

            meses_letras = ['E', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']
            df_anual_fijo = pd.DataFrame({'Mes': meses_letras, 'mm': mensual_sum.values})

            c1, c2, c3 = st.columns(3)
            c1.metric("ESTE MES", f"{acum_mes:.1f} mm")
            c2.metric("ANUAL", f"{acum_año:.1f} mm")
            c3.metric("MÁX. DÍA", f"{df_mes_actual['mm'].max() if not df_mes_actual.empty else 0:.1f} mm")

            st.divider()

           # --- CONFIGURACIÓN DE ESTILO PARA AMBOS GRÁFICOS ---
            estilo_grafico = dict(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',  
                font=dict(color="#00ffc3"),     
                dragmode=False,
                hovermode='x', # <--- CAMBIAMOS 'x unified' por solo 'x' para que no dibuje la barra blanca
                height=350,
                margin=dict(l=10, r=10, t=10, b=20)
            )

            # --- GRÁFICO 1: DIARIO ---
            st.subheader(f"📅 Registro Diario: {hoy.strftime('%B %Y')}")
            fig1 = px.bar(df_dia_fijo, x='dia', y='mm', template="plotly_dark")
            
            # Quitamos las líneas blancas (spikes) de raíz
            fig1.update_xaxes(showspikes=False)
            fig1.update_yaxes(showspikes=False)

            fig1.update_traces(
                marker_color='#1f77b4',
                hovertemplate="<b>Día %{x}</b><br>%{y} mm<extra></extra>" 
            ) 
            fig1.update_layout(
                **estilo_grafico,
                hoverlabel=dict(bgcolor="#161b22", font_size=13, font_family="Courier New", font_color="#00ffc3"),
                xaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, 31.5], fixedrange=True, tickangle=0, tickfont=dict(size=9), title=None),
                yaxis=dict(fixedrange=True, title=None, tickfont=dict(size=10), gridcolor="#30363d")
            )
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

            # --- GRÁFICO 2: ANUAL ---
            st.subheader(f"📊 Acumulado Mensual {hoy.year}")
            fig2 = px.bar(df_anual_fijo, x='Mes', y='mm', template="plotly_dark")
            
            # Quitamos las líneas blancas aquí también
            fig2.update_xaxes(showspikes=False)
            fig2.update_yaxes(showspikes=False)

            fig2.update_traces(
                marker_color='#1f77b4',
                hovertemplate="<b>Mes %{x}</b><br>%{y} mm<extra></extra>"
            )
            fig2.update_layout(
                **estilo_grafico,
                hoverlabel=dict(bgcolor="#161b22", font_size=13, font_family="Courier New", font_color="#00ffc3"),
                xaxis=dict(fixedrange=True, categoryorder='array', categoryarray=meses_letras, tickangle=0, tickfont=dict(size=10), title=None),
                yaxis=dict(fixedrange=True, title=None, tickfont=dict(size=10), gridcolor="#30363d")
            )
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
            st.divider()
            with st.expander("📂 ACCEDER A REGISTROS CRUDOS (PLANILLA)"):
                st.dataframe(df[['fecha', 'lote', 'mm']].sort_values('fecha', ascending=False), use_container_width=True)

        else:
            st.info("🛰️ Esperando sincronización de datos o sin registros...")
            
    except Exception as e:
        st.error(f"Error en el sistema de analítica: {e}")

elif menu == "💧 Balance Hídrico":
    st.markdown("### 💧 CÁLCULO DE PRECISIÓN (Blaney-Criddle)")
    
    try:
        import math
        # 1. RECUPERAR DATOS DE OPENWEATHER (Usando las variables que ya tenés al inicio)
        # Asumimos que al inicio de tu app guardaste los datos en st.session_state o variables locales
        # Si ya hiciste el pedido a OpenWeather, usamos esos valores:
        
        if 'clima_data' in st.session_state:
            temp_media = st.session_state.clima_data['main']['temp']
            lat = st.session_state.clima_data['coord']['lat']
            fuente = "📡 OpenWeather (Tiempo Real)"
        else:
            # Opción de respaldo si no hay datos en sesión
            temp_media = 25.0
            lat = -34.6
            fuente = "⚠️ Valor Estimado (Sin conexión)"

        # 2. CÁLCULO MATEMÁTICO DEL FACTOR 'p' (Horas de luz según Latitud)
        # El factor p diario depende del día del año y la latitud
        doy = datetime.datetime.now().timetuple().tm_yday
        # Fórmula simplificada para el porcentaje de horas de luz diaria
        p_diario = (0.27 * (1 - (lat / 90) * math.cos(2 * math.pi * doy / 365))) / 30

        # 3. CÁLCULO DE ETo (Blaney-Criddle)
        # ETo diaria = p * (0.46 * T + 8)
        # Nota: Multiplicamos por la constante para ajustar a mm/día
        eto_diaria = p_diario * (0.46 * temp_media + 8) * 30 / 3.2 # Ajuste de calibración para la zona

        # 4. INTERFAZ DE USUARIO
        st.success(f"📍 Ubicación: {lat:.4f} | 🌡️ Temp ({fuente}): {temp_media}°C")
        
        kc = st.slider("Kc del Cultivo (Estado Fenológico)", 0.3, 1.2, 0.8, 
                       help="0.3: Emergencia | 0.8: Crecimiento | 1.15: Floración/Llenado")
        
        etc = eto_diaria * kc

        # Muestra de resultados
        col1, col2, col3 = st.columns(3)
        col1.metric("ETo (Ambiente)", f"{eto_diaria:.2f} mm")
        col2.metric("Kc (Cultivo)", f"{kc:.2f}")
        col3.metric("ETc (Gasto)", f"{etc:.2f} mm", delta=f"-{etc:.1f}", delta_color="inverse")

        st.divider()
        
        # Recomendación técnica
        if etc > 5:
            st.warning(f"🚩 **Alerta de Estrés:** El consumo es alto ({etc:.2f} mm). Verificá humedad en el perfil.")
        else:
            st.info(f"✅ **Consumo moderado:** La demanda hídrica hoy es de {etc:.2f} mm.")

    except Exception as e:
        st.error(f"Error en el motor de cálculo: {e}")

elif menu == "⛈️ Radar Granizo":
    st.components.v1.iframe(f"https://embed.windy.com/embed2.html?lat={LAT}&lon={LON}&zoom=8&overlay=radar", height=600)

elif menu == "❄️ Análisis de Heladas":
    st.metric("Riesgo Térmico", f"{clima['temp']}°C")
    if clima['temp'] < 3: st.warning("ALERTA DE HELADA")
    else: st.success("Sin riesgo")

elif menu == "📝 Bitácora":
    st.write("Módulo de bitácora activo.")

# --- FOOTER DE CONEXIÓN Y SOS CON HORA ARGENTINA ---
st.sidebar.divider() 

# Ajuste manual de -3 horas para Argentina
ahora_utc = datetime.datetime.now()
hora_argentina = ahora_utc - datetime.timedelta(hours=3) # <--- ESTO RESTA LAS 3 HORAS
fecha_formateada = hora_argentina.strftime("%d/%m/%Y %H:%M")

# 1. Reloj de Sistema
st.sidebar.markdown(f"""
    <div style='text-align: center; color: #00ffc3; font-family: monospace; font-size: 0.8em; letter-spacing: 1px;'>
        🛰️ SISTEMA ONLINE (GMT-3)<br>
        <span style="font-size: 1.2em;">{fecha_formateada}</span>
    </div>
""", unsafe_allow_html=True)
# 2. Botón SOS WhatsApp
st.sidebar.markdown("---")
numero_sos = "5491122334455" # <--- REEMPLAZA CON TU NÚMERO (Sin el +)
mensaje_sos = "🚨 *AgroGuardian SOS:* Necesito asistencia inmediata en el lote."

link_whatsapp = f"https://wa.me/{numero_sos}?text={mensaje_sos.replace(' ', '%20')}"

st.sidebar.markdown(f"""
    <a href="{link_whatsapp}" target="_blank" style="text-decoration: none;">
        <div style="
            background-color: #25D366;
            color: white;
            padding: 12px;
            text-align: center;
            border-radius: 10px;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        ">
            🟢 SOS WHATSAPP
        </div>
    </a>
""", unsafe_allow_html=True)
