# inicializacion_supabase.py
import os
from supabase import create_client
from dotenv import load_dotenv

# Cargar variables de .env
load_dotenv()  # busca .env en el mismo directorio o en la raíz

def get_supabase_client():
    # Leemos directamente desde .env
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        # Devuelve None si no hay credenciales
        print("❌ Supabase no está configurado. Revisa tu .env")
        return None

    try:
        return create_client(url, key)
    except Exception as e:
        print(f"❌ Error al conectar con Supabase: {e}")
        return NoneS