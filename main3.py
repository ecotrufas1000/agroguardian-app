import telebot
import requests
import json

import datetime
import math
from telebot import types
from dotenv import load_dotenv
import os
# BORRÁ cualquier línea que diga "from google import genai"
# USÁ esta forma que es la más estable para bots:
import google.generativeai as genai


# 2. Configuración con la variable de entorno que pusiste en Render
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# 3. Definición del modelo
model = genai.GenerativeModel('gemini-1.5-flash')
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

load_dotenv()
# Configurá la API así:
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
from flask import Flask
from threading import Thread

# --- TRUCO PARA RENDER ---
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot vivo", 200

def run():
    # Render usa el puerto 10000 por defecto
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

Thread(target=run).start()
# -------------------------

# ======================================================
# CONFIGURACIÓN
# ======================================================
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# Definila así para que no importe cómo la llamaste en Render
OPENWEATHER_KEY = os.environ.get("OPENWEATHER_KEY") or os.environ.get("WEATHER_KEY") or os.environ.get("OPENWEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imllb2R6eWdhdWdsdmRrZW5kdm1qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDY4MTYxMywiZXhwIjoyMDg2MjU3NjEzfQ._UyIH2L5u89t8O-HQkzdJ_BNTIR61okZxA-mLpJnsLE"
SUPABASE_URL = "https://ieodzygauglvdkendvmj.supabase.co"


bot = telebot.TeleBot(TELEGRAM_TOKEN)
# Así es como debe quedar para que funcione:
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# Luego, cuando quieras usarlo en tus funciones, usás:
# response = model.generate_content("Tu pregunta aquí")
# Nombres de modelos actualizados
MODEL_TEXT = "gemini-2.0-flash"
MODEL_VISION = "gemini-2.0-flash"

BITACORA_JSON = "bitacora_campo.json"
MEMORIA_PATH = "memoria_lotes.json"

TABLA_KC = {
    "🌽 Maíz": {"Inicial": 0.3, "Medio": 1.2, "Final": 0.5},
    "🌱 Soja": {"Inicial": 0.4, "Medio": 1.15, "Final": 0.5},
    "🌾 Trigo": {"Inicial": 0.3, "Medio": 1.15, "Final": 0.25},
    "🥔 Papa": {"Inicial": 0.5, "Medio": 1.15, "Final": 0.75},
}

# ======================================================
# FUNCIONES DE MEMORIA
# ======================================================
def cargar_memoria():
    if os.path.exists(MEMORIA_PATH):
        with open(MEMORIA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def guardar_memoria(memoria):
    with open(MEMORIA_PATH, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=4, ensure_ascii=False)

def actualizar_memoria(chat_id, clave, valor):
    memoria = cargar_memoria()
    memoria.setdefault(str(chat_id), {})
    memoria[str(chat_id)][clave] = valor
    memoria[str(chat_id)]["ultima_actualizacion"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    guardar_memoria(memoria)

def leer_memoria(chat_id):
    return cargar_memoria().get(str(chat_id), {})

# ======================================================
# FUNCIONES AUXILIARES
# ======================================================
def guardar_bitacora_json(chat_id, lote, cultivo, tipo, detalle):
    data = {}
    if os.path.exists(BITACORA_JSON):
        with open(BITACORA_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
    uid = str(chat_id)
    data.setdefault(uid, [])
    data[uid].append({
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "lote": lote,
        "cultivo": cultivo,
        "tipo": tipo,
        "detalle": detalle
    })
    with open(BITACORA_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def grados_a_direccion(grados):
    val = int((grados / 22.5) + 0.5)
    direcciones = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                   "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
    return direcciones[val % 16]

def escapar_markdown_v2(texto: str) -> str:
    caracteres = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in caracteres else c for c in texto)

def enviar_mensaje_largo(chat_id, texto):
    MAX = 4000
    for i in range(0, len(texto), MAX):
        bot.send_message(chat_id, texto[i:i+MAX], parse_mode="Markdown")

# ======================================================
# MENÚ PRINCIPAL
# ======================================================
def menu_principal_profesional(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🌡 CLIMA", callback_data="clima"),
        types.InlineKeyboardButton("📅 PRONÓSTICO", callback_data="pronostico"),
        types.InlineKeyboardButton("📍 VINCULAR GPS", callback_data="pedir_gps"),
        types.InlineKeyboardButton("🌧️ ANOTAR LLUVIA", callback_data="anotar_lluvia"), # <--- AGREGÁ ESTA LÍNEA
        types.InlineKeyboardButton("💧 BALANCE", callback_data="balance"),
        types.InlineKeyboardButton("📷 FOTO AI", callback_data="foto_ai"),
        types.InlineKeyboardButton("✏️ ANOTAR", callback_data="anotar"),
        types.InlineKeyboardButton("📖 BITÁCORA", callback_data="bitacora"),
        types.InlineKeyboardButton("📂 CONFIG LOTE", callback_data="config_lote"),
        types.InlineKeyboardButton("🌱 CONFIG CULTIVO", callback_data="config_cultivo"),
        types.InlineKeyboardButton("🌐 PANEL", url="https://agroguardian-app-eowdpzrknk8ybcuyf78gmq.streamlit.app")
    )
    # ... resto de la función
    
    bot.send_message(chat_id,
        "🚜 *AGROGUARDIAN LAB v2.6*\nSeleccioná una operación:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ======================================================
# CALLBACKS
# ======================================================
@bot.callback_query_handler(func=lambda call: True)
def callback_menu(call):
    chat_id = call.message.chat.id

    if call.data == "clima": mostrar_clima(call.message)
    elif call.data == "pronostico": mostrar_pronostico(call.message)
    elif call.data == "pedir_gps": 
        bot.send_message(chat_id, "📍 *INSTRUCCIÓN:* Presioná el icono del clip (📎) y enviá tu 'Ubicación' para sincronizar este lote.")
    elif call.data == "anotar_lluvia": pedir_lluvia(call)
    elif call.data == "balance": iniciar_balance_hidrico(call.message)
    elif call.data == "foto_ai": pedir_foto(call.message)
    elif call.data == "anotar": anotar_novedad(call.message)
    elif call.data == "bitacora": ver_bitacora(call.message)
    elif call.data == "config_lote":
        msg = bot.send_message(chat_id, "📂 Escribí el nombre del lote:")
        bot.register_next_step_handler(msg, guardar_lote)
    elif call.data == "config_cultivo":
        msg = bot.send_message(chat_id, "🌱 Escribí el cultivo de este lote:")
        bot.register_next_step_handler(msg, guardar_cultivo)
    elif call.data.startswith("balance_"): seleccionar_cultivo_balance(call)
    elif call.data.startswith("etapa_"): calcular_balance(call)

# ======================================================
# ======================================================
# RECEPCIÓN GPS (HANDLER DE UBICACIÓN) - CORREGIDO
# ======================================================
@bot.message_handler(content_types=['location'])
#bot.send_message(chat_id, f"🚀 ESTA ES LA VERSION NUEVA: {lat}, {lon}")
def recibir_ubicacion_gps(message):
    chat_id = message.chat.id
    
    # EXTRAEMOS LAS COORDENADAS REALES DEL MENSAJE DE TELEGRAM
    lat_real = message.location.latitude
    lon_real = message.location.longitude
    
    # 1. Guardamos en la memoria local del bot
    actualizar_memoria(chat_id, "lat", lat_real)
    actualizar_memoria(chat_id, "lon", lon_real)
    
    memoria = leer_memoria(chat_id)
    lote = memoria.get("lote_activo", "General")
    
    # 2. Intentamos mandar a la nube (Supabase)
    try:
        registro_gps = {
            "chat_id": str(chat_id),
            "lote": f"GPS: {lote}",
            "mm": 0,
            "lat": lat_real,  # <--- USAMOS LA VARIABLE REAL
            "lon": lon_real,  # <--- USAMOS LA VARIABLE REAL
            "fecha": datetime.datetime.now().isoformat()
        }
        supabase.table("registros_lluvia").insert(registro_gps).execute()
        sync_status = "🌐 *Sincronizado con Panel Web*"
    except Exception as e:
        print(f"Error Supabase: {e}")
        sync_status = "⚠️ *Error de sincronización nube*"

    # 3. Respuesta al usuario con las coordenadas REALES
    # USAMOS lat_real y lon_real para que el mensaje no mienta
    bot.send_message(
        chat_id, 
        f"✅ *GPS VINCULADO*\n"
        f"Lote: `{lote}`\n"
        f"📍 Lat: `{lat_real}`\n"
        f"📍 Lon: `{lon_real}`\n"
        f"{sync_status}", 
        parse_mode="Markdown"
    )
    menu_principal_profesional(chat_id)
def recibir_ubicacion_gps(message):
    chat_id = message.chat.id
    
    # EXTRAEMOS LAS COORDENADAS REALES DEL MENSAJE DE TELEGRAM
    lat_real = message.location.latitude
    lon_real = message.location.longitude
    
    # 1. Guardamos en la memoria local del bot
    actualizar_memoria(chat_id, "lat", lat_real)
    actualizar_memoria(chat_id, "lon", lon_real)
    
    memoria = leer_memoria(chat_id)
    lote = memoria.get("lote_activo", "General")
    
    # 2. Intentamos mandar a la nube (Supabase)
    try:
        registro_gps = {
            "chat_id": str(chat_id),
            "lote": f"GPS: {lote}",
            "mm": 0,
            "lat": lat_real,  # <--- USAMOS LA VARIABLE REAL
            "lon": lon_real,  # <--- USAMOS LA VARIABLE REAL
            "fecha": datetime.datetime.now().isoformat()
        }
        supabase.table("registros_lluvia").insert(registro_gps).execute()
        sync_status = "🌐 *Sincronizado con Panel Web*"
    except Exception as e:
        print(f"Error Supabase: {e}")
        sync_status = "⚠️ *Error de sincronización nube*"

    # 3. Respuesta al usuario con las coordenadas REALES
    # USAMOS lat_real y lon_real para que el mensaje no mienta
    bot.send_message(
        chat_id, 
        f"✅ *GPS VINCULADO*\n"
        f"Lote: `{lote}`\n"
        f"📍 Lat: `{lat_real}`\n"
        f"📍 Lon: `{lon_real}`\n"
        f"{sync_status}", 
        parse_mode="Markdown"
    )
    menu_principal_profesional(chat_id)    # 3. Respuesta al usuario
    bot.send_message(
        chat_id, 
        f"✅ *GPS VINCULADO*\nLote: `{lote}`\nPosición: `{lat}, {lon}`{confirmacion_nube}", 
        parse_mode="Markdown"
    )
    menu_principal_profesional(chat_id)

# ======================================================
# LÓGICA DE CLIMA Y CÁLCULOS
# ======================================================
    def mostrar_clima(message):
    memoria = leer_memoria(message.chat.id)
    lat, lon = memoria.get("lat"), memoria.get("lon")
    
    if not lat or not lon:
        bot.send_message(message.chat.id, "📍 *Error:* Primero vinculá tu GPS.")
        return
    
    try:
        # IMPORTANTE: Asegurate que OPENWEATHER_KEY esté bien definida arriba
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_KEY}&units=metric&lang=es"
        response = requests.get(url)
        r = response.json()
        
        # SI LA API RESPONDE ERROR (Aquí es donde fallaba antes)
        if response.status_code != 200:
            mensaje_error = r.get('message', 'Error desconocido')
            bot.send_message(message.chat.id, f"❌ *Error de Clima:* {mensaje_error.capitalize()}")
            return

        # SI LA API RESPONDE BIEN, RECIÉN AHÍ LEEMOS LOS DATOS
        temp = r['main']['temp']
        hum = r['main']['humidity']
        v_vel = round(r['wind']['speed'] * 3.6, 1)
        
        # Punto de rocío
        a, b = 17.27, 237.7
        alpha = ((a * temp) / (b + temp)) + math.log(hum/100.0)
        t_dp = round((b * alpha) / (a - alpha), 1)
        
        texto = (
            f"📊 *DATOS ATMOSFÉRICOS*\n"
            f"🌡️ Temp: `{temp}°C` | HR: `{hum}%` \n"
            f"❄️ Dew Point: `{t_dp}°C` \n"
            f"🌬️ Viento: `{v_vel} km/h` \n"
            f"🛰️ Estado: `{r['weather'][0]['description'].upper()}`"
        )
        bot.send_message(message.chat.id, texto, parse_mode="Markdown")
        menu_principal_profesional(message.chat.id)

    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error técnico: {str(e)}")

# ======================================================
# CONFIGURACIÓN LOTE / CULTIVO
# ======================================================
def guardar_lote(message):
    actualizar_memoria(message.chat.id, "lote_activo", message.text)
    bot.send_message(message.chat.id, f"✅ Lote '{message.text}' activado.")
    menu_principal_profesional(message.chat.id)

def guardar_cultivo(message):
    chat_id = message.chat.id
    memoria = leer_memoria(chat_id)
    lote = memoria.get("lote_activo")
    if not lote:
        bot.send_message(chat_id, "⚠️ Configurá un lote primero.")
        return
    lotes = memoria.get("lotes", {})
    lotes.setdefault(lote, {})
    lotes[lote]["cultivo"] = message.text
    actualizar_memoria(chat_id, "lotes", lotes)
    bot.send_message(chat_id, f"✅ Cultivo '{message.text}' asignado a '{lote}'.")
    menu_principal_profesional(chat_id)

# ======================================================
# FOTO IA (VISIÓN)
# ======================================================
def pedir_foto(message):
    msg = bot.send_message(message.chat.id, "📸 Enviá la foto del cultivo:")
    bot.register_next_step_handler(msg, analizar_foto)

def analizar_foto(message):
    if not message.photo:
        bot.send_message(message.chat.id, "❌ No se recibió imagen.")
        return
    
    bot.send_message(message.chat.id, "🧠 *LABORATORIO IA:* Analizando muestra...")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded = bot.download_file(file_info.file_path)

    try:
        response = client.models.generate_content(
            model=MODEL_VISION,
            contents=[
                "Actúa como un ingeniero agrónomo. Analiza plagas, enfermedades o deficiencias. Sé breve.",
                genai_types.Part.from_bytes(downloaded, mime_type="image/jpeg")
            ]
        )
        bot.send_message(message.chat.id, f"🔬 *REPORTE IA:*\n{response.text}", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Error en motor IA.")
    
    menu_principal_profesional(message.chat.id)

# ---------------- ANOTAR Y BITÁCORA ----------------
def anotar_novedad(message):
    msg = bot.send_message(message.chat.id, "✍️ Describí la novedad:")
    bot.register_next_step_handler(msg, guardar_novedad_paso)

def guardar_novedad_paso(message):
    memoria = leer_memoria(message.chat.id)
    lote = memoria.get("lote_activo", "Gral")
    cultivo = memoria.get("lotes", {}).get(lote, {}).get("cultivo", "N/D")
    guardar_bitacora_json(message.chat.id, lote, cultivo, "Novedad", message.text)
    bot.send_message(message.chat.id, "✅ Registrado en bitácora.")
    menu_principal_profesional(message.chat.id)

def ver_bitacora(message):
    if not os.path.exists(BITACORA_JSON):
        bot.send_message(message.chat.id, "ℹ️ Log vacío.")
        return
    with open(BITACORA_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    eventos = data.get(str(message.chat.id), [])
    if not eventos:
        bot.send_message(message.chat.id, "❌ Sin eventos.")
    else:
        texto = "📑 *ÚLTIMOS REGISTROS*\n"
        for e in eventos[-5:]:
            texto += f"📅 `{e['fecha']}` | *{e['lote']}*: {e['detalle']}\n"
        bot.send_message(message.chat.id, texto, parse_mode="Markdown")
    menu_principal_profesional(message.chat.id)

# ======================================================
# OTROS (PRONOSTICO Y BALANCE)
# ======================================================
def mostrar_pronostico(message):
    memoria = leer_memoria(message.chat.id)
    lat, lon = memoria.get("lat"), memoria.get("lon")
    if not lat: return bot.send_message(message.chat.id, "📍 Vincular GPS primero.")
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric&lang=es"
    data = requests.get(url).json()
    res = "📅 *PRONÓSTICO 3 DÍAS*\n"
    for b in data["list"][::8][:3]:
        res += f"• {b['dt_txt'][:10]}: `{b['main']['temp']}°C` | {b['weather'][0]['description']}\n"
    bot.send_message(message.chat.id, res, parse_mode="Markdown")
    menu_principal_profesional(message.chat.id)

def iniciar_balance_hidrico(message):
    markup = types.InlineKeyboardMarkup()
    for c in TABLA_KC: markup.add(types.InlineKeyboardButton(c, callback_data=f"balance_{c}"))
    bot.send_message(message.chat.id, "🌱 Seleccioná cultivo:", reply_markup=markup)

def seleccionar_cultivo_balance(call):
    cultivo = call.data.replace("balance_", "")
    markup = types.InlineKeyboardMarkup()
    for e in ["Inicial", "Medio", "Final"]: markup.add(types.InlineKeyboardButton(e, callback_data=f"etapa_{cultivo}_{e}"))
    bot.send_message(call.message.chat.id, f"📊 Etapa para {cultivo}:", reply_markup=markup)

def calcular_balance(call):
    _, cult, etap = call.data.split("_")
    kc = TABLA_KC[cult][etap]
    bal = 0.0 - (kc * 5.0) # Simplificado
    bot.send_message(call.message.chat.id, f"💧 *BALANCE:* {bal:.2f} mm/día\nCultivo: {cult}\nEtapa: {etap}")
    menu_principal_profesional(call.message.chat.id)
# ======================================================
# LÓGICA DE PLUVIÓMETRO
# ======================================================
def pedir_lluvia(call):
    # Usamos call.message.chat.id porque viene de un botón
    msg = bot.send_message(call.message.chat.id, "🌧️ *REGISTRO DE LLUVIAS*\n¿Cuántos mm marcó el pluviómetro?", parse_mode="Markdown")
    bot.register_next_step_handler(msg, guardar_lluvia)

from supabase import create_client

# Configura tus llaves (sacalas de Settings -> API en Supabase)
SUPABASE_URL = "https://ieodzygauglvdkendvmj.supabase.co"
SUPABASE_KEY = "sb_secret_SyWyA13u80LI9nz-if5iIw_bUqo0AZB" # <--- Usá la 'service_role' para tener permiso de escritura
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def guardar_lluvia(message):
    chat_id = str(message.chat.id)
    try:
        # 1. Procesar número
        val = message.text.replace(',', '.')
        mm = float(val)
        
        memoria = leer_memoria(chat_id)
        lote = memoria.get("lote_activo", "General")
        
        # 2. Preparar datos (sin tildes en las claves)
        registro_nube = {
            "chat_id": chat_id,
            "lote": str(lote),
            "mm": mm,
            "fecha": datetime.datetime.now().isoformat()
        }

        print(">>> Intentando subir dato...")

        # 3. Insertar con manejo de error robusto
        try:
            supabase.table("registros_lluvia").insert(registro_nube).execute()
            print(">>> EXITO: Dato en la nube.")
            
            bot.send_message(chat_id, f"✅ ¡Registrado! {mm} mm en {lote}")
            menu_principal_profesional(chat_id)
            
        except Exception as e_db:
            # Esto evita el error de ASCII en Windows
            error_msg = str(e_db).encode('utf-8', 'ignore').decode('ascii', 'ignore')
            print(f">>> ERROR SUPABASE: {error_msg}")
            bot.send_message(chat_id, "⚠️ Error de conexión con la base de datos.")

    except ValueError:
        bot.send_message(chat_id, "❌ Error: Envía solo el número.")
    except Exception as e_gen:
        print(f">>> ERROR GENERAL: {e_gen}")# ======================================================
@bot.message_handler(commands=["start"])
def start(message):
    menu_principal_profesional(message.chat.id)

# ... (aquí van tus funciones de clima, ubicación, etc.) ...


if __name__ == "__main__":
    # 1. Iniciar el servidor web para Render en segundo plano
    Thread(target=run).start() 
    
    # 2. Iniciar el Bot
    print("🤖 AgroGuardian Lab Iniciado")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)













