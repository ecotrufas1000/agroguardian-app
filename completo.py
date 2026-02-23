import streamlit as st
from supabase import create_client
from streamlit_folium import folium_static
import folium
import requests
import math
import os

# 1️⃣ CONFIGURACIÓN BÁSICA
st.set_page_config(
    page_title="AgroGuardian Pro",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2️⃣ ESTILOS
st.markdown("""
<style>
header, [data-testid="stHeader"], footer {visibility: hidden; display: none !important;}
.stApp { background-color: #0d1117; color: #c9d1d9; }
[data-testid="stSidebar"] { background-color: #010409; border-right: 1px solid #30363d; }
h1, h2, h3, p { color: #00ffc3 !important; font-family: 'Courier New', monospace; }
.block-container { padding-top: 0rem !important; padding-bottom: 1rem !important; }
.stButton>button {
    background-color: #21262d;
    color: #00ffc3;
    border: 1px solid #30363d;
    border-radius: 5px;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# 3️⃣ SESSION STATE PARA NAVEGACIÓN
if "menu_principal" not in st.session_state:
    st.session_state.menu_principal = "📊 Monitoreo Total"
if "volver_menu" not in st.session_state:
    st.session_state.volver_menu = False

# 4️⃣ SIDEBAR
with st.sidebar:
    st.markdown("## AG-TERMINAL v2.6")

    # Botón “volver al panel principal”
    if st.button("⬅️ VOLVER AL PANEL", use_container_width=True):
        st.session_state.menu_principal = "📊 Monitoreo Total"
        st.rerun()

    # Menú lateral con radio buttons reflejando la sección actual
    menu = st.radio(
        "SISTEMAS",
        ["📊 Monitoreo Total", "💧 Balance Hídrico", "🌧️ Pluviómetro",
         "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora"],
        index=["📊 Monitoreo Total", "💧 Balance Hídrico", "🌧️ Pluviómetro",
               "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora"]
              .index(st.session_state.menu_principal),
        key="menu_principal"
    )

    # Botón de soporte
    numero_soporte = "5491154074144"
    texto_wa = "Hola! Necesito asistencia técnica con AgroGuardian."
    url_wa = f"https://wa.me/{numero_soporte}?text={texto_wa.replace(' ', '%20')}"
    st.markdown(f"""
        <a href="{url_wa}" target="_blank">
            <button style="background-color:black; color:#00ffc3; border:1px solid #30363d; width:100%; border-radius:5px;">🆘 SOPORTE TÉCNICO</button>
        </a>
    """, unsafe_allow_html=True)

    if st.button("🔄 RE-SCAN"):
        st.rerun()

# 5️⃣ LÓGICA DE PÁGINAS
if menu == "📊 Monitoreo Total":
    st.header("📊 MONITOREO TOTAL")
    # Aquí va tu código de métricas, mapas, etc.
    st.write("Contenido del monitoreo...")
elif menu == "💧 Balance Hídrico":
    st.header("💧 BALANCE HÍDRICO")
    st.write("Contenido del balance hídrico...")
elif menu == "🌧️ Pluviómetro":
    st.header("🌧️ PLUVIÓMETRO")
    st.write("Contenido del pluviómetro...")
elif menu == "⛈️ Radar Granizo":
    st.header("⛈️ RADAR GRANIZO")
    st.write("Contenido del radar de granizo...")
elif menu == "❄️ Análisis de Heladas":
    st.header("❄️ ANÁLISIS DE HELADAS")
    st.write("Contenido del análisis de heladas...")
elif menu == "📝 Bitácora":
    st.header("📝 BITÁCORA")
    st.write("Contenido de la bitácora...")
if menu == "📊 Monitoreo Total":
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("TEMPERATURA", f"{clima['temp']}°C")
    c2.metric("PTO. ROCÍO", f"{t_dp}°C")
    c3.metric("GDC (B10)", f"{gdc_hoy:.1f}")
    c4.metric("HUMEDAD", f"{clima['hum']}%")
    c5.metric("VIENTO", f"{clima['v_vel']} km/h", v_rumbo)
    st.divider()
    m = folium.Map(location=[LAT, LON], zoom_start=15)
    folium.TileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri').add_to(m)
    folium_static(m, width=700, height=400)

elif menu == "❄️ Análisis de Heladas":
    dif = 3.5 if clima['v_vel'] < 5 else 1.2
    st.metric("Temp. Suelo (Est.)", f"{round(clima['temp'] - dif, 1)}°C")
    if t_dp <= 0: st.error(f"HELADA NEGRA: {t_dp}°C")
    elif clima['temp'] < 3: st.warning("RIESGO DE HELADA BLANCA")
    else: st.success("Sin riesgo inmediato")

elif menu == "🌧️ Pluviómetro":
    st.title("🌧️ Registros de Lluvia")
    # ... (Acá pegá el resto de tu código del pluviómetro)

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

# CSS para botón negro de fondo, sin tocar el color del texto
st.markdown("""
    <style>
    div[data-baseweb="button"] > button {
        background-color: black !important;
    }

    div[data-baseweb="button"] > button:hover {
        background-color: #333333 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Botón de soporte
numero_soporte = "5491154074144"
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
