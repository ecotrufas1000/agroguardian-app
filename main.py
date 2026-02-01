import telebot
import requests
import google.generativeai as genai
import json
import os
from telebot import types

# === 1. CONFIGURACIÓN DE APIS ===
TELEGRAM_TOKEN = "8476115829:AAFm51KhUsNTxLrbF1HmEAUbMx9yn336woY"
GEMINI_KEY = "AIzaSyCxLycdk0Gh9BRf6nwDCfNxHmBUGn_bGoY"
WEATHER_KEY = "2762051ad62d06f1d0fe146033c1c7c8"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

# === 2. BASE DE DATOS SIMPLE ===
def guardar_usuario(chat_id, lat, lon):
    data = {}
    if os.path.exists('usuarios.json'):
        with open('usuarios.json', 'r') as f:
            data = json.load(f)
    data[str(chat_id)] = {"lat": lat, "lon": lon}
    with open('usuarios.json', 'w') as f:
        json.dump(data, f, indent=4)

def obtener_usuario(chat_id):
    if os.path.exists('usuarios.json'):
        with open('usuarios.json', 'r') as f:
            data = json.load(f)
            return data.get(str(chat_id))
    return None

# === 3. LÓGICA DE CLIMA ===
def obtener_clima(lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric&lang=es"
    try:
        r = requests.get(url).json()
        if r.get("cod") != 200:
            print(f"❌ Error Clima: {r.get('message')}")
            return None
        return {
            "temp": r['main']['temp'],
            "hum": r['main']['humidity'],
            "viento": round(r['wind']['speed'] * 3.6, 1),
            "desc": r['weather'][0]['description']
        }
    except: return None

# === 4. COMANDOS TELEGRAM ===
@bot.message_handler(commands=['start'])
def inicio(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🌦️ Clima Actual", "🆘 Consulta IA")
    bot.send_message(message.chat.id, 
        "🌾 **AgroGuardian Activo**\nEnviame tu **ubicación** (📎) para empezar.",
        reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['location'])
def recibir_ubicacion(message):
    guardar_usuario(message.chat.id, message.location.latitude, message.location.longitude)
    bot.send_message(message.chat.id, "✅ Lote guardado. Ya podés consultar el clima o la IA.")

@bot.message_handler(func=lambda m: m.text == "🌦️ Clima Actual")
def reporte_clima(message):
    user = obtener_usuario(message.chat.id)
    if not user:
        bot.send_message(message.chat.id, "📍 Enviame tu ubicación primero.")
        return
    c = obtener_clima(user['lat'], user['lon'])
    if c:
        texto = f"🌡️ **Temp:** {c['temp']}°C\n💧 **Humedad:** {c['hum']}%\n🌬️ **Viento:** {c['viento']} km/h\n☁️ **Cielo:** {c['desc']}"
        bot.send_message(message.chat.id, texto, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "⚠️ Error en API de Clima (Esperá 30 min si es nueva).")

@bot.message_handler(func=lambda m: m.text == "🆘 Consulta IA")
def consulta_ia(message):
    msg = bot.send_message(message.chat.id, "Escribí tu duda agronómica:")
    bot.register_next_step_handler(msg, procesar_ia)

def procesar_ia(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        res = ai_model.generate_content(f"Agrónomo experto, responde breve: {message.text}").text
        bot.send_message(message.chat.id, f"🧠 **Asesor:** {res}")
    except:
        bot.send_message(message.chat.id, "❌ Error en IA.")

print("🚀 AgroGuardian funcionando en @AgroGuardian_IA_bot")
bot.infinity_polling()