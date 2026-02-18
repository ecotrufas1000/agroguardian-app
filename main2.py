import telebot
import requests
import google.generativeai as genai
import json
import os
import datetime
from telebot import types
import re
from supabase import create_client

# Usá las mismas llaves que en la App
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def escapar_markdown_v2(texto: str) -> str:
    """
    Escapa todos los caracteres especiales de MarkdownV2 para Telegram.
    """
    caracteres = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(caracteres)}])', r'\\\1', texto)


# === CONFIGURACIÓN DE APIS ===

import os
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
WEATHER_KEY = os.getenv("WEATHER_KEY")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
WEATHER_KEY = os.getenv("WEATHER_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# === IA AUTO-DETECT ===
try:
    genai.configure(api_key=GEMINI_KEY.strip())
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    modelo_final = next((m for m in modelos if "flash" in m), modelos[0])
    ai_model = genai.GenerativeModel(modelo_final)
    print(f"✅ IA Conectada: {modelo_final}")
except Exception as e:
    print("⚠️ Error IA:", e)

# === TABLA MAESTRA KC (FAO-56) ===
TABLA_KC = {
    "🍀 Pastura (Alfalfa/Mix)": {"Inicial": 1.00, "Medio": 1.00, "Final": 1.00, "Tipo": "Cereal"},
    "🌽 Maíz": {"Inicial": 0.30, "Medio": 1.20, "Final": 0.50, "Tipo": "Cereal"},
    "🌾 Trigo": {"Inicial": 0.30, "Medio": 1.15, "Final": 0.25, "Tipo": "Cereal"},
    "🌱 Soja": {"Inicial": 0.40, "Medio": 1.15, "Final": 0.50, "Tipo": "Cereal"},
    "🍎 Manzano/Peral": {"Inicial": 0.45, "Medio": 0.95, "Final": 0.70, "Tipo": "Frutal"},
    "🍊 Cítricos": {"Inicial": 0.70, "Medio": 0.65, "Final": 0.70, "Tipo": "Frutal"},
    "🍇 Vid (Uva)": {"Inicial": 0.30, "Medio": 0.70, "Final": 0.45, "Tipo": "Frutal"},
    "🥬 Hortalizas de Hoja": {"Inicial": 0.70, "Medio": 1.00, "Final": 0.90, "Tipo": "Hortícola"},
    "🍅 Tomate": {"Inicial": 0.60, "Medio": 1.15, "Final": 0.80, "Tipo": "Hortícola"},
    "🥔 Papa": {"Inicial": 0.50, "Medio": 1.15, "Final": 0.75, "Tipo": "Hortícola"}
}

# === FUNCIONES DE APOYO ===
def escapar_markdown_v2(texto: str) -> str:
    caracteres = r'_*[]()~`>#+-=|{}.!'
    return ''.join(f'\\{c}' if c in caracteres else c for c in texto)

def enviar_mensaje_largo(chat_id, texto, reply_markup=None):
    MAX = 4000
    for i in range(0, len(texto), MAX):
        bot.send_message(chat_id, texto[i:i+MAX], reply_markup=reply_markup if i == 0 else None, parse_mode="MarkdownV2")

def menu_principal():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add("🔵 CLIMA ACTUAL", "📅 PRONÓSTICO 7 DÍAS")
    markup.add("🟢 ANALIZAR FOTO AI", "📝 ANOTAR NOVEDAD")
    markup.add("🟡 BALANCE HÍDRICO", "🆘 CONSULTA TÉCNICA")
    markup.add("📖 VER BITÁCORA", "📥 DESCARGAR")
    return markup

def obtener_usuario(chat_id):
    if os.path.exists('usuarios.json'):
        with open('usuarios.json', 'r', encoding='utf-8') as f:
            try: return json.load(f).get(str(chat_id))
            except: return None
    return None

def guardar_usuario(chat_id, lat, lon):
    # --- PARTE A: Guardar en el archivo local del Bot ---
    data = {}
    if os.path.exists('usuarios.json'):
        with open('usuarios.json', 'r', encoding='utf-8') as f:
            try: data = json.load(f)
            except: data = {}
    
    # Mantenemos la lógica de la suscripción (15 días)
    vence = data.get(str(chat_id), {}).get("vence", (datetime.datetime.now() + datetime.timedelta(days=15)).strftime("%Y-%m-%d"))
    data[str(chat_id)] = {"lat": lat, "lon": lon, "vence": vence}
    
    with open('usuarios.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

    # --- PARTE B: Enviar a la App (Supabase) ---
    try:
        datos_nube = {
            "fecha": datetime.datetime.now().isoformat(),
            "lote": "GPS DINAMICO",
            "mm": 0,
            "lat": lat,
            "lon": lon
        }
        supabase.table("registros_lluvia").insert(datos_nube).execute()
        print(f"🛰️ Ubicación enviada a la App: {lat}, {lon}")
    except Exception as e:
        print(f"⚠️ No se pudo actualizar el mapa de la App: {e}")

def es_activo(chat_id):
    u = obtener_usuario(chat_id)
    if not u: return False
    return datetime.datetime.now() <= datetime.datetime.strptime(u['vence'], "%Y-%m-%d")

# === HANDLERS ===

# --- Ubicación ---
@bot.message_handler(content_types=['location'])
def geo(message):
    lat = message.location.latitude
    lon = message.location.longitude
    guardar_usuario(message.chat.id, lat, lon)
    url_app = "https://agroguardian-app-eowdpzrknk8ybcuyf78gmq.streamlit.app/"
    mensaje_exito = escapar_markdown_v2(
        f"✅ ¡Lote Sincronizado!\n📍 Coordenadas: `{lat}, {lon}`\n\n👉 [ABRIR PANEL MÓVIL]({url_app})"
    )
    bot.send_message(message.chat.id, mensaje_exito, reply_markup=menu_principal(), parse_mode="MarkdownV2")

# --- Clima actual ---
@bot.message_handler(func=lambda m: "CLIMA ACTUAL" in m.text)
def reporte_clima(message):
    u = obtener_usuario(message.chat.id)
    if not u: return bot.send_message(message.chat.id, "📍 Primero enviame tu ubicación (📎).")
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={u['lat']}&lon={u['lon']}&appid={WEATHER_KEY}&units=metric&lang=es"
        r = requests.get(url).json()
        texto = escapar_markdown_v2(
            f"🌡️ Temp: **{r['main']['temp']}°C**\n🌬️ Viento: **{round(r['wind']['speed']*3.6)} km/h**\n💧 Humedad: **{r['main']['humidity']}%**\n☁️ {r['weather'][0]['description'].capitalize()}"
        )
        bot.send_message(message.chat.id, f"🛰️ **TIEMPO REAL**\n━━━━━━━━━━━━\n{texto}", parse_mode="MarkdownV2", reply_markup=menu_principal())
    except: bot.send_message(message.chat.id, "❌ Error de conexión.")

# --- Balance hídrico interactivo ---
@bot.message_handler(func=lambda m: "BALANCE HÍDRICO" in m.text)
def balance_hidrico(message):
    u = obtener_usuario(message.chat.id)
    if not u:
        return bot.send_message(message.chat.id, "📍 Primero enviame tu ubicación (📎).")

    # Crear teclado con cultivos de la tabla KC
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    for cultivo in TABLA_KC.keys():
        markup.add(cultivo)
    msg = bot.send_message(message.chat.id, "🌱 Selecciona tu cultivo:", reply_markup=markup)
    bot.register_next_step_handler(msg, seleccionar_etapa)

# --- Selección de etapa de crecimiento ---
def seleccionar_etapa(message):
    cultivo = message.text
    if cultivo not in TABLA_KC:
        return bot.send_message(message.chat.id, "❌ Cultivo no válido. Intenta de nuevo.", reply_markup=menu_principal())

    # Teclado con etapas: Inicial, Medio, Final
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=True)
    for etapa in ["Inicial", "Medio", "Final"]:
        markup.add(etapa)
    msg = bot.send_message(message.chat.id, f"🌱 Cultivo: {cultivo}\nSelecciona la etapa de desarrollo:", reply_markup=markup)
    bot.register_next_step_handler(msg, calcular_balance, cultivo)

# --- Cálculo y reporte del balance hídrico ---
def calcular_balance(message, cultivo):
    etapa = message.text
    if etapa not in ["Inicial", "Medio", "Final"]:
        return bot.send_message(message.chat.id, "❌ Etapa no válida.", reply_markup=menu_principal())

    kc = TABLA_KC[cultivo][etapa]
    tipo = TABLA_KC[cultivo]["Tipo"]

    # Aquí se podría usar datos de evapotranspiración real o ficticia
    # Para ejemplo, calculamos balance simple: Balance = Precipitación - KC*ET0
    # Supongamos ET0 promedio 5 mm/día y precipitación 10 mm
    ET0 = 5
    precip = 10
    balance = precip - kc * ET0

    texto = escapar_markdown_v2(
        f"🟢 **BALANCE HÍDRICO**\n━━━━━━━━━━━━\n"
        f"🌱 Cultivo: {cultivo}\n"
        f"📈 Etapa: {etapa}\n"
        f"💧 KC: {kc}\n"
        f"💦 Balance hídrico estimado: {balance:.2f} mm/día\n"
        f"📊 Tipo: {tipo}"
    )

    bot.send_message(message.chat.id, texto, parse_mode="MarkdownV2", reply_markup=menu_principal())

    # Guardar en estado_lote.json para histórico
    estado = {}
    if os.path.exists('estado_lote.json'):
        with open('estado_lote.json', 'r', encoding='utf-8') as f:
            try:
                estado = json.load(f)
            except: estado = {}
    estado[cultivo] = {
        "Etapa": etapa,
        "KC": kc,
        "Balance": round(balance, 2),
        "Tipo": tipo,
        "Fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    with open('estado_lote.json', 'w', encoding='utf-8') as f:
        json.dump(estado, f, indent=4)

# --- ANALIZAR FOTO AI ---
@bot.message_handler(func=lambda m: "ANALIZAR FOTO" in m.text)
def pedir_foto(message):
    if not es_activo(message.chat.id):
        return bot.send_message(message.chat.id, "🚫 Suscripción vencida.")
    msg = bot.send_message(message.chat.id, "📸 Envíame la foto del cultivo:")
    bot.register_next_step_handler(msg, procesar_foto)

def procesar_foto(message):
    if not message.photo:
        return bot.send_message(message.chat.id, "❌ No recibí ninguna imagen. Intenta de nuevo.", reply_markup=menu_principal())

    try:
        # 1️⃣ Descargar imagen desde Telegram
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)

        # Guardar imagen temporalmente
        img_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        img_filename = f"img_{img_id}.jpg"
        with open(img_filename, "wb") as f:
            f.write(downloaded)

        # 2️⃣ Subir imagen a Gemini (o la IA que uses)
        img_blob = genai.upload_file(img_filename)

        # 3️⃣ Prompt de análisis
        prompt = (
            "Sos un ingeniero agrónomo. "
            "Analizá esta imagen agrícola y brindá un diagnóstico claro en máximo 5 bullets. "
            "Indicá si hay problemas de sanidad, nutrición o estrés hídrico "
            "y sugerí acciones prácticas y concretas."
        )

        # 4️⃣ Llamada a la IA
        response = ai_model.generate_content([prompt, img_blob])

        # 5️⃣ Enviar respuesta a Telegram
        texto_seguro = escapar_markdown_v2(response.text)
        texto_final = f"🧠 Diagnóstico AI:\n\n{texto_seguro}"
        enviar_mensaje_largo(
            message.chat.id,
            texto_final,
            reply_markup=menu_principal()
        )

        # 6️⃣ Guardar en bitácora
        cultivo = "No especificado"
        if os.path.exists("estado_lote.json"):
            try:
                with open("estado_lote.json", "r", encoding="utf-8") as f:
                    estado = json.load(f)
                    cultivo = estado.get("cultivo", "No especificado")
            except:
                pass

        with open("bitacora_campo.txt", "a", encoding="utf-8") as f:
            f.write(f"📅 {datetime.datetime.now().strftime('%d/%m %H:%M')} | Cultivo: {cultivo} | Imagen: {img_filename}\n")
            f.write(response.text + "\n\n")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error analizando la imagen:\n{e}", reply_markup=menu_principal())

    finally:
        # Borrar la imagen temporal
        if os.path.exists(img_filename):
            os.remove(img_filename)
# --- PRONÓSTICO 7 DÍAS ---
@bot.message_handler(func=lambda m: "PRONÓSTICO 7 DÍAS" in m.text)
def pronostico_7dias(message):
    u = obtener_usuario(message.chat.id)
    if not u:
        return bot.send_message(message.chat.id, "📍 Primero enviame tu ubicación (📎).")

    try:
        # Llamada a la API de OpenWeatherMap (forecast 5 días cada 3h)
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={u['lat']}&lon={u['lon']}&appid={WEATHER_KEY}&units=metric&lang=es"
        res = requests.get(url).json()

        if 'list' not in res:
            return bot.send_message(message.chat.id, "❌ No se pudieron obtener datos de pronóstico.")

        # Agrupar datos por día
        pronostico_por_dia = {}
        for bloque in res['list']:
            fecha = bloque['dt_txt'].split(' ')[0]  # yyyy-mm-dd
            temp = bloque['main']['temp']
            descripcion = bloque['weather'][0]['description'].capitalize()
            viento = round(bloque['wind']['speed'] * 3.6)  # km/h
            humedad = bloque['main']['humidity']

            if fecha not in pronostico_por_dia:
                pronostico_por_dia[fecha] = []
            pronostico_por_dia[fecha].append({
                "temp": temp,
                "descripcion": descripcion,
                "viento": viento,
                "humedad": humedad
            })

        # Construir mensaje resumen por día
        texto = "📅 **PRONÓSTICO 7 DÍAS**\n━━━━━━━━━━━━\n"
        for fecha, datos in list(pronostico_por_dia.items())[:7]:
            temp_min = min(d['temp'] for d in datos)
            temp_max = max(d['temp'] for d in datos)
            descripcion_comun = max(set(d['descripcion'] for d in datos), key=lambda x: sum(d['descripcion']==x for d in datos))
            viento_prom = round(sum(d['viento'] for d in datos)/len(datos))
            humedad_prom = round(sum(d['humedad'] for d in datos)/len(datos))

            texto += (
                f"📌 {fecha}\n"
                f"🌡️ Temp: {temp_min}°C - {temp_max}°C\n"
                f"☁️ {descripcion_comun}\n"
                f"🌬️ Viento: {viento_prom} km/h | 💧 Humedad: {humedad_prom}%\n━━━━━━━━━━━━\n"
            )

        # ESCAPAR MarkdownV2 antes de enviar
        texto_seguro = escapar_markdown_v2(texto)

        # Enviar mensaje largo
        enviar_mensaje_largo(message.chat.id, texto_seguro, reply_markup=menu_principal())

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error obteniendo pronóstico: {e}", reply_markup=menu_principal())



# --- Anotar novedad ---
@bot.message_handler(func=lambda m: "ANOTAR NOVEDAD" in m.text)
def anotar_novedad(message):
    msg = bot.send_message(message.chat.id, "📝 Escribe tu nota o novedad del lote:")
    bot.register_next_step_handler(msg, guardar_novedad)

def guardar_novedad(message):
    texto = message.text
    with open('bitacora_campo.txt', 'a', encoding='utf-8') as f:
        f.write(f"{datetime.datetime.now()} | NOTA | {texto}\n")
    bot.send_message(message.chat.id, "✅ Novedad guardada.", reply_markup=menu_principal())

# --- Ver bitácora ---
@bot.message_handler(func=lambda m: "VER BITÁCORA" in m.text)
def ver_bitacora(message):
    if not os.path.exists('bitacora_campo.txt'):
        return bot.send_message(message.chat.id, "_No hay entradas aún_")
    with open('bitacora_campo.txt', 'r', encoding='utf-8') as f:
        contenido = f.read()
    enviar_mensaje_largo(message.chat.id, escapar_markdown_v2(contenido), reply_markup=menu_principal())
# --- FUNCION AUXILIAR PARA GUARDAR EN BITÁCORA ---
def guardar_en_bitacora(chat_id, texto, tipo="Consulta Técnica"):
    """Guarda un registro en la bitácora con fecha, chat_id y tipo de mensaje"""
    with open("bitacora_campo.txt", "a", encoding="utf-8") as f:
        f.write(f"📅 {datetime.datetime.now().strftime('%d/%m %H:%M')} | ChatID: {chat_id} | Tipo: {tipo}\n")
        f.write(texto + "\n\n")


# --- CONSULTA TÉCNICA ---
@bot.message_handler(func=lambda m: "CONSULTA TÉCNICA" in m.text)
def consulta(message):
    msg = bot.send_message(message.chat.id, "🆘 Escribí tu duda:")
    bot.register_next_step_handler(msg, responder_consulta)

def responder_consulta(message):
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        # Llamada a la IA (Gemini o tu modelo)
        res = ai_model.generate_content(f"Agrónomo responde: {message.text}")

        # Escapar MarkdownV2 antes de enviar
        texto_seguro = escapar_markdown_v2(res.text)

        # Enviar la respuesta
        enviar_mensaje_largo(
           message.chat.id,
           f"🧠 **Asesoría técnica:**\n\n{texto_seguro}",
           reply_markup=menu_principal()
        )

        # --- GUARDAR EN BITÁCORA ---
        with open("bitacora.txt", "a", encoding="utf-8") as f:
            f.write(f"Usuario: {message.chat.id}\n")
            f.write(f"Duda: {escapar_markdown_v2(message.text)}\n")
            f.write(f"Respuesta IA: {texto_seguro}\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ Error IA: {escapar_markdown_v2(str(e))}",
            reply_markup=menu_principal()
        )

# === INICIO POLLING ===
print("🤖 Bot iniciado...")
bot.infinity_polling()


