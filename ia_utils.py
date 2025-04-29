# ia_utils.py
import requests
import json
import os
# Importar la configuración centralizada
import ai_config

# --------------------------------------------------------------------------
# Función Genérica para Llamar a la API de IA (Movida aquí)
# --------------------------------------------------------------------------
def llamar_api_ia(messages, system_prompt=None, model=None, temperature=None, max_tokens=None):
    """
    Función genérica para llamar a la API del proveedor de IA configurado.

    Args:
        messages (list): Lista de diccionarios de mensajes (ej. [{"role": "user", "content": "..."}]).
                         Para Google, se espera un formato diferente que se adapta internamente.
        system_prompt (str, optional): Prompt del sistema. No todos los proveedores lo usan igual.
        model (str, optional): Modelo a usar, sobrescribe el de ai_config.
        temperature (float, optional): Temperatura, sobrescribe la de ai_config.
        max_tokens (int, optional): Máximo de tokens, sobrescribe el de ai_config.

    Returns:
        dict: La respuesta JSON de la API, o None si hay un error.
    """
    # --- Validaciones Iniciales ---
    if ai_config.AI_PROVIDER == "proveedor_no_configurado":
        print("Error: El proveedor de IA no está configurado correctamente en ai_config.py.")
        return None
    # Verificar clave API solo si es requerida por el proveedor
    provider_requires_key = ai_config.PROVIDER_SETTINGS.get("api_key_env_var")
    if provider_requires_key and not ai_config.API_KEY:
        api_key_var = ai_config.PROVIDER_SETTINGS.get('api_key_env_var', 'N/A')
        print(f"Error: La clave API para {ai_config.AI_PROVIDER} no se encontró.")
        print(f"Asegúrate de que la variable de entorno '{api_key_var}' esté configurada.")
        return None

    # --- Determinar Parámetros ---
    active_model = model if model else ai_config.AI_MODEL
    active_temperature = temperature if temperature is not None else ai_config.TEMPERATURE
    active_max_tokens = max_tokens if max_tokens is not None else ai_config.MAX_TOKENS
    provider_settings = ai_config.PROVIDER_SETTINGS

    print(f"\n--- Llamando a IA ({ai_config.AI_PROVIDER} / {active_model}) ---")

    # --- Construcción dinámica de la solicitud ---
    api_url = ""
    headers = {}
    payload = {}

    # 1. Construir URL
    base_url = provider_settings.get("base_url", "")
    endpoint = provider_settings.get("endpoint", "")

    if ai_config.AI_PROVIDER == "Google":
        # Google Gemini: URL incluye modelo y acción
        api_url = f"{base_url}/{active_model}:generateContent"
        if provider_settings.get("auth_scheme") == "QueryParam":
            api_url += f"?{provider_settings.get('auth_param_name', 'key')}={ai_config.API_KEY}"
    else:
        # OpenAI, Anthropic, OpenRouter, Ollama
        api_url = f"{base_url.rstrip('/')}{endpoint}"

    # 2. Construir Headers
    auth_scheme = provider_settings.get("auth_scheme")
    if auth_scheme == "Bearer":
        headers["Authorization"] = f"Bearer {ai_config.API_KEY}"
    elif auth_scheme == "Header":
        auth_header = provider_settings.get("auth_header_name", "x-api-key")
        headers[auth_header] = ai_config.API_KEY
    # Para Ollama (auth_scheme=None), no se añade cabecera de autorización

    headers.update(provider_settings.get("headers", {}))
    if "content-type" not in headers and "Content-Type" not in headers:
         headers["content-type"] = "application/json"

    # 3. Construir Payload
    # Adaptar la estructura de 'messages' y parámetros según el proveedor
    if ai_config.AI_PROVIDER in ["OpenAI", "OpenRouter", "Ollama"]:
        # Estos usan la estructura de mensajes de OpenAI
        final_messages = []
        if system_prompt:
            final_messages.append({"role": "system", "content": system_prompt})
        final_messages.extend(messages) # Añadir mensajes de usuario/asistente

        payload = {
            "model": active_model,
            "messages": final_messages,
            "temperature": active_temperature,
            "max_tokens": active_max_tokens,
            # "stream": False, # Podría añadirse como opción
        }
        # Ollama puede no soportar max_tokens, verificar documentación si da error
        if ai_config.AI_PROVIDER == "Ollama" and "max_tokens" in payload:
             # Considerar eliminar max_tokens o usar 'num_predict' en 'options' si es necesario
             # payload.pop("max_tokens")
             # payload["options"] = {"num_predict": active_max_tokens}
             pass # Por ahora lo dejamos, es compatible con la API OpenAI de Ollama

    elif ai_config.AI_PROVIDER == "Anthropic":
        # Anthropic usa 'system' y 'messages' sin rol 'system' dentro
        final_messages = [m for m in messages if m.get("role") != "system"] # Filtrar system de messages
        payload = {
            "model": active_model,
            "messages": final_messages,
            "temperature": active_temperature,
            "max_tokens": active_max_tokens,
        }
        if system_prompt:
            payload["system"] = system_prompt # Añadir system prompt aquí

    elif ai_config.AI_PROVIDER == "Google":
        # Google Gemini usa 'contents' y 'generationConfig'
        # Asumimos que 'messages' contiene un solo mensaje de usuario para simplificar
        # Una implementación más robusta manejaría historial de conversación
        user_content = ""
        if messages and messages[-1].get("role") == "user":
             user_content = messages[-1].get("content", "")
        # Podríamos intentar añadir el system_prompt si existe
        # La API de Gemini está evolucionando, verificar cómo incluirlo mejor
        payload = {
             "contents": [{"parts": [{"text": user_content}]}],
             "generationConfig": {
                 "temperature": active_temperature,
                 "maxOutputTokens": active_max_tokens,
             }
             # Añadir systemInstruction si la API lo soporta formalmente
             # if system_prompt:
             #    payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
         }
    else:
        print(f"Error: La construcción del payload para '{ai_config.AI_PROVIDER}' no está implementada.")
        return None

    # --- Realizar la llamada ---
    try:
        print(f"Llamando a API: {api_url}")
        # print(f"Headers: {headers}") # Descomentar para depurar
        # print(f"Payload: {json.dumps(payload, indent=2)}") # Descomentar para depurar

        response = requests.post(url=api_url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        # print(f"Respuesta API: {json.dumps(data, indent=2)}") # Descomentar para depurar

        # --- Añadir verificación de finish_reason ---
        try:
            if ai_config.AI_PROVIDER in ["OpenAI", "OpenRouter", "Ollama"]:
                 if data.get("choices") and len(data["choices"]) > 0:
                     finish_reason = data["choices"][0].get("finish_reason")
                     if finish_reason == "length":
                         print(f"ADVERTENCIA: La respuesta de la IA fue truncada porque alcanzó el límite de tokens (max_tokens={active_max_tokens}).")
                         # Considerar aumentar MAX_TOKENS en ai_config.py o revisar el prompt.
            # Añadir verificaciones similares para otros proveedores si tienen indicadores de truncamiento
            # elif ai_config.AI_PROVIDER == "Google":
            #     if data.get("candidates") and ... finishReason == "MAX_TOKENS" ...
            # elif ai_config.AI_PROVIDER == "Anthropic":
            #     if data.get("stop_reason") == "max_tokens": ...
        except Exception as check_e:
             print(f"Advertencia: No se pudo verificar finish_reason en la respuesta: {check_e}")
        # --- Fin verificación ---

        return data # Devolver el JSON crudo

    except requests.exceptions.RequestException as e:
        print(f"Error al llamar a la API de {ai_config.AI_PROVIDER}: {e}")
        if e.response is not None:
            try:
                error_details = e.response.json()
                print(f"Detalles del error ({e.response.status_code}): {json.dumps(error_details, indent=2)}")
            except json.JSONDecodeError:
                print(f"Detalles del error ({e.response.status_code}): {e.response.text}")
        return None
    except Exception as e:
        print(f"Error inesperado al llamar a la API: {e}")
        return None
