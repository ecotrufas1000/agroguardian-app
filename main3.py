import telebot
import requests
import json
import datetime
import math
from telebot import types
from dotenv import load_dotenv
import os
import google.generativeai as genai
from flask import Flask
from threading import Thread
from supabase import create_client

# ======================================================
# CONFIGURACIÓN INICIAL
# ======================================================
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = "https://ieodzygauglvdkendvmj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imllb2R6eWdhdWdsdmRrZW5kdm1qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MDY4MTYxMywiZXhwIjoyMDg2MjU3NjEzfQ._UyIH2L5u89t8O-HQkzdJ_BNTIR61okZxA-mLpJnsLE"

# Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Telegram Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

BITACORA_JSON = "bitacora_campo.json"
MEMORIA_PATH = "memoria_lotes.json"

TABLA_KC = {
    "🌽 Maíz":  {"Inicial": 0.3,  "Medio": 1.2,  "Final": 0.5},
    "🌱 Soja":  {"Inicial": 0.4,  "Medio": 1.15, "Final": 0.5},
    "🌾 Trigo": {"Inicial": 0.3,  "Medio": 1.15, "Final": 0.25},
    "🥔 Papa":  {"Inicial": 0.5,  "Medio": 1.15, "Final": 0.75},
}

# ======================================================
# TRUCO PARA RENDER (servidor web keep-alive)
# ======================================================
app = Flask(__name__)

@app.route('/')
def health():
    return "Bot vivo", 200

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

Thread(target=run).start()

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
        types.InlineKeyboardButton("🌡 CLIMA",          callback_data="clima"),
        types.InlineKeyboardButton("📅 PRONÓSTICO",     callback_data="pronostico"),
        types.InlineKeyboardButton("📍 VINCULAR GPS",   callback_data="pedir_gps"),
        types.InlineKeyboardButton("🌧️ ANOTAR LLUVIA",  callback_data="anotar_lluvia"),
        types.InlineKeyboardButton("💧 BALANCE",        callback_data="balance"),
        types.InlineKeyboardButton("📷 FOTO AI",        callback_data="foto_ai"),
        types.InlineKeyboardButton("✏️ ANOTAR",         callback_data="anotar"),
        types.InlineKeyboardButton("📖 BITÁCORA",       callback_data="bitacora"),
        types.InlineKeyboardButton("📂 CONFIG LOTE",    callback_data="config_lote"),
        types.InlineKeyboardButton("🌱 CONFIG CULTIVO", callback_data="config_cultivo"),
        types.InlineKeyboardButton("🌐 PANEL", url="https://agroguardian-app-eowdpzrknk8ybcuyf78gmq.streamlit.app")
    )
    bot.send_message(
        chat_id,
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

    if call.data == "clima":
        mostrar_clima(call.message)
    elif call.data == "pronostico":
        mostrar_pronostico(call.message)
    elif call.data == "pedir_gps":
        bot.send_message(chat_id, "📍 *INSTRUCCIÓN:* Presioná el icono del clip (📎) y enviá tu 'Ubicación' para sincronizar este lote.", parse_mode="Markdown")
    elif call.data == "anotar_lluvia":
        pedir_lluvia(call)
    elif call.data == "balance":
        iniciar_balance_hidrico(call.message)
    elif call.data == "foto_ai":
        pedir_foto(call.message)
    elif call.data == "anotar":
        anotar_novedad(call.message)
    elif call.data == "bitacora":
        ver_bitacora(call.message)
    elif call.data == "config_lote":
        msg = bot.send_message(chat_id, "📂 Escribí el nombre del lote:")
        bot.register_next_step_handler(msg, guardar_lote)
    elif call.data == "config_cultivo":
        msg = bot.send_message(chat_id, "🌱 Escribí el cultivo de este lote:")
        bot.register_next_step_handler(msg, guardar_cultivo)
    elif call.data.startswith("balance_"):
        seleccionar_cultivo_balance(call)
    elif call.data.startswith("etapa_"):
        calcular_balance(call)

# ======================================================
# RECEPCIÓN GPS — CORREGIDO (una sola definición)
# ======================================================
@bot.message_handler(content_types=['location'])
def recibir_ubicacion_gps(message):
    chat_id = message.chat.id

    lat_real = message.location.latitude
    lon_real = message.location.longitude

    # Guardar en memoria local
    actualizar_memoria(chat_id, "lat", lat_real)
    actualizar_memoria(chat_id, "lon", lon_real)

    memoria = leer_memoria(chat_id)
    lote = memoria.get("lote_activo", "General")

    # Intentar sincronizar con Supabase
    try:
        registro_gps = {
            "chat_id": str(chat_id),
            "lote": f"GPS: {lote}",
            "mm": 0,
            "lat": lat_real,
            "lon": lon_real,
            "fecha": datetime.datetime.now().isoformat()
        }
        supabase.table("registros_lluvia").insert(registro_gps).execute()
        sync_status = "🌐 *Sincronizado con Panel Web*"
    except Exception as e:
        print(f"Error Supabase GPS: {e}")
        sync_status = "⚠️ *Error de sincronización nube*"

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

# ======================================================
# CLIMA ACTUAL — Open-Meteo (sin API key, 100% gratis)
# ======================================================

# Códigos WMO de clima → descripción en español
def descripcion_wmo(code):
    tabla = {
        0: "☀️ Despejado", 1: "🌤 Mayormente despejado", 2: "⛅ Parcialmente nublado",
        3: "☁️ Nublado", 45: "🌫 Niebla", 48: "🌫 Niebla con escarcha",
        51: "🌦 Llovizna leve", 53: "🌦 Llovizna moderada", 55: "🌧 Llovizna intensa",
        61: "🌧 Lluvia leve", 63: "🌧 Lluvia moderada", 65: "🌧 Lluvia intensa",
        71: "🌨 Nieve leve", 73: "🌨 Nieve moderada", 75: "❄️ Nieve intensa",
        80: "🌦 Chaparrones leves", 81: "🌧 Chaparrones moderados", 82: "⛈ Chaparrones intensos",
        95: "⛈ Tormenta", 96: "⛈ Tormenta con granizo", 99: "⛈ Tormenta con granizo intenso"
    }
    return tabla.get(code, f"Código {code}")

def mostrar_clima(message):
    memoria = leer_memoria(message.chat.id)
    lat, lon = memoria.get("lat"), memoria.get("lon")

    if not lat:
        return bot.send_message(message.chat.id, "📍 Vinculá tu GPS primero.")

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
            f"&wind_speed_unit=kmh"
        )
        r = requests.get(url).json()
        c = r["current"]

        temp  = c["temperature_2m"]
        hum   = c["relative_humidity_2m"]
        viento = c["wind_speed_10m"]
        desc  = descripcion_wmo(c["weather_code"])

        texto = (
            f"🌡️ *Temp:* `{temp}°C` | *HR:* `{hum}%`\n"
            f"🌬️ *Viento:* `{viento} km/h`\n"
            f"☁️ {desc}"
        )
        bot.send_message(message.chat.id, texto, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Error clima: {e}")

    menu_principal_profesional(message.chat.id)

# ======================================================
# PRONÓSTICO 3 DÍAS — Open-Meteo (sin API key, 100% gratis)
# ======================================================
def mostrar_pronostico(message):
    memoria = leer_memoria(message.chat.id)
    lat, lon = memoria.get("lat"), memoria.get("lon")

    if not lat:
        return bot.send_message(message.chat.id, "📍 Vinculá tu GPS primero.")

    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code"
            f"&forecast_days=3&timezone=auto"
        )
        data = requests.get(url).json()
        d = data["daily"]

        res = "📅 *PRONÓSTICO 3 DÍAS*\n"
        for i in range(3):
            fecha  = d["time"][i]
            tmax   = d["temperature_2m_max"][i]
            tmin   = d["temperature_2m_min"][i]
            lluvia = d["precipitation_sum"][i]
            desc   = descripcion_wmo(d["weather_code"][i])
            res += (
                f"\n📆 *{fecha}*\n"
                f"   🌡 `{tmin}°C → {tmax}°C` | 🌧 `{lluvia} mm`\n"
                f"   {desc}\n"
            )

        bot.send_message(message.chat.id, res, parse_mode="Markdown")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error pronóstico: {e}")

    menu_principal_profesional(message.chat.id)

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

    bot.send_message(message.chat.id, "🧠 *LABORATORIO IA:* Analizando muestra...", parse_mode="Markdown")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded = bot.download_file(file_info.file_path)

    try:
        img_data = {'mime_type': 'image/jpeg', 'data': downloaded}
        prompt = (
            "Actúa como un ingeniero agrónomo. "
            "Analiza plagas, enfermedades o deficiencias en esta foto de cultivo. "
            "Sé breve y profesional."
        )
        response = model.generate_content([prompt, img_data])
        bot.send_message(message.chat.id, f"🔬 *REPORTE IA:*\n{response.text}", parse_mode="Markdown")
    except Exception as e:
        print(f"Error Gemini: {e}")
        bot.send_message(message.chat.id, "⚠️ Error en motor IA (Gemini). Revisá tu API Key.")

    menu_principal_profesional(message.chat.id)

# ======================================================
# ANOTAR Y BITÁCORA
# ======================================================
def anotar_novedad(message):
    msg = bot.send_message(message.chat.id, "✍️ Describí la novedad:")
    bot.register_next_step_handler(msg, guardar_novedad_paso)

def guardar_novedad_paso(message):
    memoria = leer_memoria(message.chat.id)
    lote    = memoria.get("lote_activo", "Gral")
    cultivo = memoria.get("lotes", {}).get(lote, {}).get("cultivo", "N/D")
    guardar_bitacora_json(message.chat.id, lote, cultivo, "Novedad", message.text)
    bot.send_message(message.chat.id, "✅ Registrado en bitácora.")
    menu_principal_profesional(message.chat.id)

def ver_bitacora(message):
    if not os.path.exists(BITACORA_JSON):
        bot.send_message(message.chat.id, "ℹ️ Log vacío.")
        menu_principal_profesional(message.chat.id)
        return

    with open(BITACORA_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    eventos = data.get(str(message.chat.id), [])
    if not eventos:
        bot.send_message(message.chat.id, "❌ Sin eventos registrados.")
    else:
        texto = "📑 *ÚLTIMOS REGISTROS*\n"
        for e in eventos[-5:]:
            texto += f"📅 `{e['fecha']}` | *{e['lote']}*: {e['detalle']}\n"
        bot.send_message(message.chat.id, texto, parse_mode="Markdown")

    menu_principal_profesional(message.chat.id)

# ======================================================
# BALANCE HÍDRICO — CORREGIDO (split seguro)
# ======================================================
def iniciar_balance_hidrico(message):
    markup = types.InlineKeyboardMarkup()
    for c in TABLA_KC:
        markup.add(types.InlineKeyboardButton(c, callback_data=f"balance_{c}"))
    bot.send_message(message.chat.id, "🌱 Seleccioná cultivo:", reply_markup=markup)

def seleccionar_cultivo_balance(call):
    # callback_data: "balance_🌽 Maíz"
    cultivo = call.data[len("balance_"):]   # Evita problemas con emojis en split
    markup = types.InlineKeyboardMarkup()
    for e in ["Inicial", "Medio", "Final"]:
        markup.add(types.InlineKeyboardButton(e, callback_data=f"etapa_{cultivo}_{e}"))
    bot.send_message(call.message.chat.id, f"📊 Etapa para {cultivo}:", reply_markup=markup)

def calcular_balance(call):
    # callback_data: "etapa_🌽 Maíz_Inicial"
    # Usamos maxsplit=2 para no romper con emojis ni espacios en el nombre del cultivo
    partes = call.data.split("_", 2)
    cult = partes[1]
    etap = partes[2]

    kc  = TABLA_KC.get(cult, {}).get(etap, 1.0)
    bal = 0.0 - (kc * 5.0)

    bot.send_message(
        call.message.chat.id,
        f"💧 *BALANCE:* `{bal:.2f}` mm/día\nCultivo: {cult}\nEtapa: {etap}",
        parse_mode="Markdown"
    )
    menu_principal_profesional(call.message.chat.id)

# ======================================================
# PLUVIÓMETRO
# ======================================================
def pedir_lluvia(call):
    msg = bot.send_message(
        call.message.chat.id,
        "🌧️ *REGISTRO DE LLUVIAS*\n¿Cuántos mm marcó el pluviómetro?",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, guardar_lluvia)

def guardar_lluvia(message):
    chat_id = str(message.chat.id)
    try:
        mm = float(message.text.replace(',', '.'))

        memoria = leer_memoria(chat_id)
        lote    = memoria.get("lote_activo", "General")

        registro_nube = {
            "chat_id": chat_id,
            "lote":    str(lote),
            "mm":      mm,
            "fecha":   datetime.datetime.now().isoformat()
        }

        try:
            supabase.table("registros_lluvia").insert(registro_nube).execute()
            bot.send_message(chat_id, f"✅ ¡Registrado! `{mm}` mm en *{lote}*", parse_mode="Markdown")
        except Exception as e_db:
            error_msg = str(e_db).encode('utf-8', 'ignore').decode('ascii', 'ignore')
            print(f">>> ERROR SUPABASE: {error_msg}")
            bot.send_message(chat_id, "⚠️ Error de conexión con la base de datos.")

    except ValueError:
        bot.send_message(chat_id, "❌ Error: Enviá solo el número (ej: 12.5)")
    except Exception as e_gen:
        print(f">>> ERROR GENERAL lluvia: {e_gen}")
        bot.send_message(chat_id, "⚠️ Error inesperado al guardar la lluvia.")

    menu_principal_profesional(chat_id)

# ======================================================
# COMANDO START
# ======================================================
@bot.message_handler(commands=["start"])
def start(message):
    menu_principal_profesional(message.chat.id)

# ======================================================
# ARRANQUE
# ======================================================
if __name__ == "__main__":
    print("🤖 AgroGuardian Lab Iniciado")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)








