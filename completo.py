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
# ==========================================================
# 2. GEOLOCALIZACIÓN + CLIMA
# ==========================================================
import streamlit.components.v1 as components

st.markdown("### 📍 Ubicación")

# Botón GPS + display de coordenadas
    </script>
""", height=120)
// Reemplazá el bloque de script dentro del components.html por este:
function getLocation() {
    document.getElementById('status').innerText = '⏳ Buscando ubicación...';
    navigator.geolocation.getCurrentPosition(
        function(pos) {
            const lat = pos.coords.latitude.toFixed(6);
            const lon = pos.coords.longitude.toFixed(6);
            document.getElementById('status').innerText = '✅ Ubicación detectada:';
            document.getElementById('coords').innerHTML = 
                'LAT: ' + lat + '  |  LON: ' + lon + '<br><br>' +
                '<a href="?lat=' + lat + '&lon=' + lon + '" ' +
                'style="background:#00ffc3; color:#0d1117; padding:6px 14px; ' +
                'text-decoration:none; font-weight:bold; border-radius:4px;">'+
                '✅ CONFIRMAR Y CARGAR CLIMA</a>';
        },
        function(err) {
            document.getElementById('status').innerText = '❌ Error: ' + err.message;
        },
        {enableHighAccuracy: true, timeout: 10000}
    );
}
# Inputs de coordenadas (se rellenan solos con el botón o manualmente)
col1, col2 = st.columns(2)
with col1:
    lat_input = st.text_input("Latitud", value="-38.298", key="lat_input")
with col2:
    lon_input = st.text_input("Longitud", value="-58.208", key="lon_input")

try:
    LAT = float(lat_input)
    LON = float(lon_input)
    st.sidebar.success(f"📍 {round(LAT,4)}, {round(LON,4)}")
except:
    LAT, LON = -38.298, -58.208
    st.sidebar.warning("⚠️ Coordenadas inválidas, usando default")

# Función clima
def traer_datos(lat, lon):
    try:
        query = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
        r = requests.get(query)
        return r.json() if r.status_code == 200 else None
    except:
        return None

r_raw = traer_datos(LAT, LON)

if r_raw:
    st.session_state.clima_data = r_raw
    st.sidebar.write(f"🌍 {r_raw.get('name','')}, {r_raw.get('sys',{}).get('country','')}")

clima = {
    "temp":  r_raw["main"]["temp"] if r_raw and "main" in r_raw else 0,
    "hum":   r_raw["main"]["humidity"] if r_raw and "main" in r_raw else 0,
    "v_vel": round(r_raw["wind"]["speed"] * 3.6, 1) if r_raw and "wind" in r_raw else 0,
    "v_dir": r_raw["wind"]["deg"] if r_raw and "wind" in r_raw else 0
}
#==========================================================
# 3. SIDEBAR
# ==========================================================
with st.sidebar:
    st.markdown("## AG-TERMINAL v2.6")
    menu = st.radio(
        "SISTEMAS",
        ["📊 Monitoreo Total", "💧 Balance Hídrico", "🌧️ Pluviómetro", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora"]
    )

# ==========================================================
# 4. PÁGINAS (ESTRUCTURA CORREGIDA Y BLINDADA)
# ==========================================================
if menu == "📊 Monitoreo Total":
    st.header("📊 Tablero de Control Integral")
    
    # 1. MÉTRICAS DE CLIMA (Aseguramos que 'clima' exista)
    if 'clima' in locals() or 'clima' in globals():
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Temperatura", f"{clima.get('temp', 0)} °C")
        with col2:
            st.metric("Humedad", f"{clima.get('hum', 0)} %")
        with col3:
            st.metric("Viento", f"{clima.get('v_vel', 0)} km/h")
    
    st.divider()
    
elif menu == "🌧️ Pluviómetro":
    st.header("🌧️ Pluviómetro Digital")

    try:
        res = supabase.table("registros_lluvia").select("*").execute()

        if res.data and len(res.data) > 0:
            df = pd.DataFrame(res.data)
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['mm'] = pd.to_numeric(df['mm'], errors='coerce').fillna(0)
            hoy = datetime.datetime.now(datetime.timezone.utc)

            # ── MÉTRICAS RÁPIDAS ──────────────────────────────────────
            df_mes = df[(df['fecha'].dt.month == hoy.month) & (df['fecha'].dt.year == hoy.year)].copy()
            df_año = df[df['fecha'].dt.year == hoy.year].copy()
            df_7d = df[df['fecha'] >= (hoy - datetime.timedelta(days=7))].copy()

            acum_mes  = df_mes['mm'].sum()
            acum_año  = df_año['mm'].sum()
            acum_7d   = df_7d['mm'].sum()
            max_dia   = df_mes['mm'].max() if not df_mes.empty else 0
            ult_evento = df.sort_values('fecha', ascending=False).iloc[0]

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💧 Este Mes",     f"{acum_mes:.1f} mm")
            c2.metric("📅 Últimos 7 días", f"{acum_7d:.1f} mm")
            c3.metric("📆 Acum. Anual",  f"{acum_año:.1f} mm")
            c4.metric("⚡ Máx. en un día", f"{max_dia:.1f} mm")

            st.divider()

            # ── ÚLTIMO EVENTO ─────────────────────────────────────────
            st.markdown(f"""
            **🕒 Último registro:** `{ult_evento['fecha'].strftime('%d/%m/%Y')}`  &nbsp;|&nbsp;
            **Lote:** `{ult_evento.get('lote', '-')}`  &nbsp;|&nbsp;
            **Cantidad:** `{ult_evento['mm']:.1f} mm`
            """)

            st.divider()

            # ── ESTILO GRÁFICOS ───────────────────────────────────────
            estilo_grafico = dict(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#00ffc3"),
                dragmode=False,
                hovermode='x',
                height=350,
                margin=dict(l=10, r=10, t=10, b=20)
            )

            # ── GRÁFICO 1: DIARIO (mes actual) ────────────────────────
            st.subheader(f"📅 Registro Diario — {hoy.strftime('%B %Y')}")
            df_mes['dia'] = df_mes['fecha'].dt.day
            df_dia = df_mes.groupby('dia')['mm'].sum().reindex(range(1, 32), fill_value=0).reset_index()

            fig1 = px.bar(df_dia, x='dia', y='mm', template="plotly_dark")
            fig1.update_traces(marker_color='#1f77b4', hovertemplate="<b>Día %{x}</b><br>%{y} mm<extra></extra>")
            fig1.update_layout(**estilo_grafico,
                xaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, 31.5], fixedrange=True, title=None))
            fig1.update_xaxes(showspikes=False)
            fig1.update_yaxes(showspikes=False)
            st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})

            # ── GRÁFICO 2: MENSUAL (año actual) ──────────────────────
            st.subheader(f"📊 Acumulado Mensual — {hoy.year}")
            meses_letras = ['E','F','M','A','M','J','J','A','S','O','N','D']
            mensual = df_año.groupby(df_año['fecha'].dt.month)['mm'].sum().reindex(range(1, 13), fill_value=0)
            df_anual = pd.DataFrame({'Mes': meses_letras, 'mm': mensual.values})

            fig2 = px.bar(df_anual, x='Mes', y='mm', template="plotly_dark")
            fig2.update_traces(marker_color='#00ffc3', hovertemplate="<b>%{x}</b><br>%{y} mm<extra></extra>")
            fig2.update_layout(**estilo_grafico,
                xaxis=dict(fixedrange=True, categoryorder='array', categoryarray=meses_letras, title=None))
            fig2.update_xaxes(showspikes=False)
            fig2.update_yaxes(showspikes=False)
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

            # ── GRÁFICO 3: LÍNEA HISTÓRICA ────────────────────────────
            st.subheader("📈 Historial de Precipitaciones")
            df_hist = df.groupby(df['fecha'].dt.to_period('M'))['mm'].sum().reset_index()
            df_hist['fecha'] = df_hist['fecha'].dt.to_timestamp()

            fig3 = px.line(df_hist, x='fecha', y='mm', template="plotly_dark", markers=True)
            fig3.update_traces(line_color='#00ffc3', marker_color='#ffffff',
                               hovertemplate="<b>%{x|%b %Y}</b><br>%{y} mm<extra></extra>")
            fig3.update_layout(**estilo_grafico, xaxis=dict(fixedrange=True, title=None))
            fig3.update_xaxes(showspikes=False)
            fig3.update_yaxes(showspikes=False)
            st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

            # ── TABLA DE REGISTROS ────────────────────────────────────
            with st.expander("📂 Ver Planilla Completa de Registros"):
                cols_mostrar = [c for c in ['fecha', 'lote', 'mm'] if c in df.columns]
                st.dataframe(
                    df[cols_mostrar].sort_values('fecha', ascending=False),
                    use_container_width=True
                )

        else:
            st.info("🛰️ No hay registros de lluvia cargados todavía.")

    except Exception as e:
        st.error(f"Error en Pluviómetro: {e}")

    

# Aquí seguirían los otros ELIF alineados con el IF de arriba

elif menu == "💧 Balance Hídrico":
    st.markdown("### 💧 CÁLCULO DE PRECISIÓN (Blaney-Criddle)")
    
    try:
        import math
        # 1. RECUPERAR DATOS (Ya vienen de Supabase/OpenWeather al inicio)
        if 'clima_data' in st.session_state:
            temp_media = st.session_state.clima_data['main']['temp']
            lat = float(st.session_state.clima_data['coord']['lat']) # <--- GPS REAL
            fuente = "📡 OpenWeather (Tiempo Real)"
        else:
            temp_media, lat = 25.0, -38.29 # Fallback
            fuente = "⚠️ Valor Estimado"

        # 2. CÁLCULO CIENTÍFICO DEL FACTOR 'p'
        # Calculamos el día del año (1-365)
        doy = datetime.datetime.now().timetuple().tm_yday
        
        # El factor p depende de la insolación diaria. 
        # Una aproximación robusta para Blaney-Criddle es:
        # p = (Horas de luz diarias / Horas de luz anuales) * 100
        # Calculamos la declinación solar (delta)
        delta = 0.409 * math.sin((2 * math.pi * doy / 365) - 1.39)
        
        # Ángulo horario del atardecer (ws)
        lat_rad = math.radians(lat)
        # Evitamos errores matemáticos en los polos
        arg = -math.tan(lat_rad) * math.tan(delta)
        ws = math.acos(max(-1, min(1, arg)))
        
        # Horas de luz máximas (N)
        N = (24 / math.pi) * ws
        
        # El factor 'p' para la fórmula de Blaney-Criddle (diario)
        # Se estima como el porcentaje de horas de luz sobre el total del año
        p_diario = (N / 4380) * 100 # 4380 son las horas de luz promedio anual

        # 3. CÁLCULO DE ETo DIARIA
        # ETo = p * (0.46 * T + 8)
        eto_diaria = p_diario * (0.46 * temp_media + 8)

        # 4. INTERFAZ PROFESIONAL
        st.success(f"📍 GPS detectado: {lat:.4f} | Factor de Luz (p): {p_diario:.4f}")
        
        kc = st.slider("Kc del Cultivo (Estado actual)", 0.3, 1.2, 0.8)
        etc = eto_diaria * kc

        c1, col_gap, c2 = st.columns([1, 0.1, 1])
        with c1:
            st.metric("Demanda Ambiental (ETo)", f"{eto_diaria:.2f} mm/día")
        with c2:
            st.metric("Consumo Cultivo (ETc)", f"{etc:.2f} mm/día", delta=f"Kc: {kc}", delta_color="normal")

        # Visualización gráfica del balance
        st.progress(min(etc / 10.0, 1.0)) 
        st.caption(f"Consumo de agua basado en {temp_media}°C y latitud {lat:.1f}°")

    except Exception as e:
        st.error(f"Error en el cálculo astronómico: {e}")
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
