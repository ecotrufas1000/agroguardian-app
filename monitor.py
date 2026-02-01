import streamlit as st
import json
import os

st.set_page_config(page_title="AgroGuardian Monitor", page_icon="🌾")

st.title("🌾 Panel de Control AgroGuardian")

# --- SECCIÓN 1: UBICACIÓN (desde usuarios.json) ---
st.subheader("📍 Estado del Lote")
archivo_user = "usuarios.json"

if os.path.exists(archivo_user):
    with open(archivo_user, "r", encoding="utf-8") as f:
        try:
            usuarios = json.load(f)
            # Mostramos la ubicación del último usuario registrado
            if usuarios:
                ultimo_user = list(usuarios.values())[-1]
                lat = ultimo_user.get("lat")
                lon = ultimo_user.get("lon")
                st.success(f"Lote Sincronizado: Lat {lat}, Lon {lon}")
        except:
            st.error("Error al leer usuarios.json")
else:
    st.info("Esperando sincronización de GPS desde Telegram...")

# --- SECCIÓN 2: BITÁCORA (desde bitacora_campo.txt) ---
st.subheader("📝 Novedades del Campo")
archivo_txt = "bitacora_campo.txt"

if os.path.exists(archivo_txt):
    with open(archivo_txt, "r", encoding="utf-8") as f:
        lineas = f.readlines()
    
    if lineas:
        # Mostramos las líneas en orden inverso (la más nueva arriba)
        for linea in reversed(lineas):
            if linea.strip(): # Evita líneas vacías
                st.info(linea.strip())
    else:
        st.warning("La bitácora está vacía.")
else:
    st.error(f"No se encontró el archivo: {archivo_txt}")

# --- BOTÓN DE RECARGA ---
if st.button("🔄 Actualizar"):
    st.rerun()