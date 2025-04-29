# ai_config.py
import os

# --- Selección del Proveedor Activo ---
# Cambia esto para seleccionar el proveedor a usar: "OpenAI", "Google", "Anthropic", "OpenRouter"
# También se puede configurar mediante la variable de entorno AI_PROVIDER
AI_PROVIDER = os.environ.get("AI_PROVIDER", "OpenRouter" \
"")

# --- Configuración Específica por Proveedor ---
# Define los detalles necesarios para cada proveedor soportado.
PROVIDERS_CONFIG = {
    "OpenAI": {
        "api_key_env_var": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-3.5-turbo",
        "endpoint": "/chat/completions", # Endpoint para chat
        "auth_scheme": "Bearer", # Esquema de autenticación
    },
    "Google": {
        "api_key_env_var": "GOOGLE_API_KEY",
        # La URL base de Google Gemini puede variar, esta es una común.
        # El endpoint se construye de forma diferente (incluye el modelo).
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "default_model": "models/gemini-1.5-flash-latest",
        # Google usa ?key=API_KEY en la URL en lugar de cabecera Authorization
        "auth_scheme": "QueryParam",
        "auth_param_name": "key",
    },
    "Anthropic": {
        "api_key_env_var": "ANTHROPIC_API_KEY",
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-3-sonnet-20240229",
        "endpoint": "/messages", # Endpoint de Anthropic
        "auth_scheme": "Header", # Usa cabecera x-api-key
        "auth_header_name": "x-api-key",
        "headers": { # Headers específicos requeridos por Anthropic
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
    },
    "OpenRouter": {
        # OpenRouter actúa como un proxy, usando a menudo la misma clave que OpenAI
        "api_key_env_var": "OPENROUTER_API_KEY", # O usar OPENAI_API_KEY si es la misma
        "base_url": "https://openrouter.ai/api/v1",
        # Los modelos en OpenRouter requieren el prefijo del proveedor original
        "default_model": os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-pro-preview-03-25"),
        "endpoint": "/chat/completions", # Similar a OpenAI
        "auth_scheme": "Bearer",
        "headers": { # Headers opcionales recomendados por OpenRouter
            # "HTTP-Referer": "YOUR_SITE_URL", # Reemplazar si se usa
            # "X-Title": "YOUR_APP_NAME",     # Reemplazar si se usa
            "content-type": "application/json",
        }
    },
    "Ollama": {
        # Ollama generalmente se ejecuta localmente y no requiere clave API
        "api_key_env_var": None, # No necesita clave API por defecto
        # La URL base por defecto de Ollama
        "base_url": os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        # El modelo se especifica en la llamada, pero podemos tener uno por defecto
        # Asegúrate de que este modelo esté disponible en tu instancia de Ollama
        "default_model": os.environ.get("OLLAMA_MODEL", "phi4"),
        "endpoint": "/chat/completions", # Endpoint compatible con OpenAI
        "auth_scheme": None, # No requiere autenticación por defecto
        "headers": {
             "content-type": "application/json",
        }
    }
    # Añadir configuraciones para otros proveedores aquí si es necesario
}

# --- Selección del Modelo ---
# Usa el modelo por defecto del proveedor activo, o uno específico si se define por variable de entorno AI_MODEL
_active_provider_config = PROVIDERS_CONFIG.get(AI_PROVIDER, {})
AI_MODEL = os.environ.get("AI_MODEL", _active_provider_config.get("default_model", "proveedor_no_configurado"))

# --- Obtener la Clave API y Configuración del Proveedor Activo ---
API_KEY = None
PROVIDER_SETTINGS = {}
if AI_PROVIDER in PROVIDERS_CONFIG:
    PROVIDER_SETTINGS = PROVIDERS_CONFIG[AI_PROVIDER]
    API_KEY_ENV_VAR = PROVIDER_SETTINGS.get("api_key_env_var")
    if API_KEY_ENV_VAR: # Si el proveedor requiere una clave API
        API_KEY = os.environ.get(API_KEY_ENV_VAR)
        if not API_KEY:
            print(f"ADVERTENCIA: La variable de entorno '{API_KEY_ENV_VAR}' para el proveedor '{AI_PROVIDER}' no está configurada.")
    # else: # Si no requiere clave (como Ollama por defecto), no mostramos advertencia
    #    print(f"Info: El proveedor '{AI_PROVIDER}' no requiere una clave API según la configuración.")
else:
    print(f"ERROR: El proveedor '{AI_PROVIDER}' no está configurado en PROVIDERS_CONFIG en ai_config.py.")
    AI_MODEL = "proveedor_no_configurado"


# --- Plantilla del Prompt (Puede ser la misma o específica por proveedor) ---
# Esta plantilla funciona bien para modelos tipo chat como GPT, Gemini, Claude.
PROMPT_TEMPLATE = """
Eres un asistente experto en generar consultas SQL basadas en un esquema de base de datos.
El usuario proporcionará una descripción de los datos que desea y tú generarás una consulta SQL para obtenerlos.

Esquema de la Base de Datos:
{schema}

Consulta del Usuario:
{query}

Consulta SQL:
"""

# --- Formato de Respuesta Esperado (Generalmente texto/SQL para este caso) ---
RESPONSE_FORMAT = "SQL"

# --- Parámetros de Inferencia Comunes ---
# Se pueden sobrescribir con variables de entorno si es necesario
TEMPERATURE = float(os.environ.get("AI_TEMPERATURE", 0.5))
# Aumentamos el límite de tokens por defecto para evitar truncamiento
MAX_TOKENS = int(os.environ.get("AI_MAX_TOKENS", 8192))

# --- Otros Parámetros (Opcional, podrían ser específicos del proveedor) ---
# TOP_P = float(os.environ.get("AI_TOP_P", 1.0))
# FREQUENCY_PENALTY = float(os.environ.get("AI_FREQUENCY_PENALTY", 0.0))
# PRESENCE_PENALTY = float(os.environ.get("AI_PRESENCE_PENALTY", 0.0))

# --- Validación ---
# Solo advertir sobre la clave API si el proveedor la requiere
if PROVIDER_SETTINGS.get("api_key_env_var") and not API_KEY and AI_PROVIDER != "proveedor_no_configurado":
     print(f"ADVERTENCIA: La clave API para el proveedor '{AI_PROVIDER}' no se pudo obtener. Verifica la variable de entorno '{PROVIDER_SETTINGS.get('api_key_env_var', 'N/A')}'.")

# Puedes añadir más validaciones específicas si es necesario
print(f"--- Configuración IA Cargada ---")
print(f"Proveedor Activo: {AI_PROVIDER}")
print(f"Modelo Seleccionado: {AI_MODEL}")
# Indicar si se requiere y si está cargada
api_key_status = "No requerida"
if PROVIDER_SETTINGS.get("api_key_env_var"):
    api_key_status = "Sí" if API_KEY else "No (Requerida pero no encontrada)"
print(f"Clave API: {api_key_status}")
print(f"URL Base: {PROVIDER_SETTINGS.get('base_url', 'N/A')}")
print(f"-----------------------------")
