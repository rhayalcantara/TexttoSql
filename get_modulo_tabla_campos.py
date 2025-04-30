# Importar la función genérica de llamada a IA desde el nuevo archivo
from ia_utils import llamar_api_ia
# Importar configuración para saber qué proveedor se usa (para la extracción)
import ai_config
import re
import json
import argparse
import csv
import os
import glob # Para buscar archivos


# --- Funciones para leer Esquema ---

def cargar_modulos_disponibles(json_path="descripciones_modulos.json"):
    """Carga la lista de módulos desde el archivo JSON."""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Asegurarse que 'modulo' existe en cada item
        modulos = [item['modulo'] for item in data if 'modulo' in item]
        if len(modulos) != len(data):
            print(f"Advertencia: Algunos elementos en {json_path} no tienen la clave 'modulo'.")
        return modulos
    except FileNotFoundError:
        print(f"Error: El archivo {json_path} no fue encontrado.")
        return []
    except json.JSONDecodeError:
        print(f"Error: El archivo {json_path} no es un JSON válido.")
        return []
    except Exception as e:
        print(f"Error inesperado al cargar módulos: {e}")
        return []

def obtener_tablas_del_modulo(nombre_modulo):
    """
    Obtiene la lista de nombres de tablas para un módulo dado
    leyendo el archivo CSV correspondiente.
    """
    archivo_csv = f"FBS_{nombre_modulo}_schema.csv" # Asumiendo prefijo FBS_
    tablas = set() # Usamos un set para evitar duplicados
    print(f"DEBUG: Buscando tablas para el módulo: {nombre_modulo} en archivo: {archivo_csv}")
    try:
        with open(archivo_csv, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            # Asegurarse que la columna 'Table' existe
            if 'Table' not in reader.fieldnames:
                print(f"Error: El archivo {archivo_csv} no contiene la columna 'Table'.")
                return []
            for row in reader:
                nombre_completo_tabla = row['Table']
                # Esperamos formato como MODULO.TABLA o solo TABLA
                if '.' in nombre_completo_tabla:
                    # Extraer solo el nombre de la tabla después del primer punto
                    nombre_tabla_sin_prefijo = nombre_completo_tabla.split('.', 1)[1]
                    tablas.add(nombre_tabla_sin_prefijo)
                else:
                    # Si no tiene prefijo, añadirla tal cual
                    tablas.add(nombre_completo_tabla)
        print(f"DEBUG: Tablas encontradas para {nombre_modulo}: {list(tablas)}")
        return sorted(list(tablas))
    except FileNotFoundError:
        print(f"Advertencia: Archivo de esquema no encontrado: {archivo_csv}. Intentando sin prefijo FBS_...")
        # Intento alternativo sin prefijo FBS_
        archivo_csv_alt = f"{nombre_modulo}_schema.csv"
        try:
            with open(archivo_csv_alt, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if 'Table' not in reader.fieldnames:
                    print(f"Error: El archivo {archivo_csv_alt} no contiene la columna 'Table'.")
                    return []
                for row in reader:
                    nombre_completo_tabla = row['Table']
                    if '.' in nombre_completo_tabla:
                        nombre_tabla_sin_prefijo = nombre_completo_tabla.split('.', 1)[1]
                        tablas.add(nombre_tabla_sin_prefijo)
                    else:
                        tablas.add(nombre_completo_tabla)
            print(f"DEBUG: Tablas encontradas (sin prefijo FBS_) para {nombre_modulo}: {list(tablas)}")
            return sorted(list(tablas))
        except FileNotFoundError:
             print(f"Advertencia: Archivo de esquema tampoco encontrado como: {archivo_csv_alt}")
             return []
        except Exception as e_alt:
             print(f"Error al leer {archivo_csv_alt}: {e_alt}")
             return []
    except Exception as e:
        print(f"Error al leer {archivo_csv}: {e}")
        return []


def obtener_campos_de_tabla(nombre_tabla_buscada):
    """
    Obtiene la lista de nombres de campos para una tabla dada,
    buscando en todos los archivos *_schema.csv.
    """
    campos = set()
    print(f"DEBUG: Buscando campos para la tabla: {nombre_tabla_buscada} en todos los CSV...")
    archivos_csv = glob.glob('*_schema.csv') # Busca todos los archivos que terminen en _schema.csv

    if not archivos_csv:
        print("Advertencia: No se encontraron archivos *_schema.csv en el directorio.")
        return []

    for archivo_csv in archivos_csv:
        try:
            with open(archivo_csv, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if 'Table' not in reader.fieldnames or 'Column Name' not in reader.fieldnames:
                    # print(f"Advertencia: Saltando archivo {archivo_csv} (faltan columnas 'Table' o 'Column Name').")
                    continue # Silencioso para no llenar el log

                for row in reader:
                    nombre_completo_tabla = row['Table']
                    nombre_tabla_sin_prefijo = nombre_completo_tabla
                    if '.' in nombre_completo_tabla:
                        # Extraer solo el nombre de la tabla después del primer punto
                        partes = nombre_completo_tabla.split('.', 1)
                        if len(partes) > 1:
                            nombre_tabla_sin_prefijo = partes[1]
                        else: # Caso raro: termina en punto?
                            nombre_tabla_sin_prefijo = partes[0]


                    # Comparamos el nombre de tabla sin prefijo (case-insensitive)
                    if nombre_tabla_sin_prefijo.lower() == nombre_tabla_buscada.lower():
                        campos.add(row['Column Name'])

        except Exception as e:
            print(f"Error al procesar {archivo_csv}: {e}")
            # Continuar con el siguiente archivo

    print(f"DEBUG: Campos encontrados para {nombre_tabla_buscada}: {list(campos)}")
    return sorted(list(campos))


# --- Funciones de Interacción con IA (Refactorizadas) ---

def llamar_ia(prompt_usuario, contexto_sistema):
    """
    Prepara el prompt y llama a la función genérica `llamar_api_ia`.
    Espera una respuesta JSON que contenga una lista bajo la clave 'resultado'.
    """
    # Construir el prompt completo para el mensaje de usuario,
    # incluyendo la instrucción de formato JSON.
    prompt_completo_usuario = f"""Basado en la siguiente solicitud del usuario y el contexto proporcionado (en el mensaje del sistema), responde únicamente con un array JSON que contenga los elementos solicitados. El array debe estar bajo la clave 'resultado'. No incluyas ninguna otra explicación o texto adicional fuera del JSON.

Solicitud del usuario: "{prompt_usuario}"

Respuesta JSON esperada (ejemplo):
{{
  "resultado": ["elemento1", "elemento2", ...]
}}

Tu respuesta JSON:"""

    # Preparar mensajes para la función genérica
    messages = [{"role": "user", "content": prompt_completo_usuario}]

    # Llamar a la función genérica (usará el proveedor/modelo de ai_config)
    respuesta_json = llamar_api_ia(messages=messages, system_prompt=contexto_sistema)

    if not respuesta_json:
        return [] # Error ya impreso en llamar_api_ia

    # Extraer el contenido de texto de la respuesta según el proveedor
    texto_respuesta = None
    try:
        if ai_config.AI_PROVIDER in ["OpenAI", "OpenRouter", "Ollama"]:
            if respuesta_json.get("choices") and len(respuesta_json["choices"]) > 0:
                message = respuesta_json["choices"][0].get("message", {})
                texto_respuesta = message.get("content", "").strip()
        elif ai_config.AI_PROVIDER == "Anthropic":
             if respuesta_json.get("content") and len(respuesta_json["content"]) > 0:
                 for block in respuesta_json["content"]:
                     if block.get("type") == "text":
                         texto_respuesta = block.get("text", "").strip()
                         break
        elif ai_config.AI_PROVIDER == "Google":
             if respuesta_json.get("candidates") and len(respuesta_json["candidates"]) > 0:
                 content = respuesta_json["candidates"][0].get("content", {})
                 if content.get("parts") and len(content["parts"]) > 0:
                     texto_respuesta = content["parts"][0].get("text", "").strip()

        if not texto_respuesta:
            print(f"Error: No se pudo extraer contenido de texto de la respuesta de {ai_config.AI_PROVIDER}.")
            print(f"Respuesta recibida: {json.dumps(respuesta_json, indent=2)}")
            return []

        # --- Limpieza robusta de Markdown y Parseo JSON ---
        print(f"DEBUG: Texto crudo recibido de IA: '{texto_respuesta}'") # Ver la respuesta cruda
        if "<think>" in texto_respuesta and "</think>" in texto_respuesta:
            texto_respuesta = texto_respuesta.split("<think>")[0] + texto_respuesta.split("</think>")[1]
            print(f"DEBUG: Texto después de eliminar <think>: '{texto_respuesta}'")
        
        # # Eliminar ```json al inicio (con posible espacio/salto de línea)
        # if texto_respuesta.startswith("```json"):
        #     texto_respuesta = texto_respuesta[len("```json"):].lstrip() # lstrip() quita espacios/saltos iniciales
        #     print(f"DEBUG: Texto después de eliminar ```json: '{texto_respuesta}'") # Ver texto limpio
        # # Eliminar ``` al final (con posible espacio/salto de línea)
        # if texto_respuesta.endswith("```"):
        #     texto_respuesta = texto_respuesta[:-len("```")].rstrip() # rstrip() quita espacios/saltos finales
        #     print(f"DEBUG: Texto después de eliminar ``` al final: '{texto_respuesta}'") # Ver texto limpio
        
                # Intentar extraer contenido entre ```json y ``` usando expresiones regulares
        # El patrón busca ```json, luego captura cualquier cosa (.*?) de forma no codiciosa,
        # hasta encontrar ```. re.DOTALL permite que '.' coincida con saltos de línea.
        # \s* permite espacios opcionales alrededor del contenido capturado.
        pattern = r"```json\s*(.*?)\s*```"
        match = re.search(pattern, texto_respuesta, re.DOTALL)

        if match:
            # Si se encuentra el patrón, extraer el grupo capturado (el contenido JSON)
            texto_para_parsear = match.group(1).strip() # group(1) es el contenido dentro de (.*?)
            print(f"DEBUG: Contenido extraído entre ```json y ```: '{texto_para_parsear}'")
        else:
            # Si no se encuentra el patrón ```json...```, usar el texto como está
            # (ya potencialmente limpio de <think> tags).
            # Esto maneja casos donde la IA podría devolver JSON directamente sin los marcadores.
            texto_para_parsear = texto_respuesta.strip()
            print(f"DEBUG: No se encontró el patrón ```json...```. Usando texto (posiblemente sin <think>): '{texto_para_parsear}'")

        texto_respuesta = texto_para_parsear # Limpieza final

        print(f"DEBUG: Texto después de limpiar Markdown: '{texto_respuesta}'") # Ver texto limpio

        # Intentar parsear el texto como JSON y extraer 'resultado'
        try:
            data = json.loads(texto_respuesta)
            print(f"DEBUG: Texto parseado como JSON: {data}") # Ver el JSON parseado
            if isinstance(data, dict) and 'resultado' in data and isinstance(data['resultado'], list):
                 print(f"DEBUG: JSON parseado correctamente. Resultado: {data['resultado']}")
                 return data['resultado']
            else:
                 print(f"ADVERTENCIA: La respuesta JSON no tiene el formato esperado (falta 'resultado' o no es lista): {texto_respuesta}")
                 # Intento alternativo: si la respuesta es directamente la lista como string
                 try:
                     list_data = json.loads(texto_respuesta)
                     if isinstance(list_data, list):
                         print(f"DEBUG: Interpretado como lista JSON directamente. Resultado: {list_data}")
                         return list_data
                 except json.JSONDecodeError:
                     pass # Si falla, se devuelve lista vacía abajo
                 print(f"ADVERTENCIA: No se pudo interpretar la respuesta como lista JSON. Respuesta: {texto_respuesta}")
                 return [] # Devolver lista vacía si el formato no es el esperado
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON de la IA: {e}")
            print(f"Texto que se intentó decodificar: {texto_respuesta}")
            return []
        # --- Fin Limpieza y Parseo ---

    # Captura de errores al procesar la respuesta general de la IA (fuera del parseo JSON específico)
    except Exception as e:
        print(f"Error inesperado al procesar respuesta de IA: {e}")
        # Intentar imprimir texto_respuesta si existe, si no, la respuesta_json cruda
        error_context = f"Texto Respuesta: '{texto_respuesta}'" if texto_respuesta is not None else f"Respuesta JSON Cruda: {json.dumps(respuesta_json, indent=2)}"
        print(f"Contexto del error: {error_context}")
        return []


def obtener_modulos_por_ia(prompt_usuario, modulos_disponibles):
    """Paso 1: Obtiene los módulos relevantes."""
    contexto_sistema = f"""Eres un asistente experto en bases de datos financieras. Tu tarea es identificar qué módulos de base de datos son necesarios para responder a la solicitud del usuario. Los módulos disponibles son: {', '.join(modulos_disponibles)}. Selecciona solo los módulos estrictamente necesarios de esta lista."""
    print("\n--- Paso 1: Obteniendo Módulos ---")
    # Llama a la nueva función genérica
    modulos = llamar_ia(prompt_usuario, contexto_sistema)
    print(f"Módulos identificados por IA: {modulos}")
    # Filtrar para asegurar que solo devolvemos módulos que existen
    modulos_validos = [m for m in modulos if m in modulos_disponibles]
    if len(modulos_validos) != len(modulos):
        print(f"Advertencia: La IA sugirió módulos no disponibles: {list(set(modulos) - set(modulos_validos))}")
    return modulos_validos

def obtener_tablas_por_ia(prompt_usuario, modulo, tablas_disponibles):
    """Paso 2: Obtiene las tablas relevantes para un módulo."""
    if not tablas_disponibles:
        print(f"No hay tablas disponibles para el módulo {modulo}. Saltando.")
        return []
    contexto_sistema = f"""Eres un asistente experto en bases de datos financieras. Para el módulo '{modulo}', las tablas disponibles son: {', '.join(tablas_disponibles)}. Basado en la solicitud del usuario: '{prompt_usuario}', identifica qué tablas de esta lista son necesarias. Selecciona solo las tablas estrictamente necesarias."""
    print(f"\n--- Paso 2: Obteniendo Tablas para el Módulo: {modulo} ---")
    # Llama a la nueva función genérica
    tablas = llamar_ia(prompt_usuario, contexto_sistema)
    print(f"Tablas identificadas por IA para {modulo}: {tablas}")
    # Filtrar para asegurar que solo devolvemos tablas que existen para este módulo
    tablas_validas = [t for t in tablas if t in tablas_disponibles]
    if len(tablas_validas) != len(tablas):
        print(f"Advertencia: La IA sugirió tablas no disponibles para {modulo}: {list(set(tablas) - set(tablas_validas))}")
    return tablas_validas

def obtener_campos_por_ia(prompt_usuario, tabla, campos_disponibles):
    """Paso 3: Obtiene los campos relevantes para una tabla."""
    if not campos_disponibles:
        print(f"No hay campos disponibles para la tabla {tabla}. Saltando.")
        return []
    contexto_sistema = f"""Eres un asistente experto en bases de datos financieras. Para la tabla '{tabla}', los campos disponibles son: {', '.join(campos_disponibles)}. Basado en la solicitud del usuario: '{prompt_usuario}', identifica qué campos de esta lista son necesarios para construir la consulta o reporte. Selecciona solo los campos estrictamente necesarios."""
    print(f"\n--- Paso 3: Obteniendo Campos para la Tabla: {tabla} ---")
    # Llama a la nueva función genérica (DESCOMENTADO)
    campos = llamar_ia(prompt_usuario, contexto_sistema)
    print(f"Campos identificados por IA para {tabla}: {campos}")
    # Filtrar para asegurar que solo devolvemos campos que existen para esta tabla
    campos_validos = [c for c in campos if c in campos_disponibles]
    if len(campos_validos) != len(campos):
        print(f"Advertencia: La IA sugirió campos no disponibles para {tabla}: {list(set(campos) - set(campos_validos))}")
    return campos_validos # Devolver campos filtrados por IA y validados

# --- Flujo Principal ---
# Modificado para devolver estructura anidada y usar IA para campos
def main(prompt_usuario, archivo_desc_modulos="descripciones_modulos.json"):
    """
    Función principal refactorizada para ser importable.
    Identifica módulos, tablas y campos relevantes para un prompt dado,
    usando la configuración central de IA y devuelve una estructura anidada.
    """
    # Cargar módulos disponibles desde el JSON
    modulos_disponibles = cargar_modulos_disponibles(archivo_desc_modulos)
    if not modulos_disponibles:
        print("No se pudieron cargar los módulos disponibles. Saliendo.")
        return None # Devolver None en caso de error

    print(f"Módulos disponibles cargados: {len(modulos_disponibles)}")
    # El modelo se obtiene de ai_config, no se pasa como parámetro
    print(f"Usando IA configurada: {ai_config.AI_PROVIDER} / {ai_config.AI_MODEL}")
    print(f"Prompt del usuario: {prompt_usuario}")

    # Paso 1: Obtener Módulos
    modulos_seleccionados = obtener_modulos_por_ia(prompt_usuario, modulos_disponibles)
    if not modulos_seleccionados:
        print("No se pudieron identificar módulos relevantes.")
        return {} # Devolver diccionario vacío si no hay módulos

    # Estructura para el resultado final anidado
    resultado_anidado = {}

    # Paso 2 y 3: Obtener Tablas y Campos (por cada módulo seleccionado)
    for modulo in modulos_seleccionados:
        tablas_del_modulo = obtener_tablas_del_modulo(modulo)
        if tablas_del_modulo:
            # Paso 2: Obtener tablas para este módulo
            tablas_seleccionadas_modulo = obtener_tablas_por_ia(prompt_usuario, modulo, tablas_del_modulo)

            if tablas_seleccionadas_modulo:
                tablas_y_campos_modulo = {} # Diccionario para las tablas y campos de este módulo
                # Paso 3: Obtener campos para cada tabla seleccionada en este módulo
                for tabla in tablas_seleccionadas_modulo:
                    campos_de_tabla = obtener_campos_de_tabla(tabla)
                    if campos_de_tabla:
                        # Obtener campos filtrados por IA (DESCOMENTADO)
                        campos_seleccionados_tabla = obtener_campos_por_ia(prompt_usuario, tabla, campos_de_tabla)
                        if campos_seleccionados_tabla: # Solo añadir si la IA devolvió campos
                            tablas_y_campos_modulo[tabla] = campos_seleccionados_tabla
                        else:
                             print(f"Advertencia: La IA no seleccionó campos para la tabla '{tabla}' del módulo '{modulo}'.")
                    else:
                        print(f"Advertencia: No se encontraron campos definidos para la tabla '{tabla}' del módulo '{modulo}'.")

                # Añadir las tablas y campos de este módulo al resultado final si no está vacío
                if tablas_y_campos_modulo:
                    resultado_anidado[modulo] = tablas_y_campos_modulo
                else:
                    print(f"Advertencia: No se seleccionaron tablas/campos válidos para el módulo '{modulo}' después del filtrado.")
            else:
                 print(f"Advertencia: La IA no seleccionó tablas para el módulo '{modulo}'.")
        else:
            print(f"Advertencia: No se encontraron tablas definidas para el módulo '{modulo}'.")


    # --- Salida Final ---
    print("\n===================================")
    print("  CONTEXTO BD IDENTIFICADO (ANIDADO)")
    print("===================================")
    print(f"\nPrompt Original: {prompt_usuario}")
    print("\nEstructura Módulo -> Tabla -> Campos:")
    if resultado_anidado:
        print(json.dumps(resultado_anidado, indent=2))
    else:
        print("(No se identificó ninguna estructura relevante)")
    print("===================================")

    # Devolver la estructura anidada
    return resultado_anidado

if __name__ == "__main__":
    # Esta parte solo se ejecuta si el script se corre directamente
    parser = argparse.ArgumentParser(description="Obtener módulos, tablas y campos relevantes usando la IA configurada (ejecución directa). Devuelve estructura anidada.")
    parser.add_argument("prompt", help="La solicitud del usuario.")
    # Ya no necesitamos el argumento --modelo
    parser.add_argument("--desc-modulos", default="descripciones_modulos.json", help="Ruta al JSON con descripciones de módulos.")
    args = parser.parse_args()

    # Llamar a la función principal con los argumentos parseados
    resultados = main(
        prompt_usuario=args.prompt,
        archivo_desc_modulos=args.desc_modulos
    )

    # Imprimir los resultados si se ejecuta directamente (ya se imprimen dentro de main)
    # if resultados:
    #     print("\n--- Resultados de Ejecución Directa (Anidado) ---")
    #     print(json.dumps(resultados, indent=2))
    # elif resultados == {}: # Caso de no encontrar módulos/tablas/campos
    #      print("\n--- Resultados de Ejecución Directa (Anidado) ---")
    #      print("{}")
    # else: # Caso de error inicial (e.g., no cargar módulos)
    #      print("\n--- Ejecución Directa Finalizada con Errores ---")
