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
# FUNCIONES DE CONVERSIÓN (DEBEN IR ARRIBA)
# ==========================================================
def grados_a_direccion(grados):
    try:
        val = int((grados / 22.5) + 0.5)
        direcciones = [
            "N", "NNE", "NE", "ENE", 
            "E", "ESE", "SE", "SSE", 
            "S", "SSO", "SO", "OSO", 
            "O", "ONO", "NO", "NNO"
        ]
        return direcciones[(val % 16)]
    except:
        return "N/A"
import urllib.parse
def generar_link_whatsapp(tarea, lote, temp, viento, nota):
    texto = f"📝 *Reporte AgroGuardian Pro*\n\n"
    texto += f"✅ *Tarea:* {tarea}\n"
    texto += f"📍 *Lote:* {lote}\n"
    texto += f"🌡️ *Condiciones:* {temp}°C | 💨 {viento} km/h\n"
    if nota:
        texto += f"📋 *Notas:* {nota}\n"
    
    # Codificar para URL
    msg_encoded = urllib.parse.quote(texto)
    return f"https://wa.me/?text={msg_encoded}"
# ==========================================================
# 1.5 CONEXIÓN A BASE DE DATOS
# ==========================================================

# Accedemos a las credenciales guardadas en Streamlit Cloud
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("🚨 Error: No se encontraron las credenciales 'SUPABASE_URL' y 'SUPABASE_KEY' en los Secrets de Streamlit.")
    st.stop() # Detiene la app si no hay conexión, para evitar errores en cadena

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

# --- INICIALIZACIÓN DE SUPABASE (Asegúrate de tener tus credenciales) ---
# url: str = st.secrets["SUPABASE_URL"]
# key: str = st.secrets["SUPABASE_KEY"]
# supabase = create_client(url, key)
# ==========================================================
# 1.5 CONEXIÓN A BASE DE DATOS (CRUCIAL PARA EL GPS)
# ==========================================================
# Reemplazá con tus datos de Supabase o usá st.secrets
#if 'supabase' not in locals():
#    try:
#        url = st.secrets["SUPABASE_URL"]
#        key = st.secrets["SUPABASE_KEY"]
#        supabase = create_client(url, key)
#    except Exception as e:
#        st.error("❌ Error de configuración: Faltan credenciales de Supabase en Secrets.")
# ==========================================================
# 2. MOTOR DE UBICACIÓN Y CLIMA CIENTÍFICO (AUTÓNOMO)
# ==========================================================
from streamlit_js_eval import get_geolocation

def obtener_clima_completo(lat, lon):
    if not lat or not lon: return None
    try:
        API_KEY = st.secrets["OPENWEATHER_API_KEY"]
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
        r = requests.get(url).json()
        
        if r.get("main"):
            t = r["main"]["temp"]
            h = r["main"]["humidity"]
            a, b = 17.27, 237.7
            alpha = ((a * t) / (b + t)) + math.log(h/100.0)
            punto_rocio = (b * alpha) / (a - alpha)
            
            return {
                "temp": t,
                "hum": h,
                "v_vel": round(r["wind"]["speed"] * 3.6, 1),
                "v_dir": r["wind"].get("deg", 0),
                "rocio": round(punto_rocio, 1),
                "presion": r["main"]["pressure"],
                "localidad": r.get("name", "Zona Rural")
            }
    except Exception as e:
        st.error(f"Error de conexión meteorológica: {e}")
    return None

if 'lat' not in st.session_state:
    try:
        res = supabase.table("configuracion").select("latitud", "longitud").order("created_at", desc=True).limit(1).execute()
        if res.data:
            st.session_state.lat = float(res.data[0]['latitud'])
            st.session_state.lon = float(res.data[0]['longitud'])
    except:
        st.session_state.lat = None

# --- SIDEBAR Y NAVEGACIÓN ---
with st.sidebar:
    st.markdown("### 🛰️ SENSORES DEL LOTE")
    gps_data = get_geolocation()
    
    if st.button("📍 VINCULAR GPS DEL MÓVIL"):
        if gps_data:
            lat_gps = gps_data['coords']['latitude']
            lon_gps = gps_data['coords']['longitude']
            supabase.table("configuracion").insert({"latitud": lat_gps, "longitud": lon_gps}).execute()
            st.session_state.lat = lat_gps
            st.session_state.lon = lon_gps
            st.success("✅ Ubicación actualizada")
            st.rerun()
        else:
            st.warning("⚠️ Activá el GPS y permití el acceso.")
# ==========================================================
# ==========================================================
# IDENTIDAD VISUAL EN SIDEBAR
# ==========================================================
st.sidebar.markdown("""
    <div style="
        background-color: #1e1e1e; 
        padding: 20px; 
        border-radius: 10px; 
        border: 1px solid #00ffc3; 
        text-align: center; 
        margin-bottom: 20px;
        box-shadow: 0px 4px 15px rgba(0, 255, 195, 0.2);
    ">
        <h1 style="color: #00ffc3; margin: 0; font-size: 22px; letter-spacing: 2px;">AGROGUARDIAN</h1>
        <p style="color: #ffffff; margin: 0; font-size: 12px; opacity: 0.8;">PRECISION LAB v2.6</p>
    </div>
""", unsafe_allow_html=True)

# AGREGAMOS .sidebar AQUÍ TAMBIÉN:
st.sidebar.divider()

menu = st.sidebar.radio(
    "MENÚ DE CONTROL", 
    ["📊 Monitoreo Total", "🌧️ Pluviómetro", "💧 Balance Hídrico", "⛈️ Radar Granizo", "❄️ Análisis de Heladas", "📝 Bitácora"]
)

# Esto sigue igual, fuera del sidebar para procesar la lógica
LAT = st.session_state.get('lat')
LON = st.session_state.get('lon')
clima = obtener_clima_completo(LAT, LON)

if clima:
    st.session_state.clima_data = clima

# ==========================================================
# 4. PÁGINAS (ESTRUCTURA INTEGRADA)
# ==========================================================

if menu == "📊 Monitoreo Total":
    st.header("📊 Tablero de Control Integral")
    
    if clima:
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Temperatura", f"{clima['temp']} °C")
        with col2: st.metric("Humedad Rel.", f"{clima['hum']} %")
        with col3: st.metric("Pto. de Rocío", f"{clima['rocio']} °C")
        with col4: st.metric("Viento", f"{clima['v_vel']} km/h")

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
            df['fecha'] = pd.to_datetime(df['fecha'])
            df['mm'] = pd.to_numeric(df['mm'], errors='coerce').fillna(0)
            hoy = datetime.datetime.now(datetime.timezone.utc)

            # --- MÉTRICAS RÁPIDAS ---
            df_mes = df[(df['fecha'].dt.month == hoy.month) & (df['fecha'].dt.year == hoy.year)].copy()
            df_año = df[df['fecha'].dt.year == hoy.year].copy()
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("💧 Este Mes", f"{df_mes['mm'].sum():.1f} mm")
            c2.metric("📆 Acum. Anual", f"{df_año['mm'].sum():.1f} mm")
            c3.metric("⚡ Máx. Día", f"{df_mes['mm'].max() if not df_mes.empty else 0:.1f} mm")
            c4.metric("📊 Registros", f"{len(df)} eventos")

            st.divider()
            
            # Estilo común para gráficos
            estilo_grafico = dict(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#00ffc3"),
                height=350,
                margin=dict(l=10, r=10, t=30, b=20)
            )

            # --- GRÁFICO 1: DIARIO (Ya lo tenías, lo mantenemos) ---
            st.subheader(f"📅 Detalle Diario — {hoy.strftime('%B %Y')}")
            df_mes['dia'] = df_mes['fecha'].dt.day
            df_dia = df_mes.groupby('dia')['mm'].sum().reindex(range(1, 32), fill_value=0).reset_index()
            fig1 = px.bar(df_dia, x='dia', y='mm', template="plotly_dark")
            fig1.update_traces(marker_color='#1f77b4')
            fig1.update_layout(**estilo_grafico)
            st.plotly_chart(fig1, use_container_width=True)

            # --- GRÁFICO 2: MENSUAL ACUMULADO (AÑADIDO) ---
            st.subheader(f"📊 Acumulado Mensual — Año {hoy.year}")
            meses_nombres = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            # Agrupar por mes (1-12)
            mensual = df_año.groupby(df_año['fecha'].dt.month)['mm'].sum().reindex(range(1, 13), fill_value=0)
            df_anual = pd.DataFrame({'Mes': meses_nombres, 'Prec_mm': mensual.values})

            fig2 = px.bar(df_anual, x='Mes', y='Prec_mm', template="plotly_dark", 
                          text_auto='.1f', title="Distribución de Lluvias por Mes")
            fig2.update_traces(marker_color='#00ffc3', textposition="outside")
            fig2.update_layout(**estilo_grafico)
            st.plotly_chart(fig2, use_container_width=True)

            

            st.divider()

            # --- BOTÓN PARA PLANILLA DE DATOS (AÑADIDO) ---
            st.subheader("📂 Base de Datos Histórica")
            with st.expander("VER PLANILLA DE REGISTROS COMPLETOS"):
                # Limpiamos el DataFrame para mostrarlo lindo
                df_display = df.copy()
                df_display['fecha'] = df_display['fecha'].dt.strftime('%d/%m/%Y %H:%M')
                df_display = df_display.sort_values('fecha', ascending=False)
                
                # Botón de descarga CSV
                csv = df_display.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar datos en Excel/CSV",
                    data=csv,
                    file_name=f'lluvias_agroguardian_{hoy.year}.csv',
                    mime='text/csv',
                )
                
                # Tabla interactiva
                st.dataframe(
                    df_display[['fecha', 'lote', 'mm']], 
                    use_container_width=True,
                    column_config={
                        "mm": st.column_config.NumberColumn("Milímetros", format="%.1f mm"),
                        "fecha": "Fecha de Registro",
                        "lote": "Identificación Lote"
                    }
                )

        else:
            st.info("🛰️ No hay registros de lluvia cargados todavía en Supabase.")

    except Exception as e:
        st.error(f"Error al procesar los datos de lluvia: {e}")
 elif menu == "💧 Balance Hídrico":
    import folium
    from streamlit_folium import folium_static
    st.markdown("### 💧 MONITOREO DE PRECISIÓN COPERNICUS (S2_SR)")
    try:
        lat = LAT if LAT else -38.29
        lon = LON if LON else -57.55
        temp_media = st.session_state.clima_data['temp'] if 'clima_data' in st.session_state else 25.0
        doy = datetime.datetime.now().timetuple().tm_yday
        delta = 0.409 * math.sin((2 * math.pi * doy / 365) - 1.39)
        ws = math.acos(max(-1, min(1, -math.tan(math.radians(lat)) * math.tan(delta))))
        eto_diaria = ((24/math.pi)*ws / 4380) * 100 * (0.46 * temp_media + 8)
        try:
            url_cop = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=soil_moisture_28_to_100cm&models=ecmwf_ifs&forecast_days=1"
            res_cop = requests.get(url_cop).json()
            hum_profunda = res_cop['hourly']['soil_moisture_28_to_100cm'][0]
        except:
            hum_profunda = 0.0
        kc = st.slider("Kc del Cultivo", 0.3, 1.2, 0.8)
        etc = eto_diaria * kc
        c1, c2, c3 = st.columns(3)
        c1.metric("ETo (Demanda)", f"{eto_diaria:.2f} mm")
        c2.metric("ETc (Consumo)", f"{etc:.2f} mm")
        c3.metric("Humedad Perfil", f"{hum_profunda:.3f} m³/m³")
        st.divider()
        st.markdown("### 🛰️ Anomalía de Humedad del Suelo (Copernicus)")
        lat_map = LAT if LAT else -38.29
        lon_map = LON if LON else -57.55
        zoom_level = 8 if LAT else 5
        opacidad = st.slider("Transparencia de capa", 0.1, 1.0, 0.7)
        m = folium.Map(
            location=[lat_map, lon_map],
            zoom_start=zoom_level,
            tiles="CartoDB dark_matter",
            control_scale=True
        )
        folium.WmsTileLayer(
            url="https://drought.emergency.copernicus.eu/api/wms",
            name="Soil Moisture Anomaly",
            layers="SMI_v4_0_anomaly",
            fmt="image/png",
            transparent=True,
            opacity=opacidad,
            attr="Copernicus Emergency Management Service",
            version="1.3.0",
            styles="",
        ).add_to(m)
        folium.CircleMarker(
            location=[lat_map, lon_map],
            radius=6,
            color="#00ffc3",
            fill=True,
            fill_opacity=1
        ).add_to(m)
        folium.LayerControl().add_to(m)
        folium_static(m, width=1000, height=600)
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
    if clima:
        st.metric("Riesgo Térmico", f"{clima['temp']}°C")
        if clima['temp'] < 3: st.warning("ALERTA DE HELADA")
        else: st.success("Sin riesgo")

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

    st.divider()    # 2. VISUALIZACIÓN DE REGISTROS
    st.subheader("📋 Historial de Actividades")
    try:
        res = supabase.table("bitacora").select("*").order("fecha", desc=True).execute()
        if res.data:
            df_bit = pd.DataFrame(res.data)
            df_bit['fecha'] = pd.to_datetime(df_bit['fecha']).dt.strftime('%d/%m/%Y %H:%M')
            
            # Formateamos la tabla para que sea legible
            st.dataframe(
                df_bit[['fecha', 'tarea', 'lote', 'clima_temp', 'clima_viento', 'nota']],
                use_container_width=True,
                column_config={
                    "clima_temp": st.column_config.NumberColumn("Temp (°C)", format="%.1f"),
                    "clima_viento": st.column_config.NumberColumn("Viento (km/h)", format="%.1f"),
                    "nota": "Observaciones"
                }
            )
        else:
            st.info("No hay registros en la bitácora todavía.")
    except:
        st.error("No se pudo conectar con la tabla de bitácora.")
