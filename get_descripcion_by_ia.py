import os
import csv
import json
import glob
# Importar la función genérica y la configuración desde sus archivos correctos
from ia_utils import llamar_api_ia
import ai_config

def obtener_descripcion_ia(nombre_modulo, nombres_tablas):
    """
    Obtiene la descripción del módulo usando la IA configurada en ai_config.py.

    Args:
        nombre_modulo (str): El nombre del módulo (prefijo).
        nombres_tablas (list): Una lista de nombres de tablas del módulo.

    Returns:
        str: La descripción generada por la IA o un mensaje de error.
    """
    # Limitar la cantidad de nombres de tablas en el prompt
    max_tablas_prompt = 50
    tablas_para_prompt = nombres_tablas[:max_tablas_prompt]
    if len(nombres_tablas) > max_tablas_prompt:
        print(f"  Advertencia: Se usarán solo las primeras {max_tablas_prompt} tablas de {len(nombres_tablas)} en el prompt para el módulo '{nombre_modulo}'.")

    # Prompt del sistema (define el rol)
    system_prompt = "Eres un asistente experto en análisis de esquemas de bases de datos."
    # Prompt del usuario (define la tarea específica)
    user_prompt = f"""Describe brevemente el propósito principal o la función del módulo de base de datos llamado '{nombre_modulo}'.
Este módulo contiene las siguientes tablas (lista parcial o completa): {', '.join(tablas_para_prompt)}.
Basándote en el nombre del módulo y los nombres de estas tablas, proporciona una descripción concisa en español.
No incluyas saludos ni despedidas en tu respuesta, solo la descripción."""

    # Preparar mensajes para la función genérica
    messages = [{"role": "user", "content": user_prompt}]

    print(f"  Llamando a IA ({ai_config.AI_PROVIDER} / {ai_config.AI_MODEL}) para el módulo '{nombre_modulo}'...")
    # Llamar a la función genérica
    respuesta_json = llamar_api_ia(messages=messages, system_prompt=system_prompt)

    if not respuesta_json:
        return f"Error al llamar a la API de IA para '{nombre_modulo}'."

    # Extraer la descripción de la respuesta JSON (específico del proveedor)
    descripcion = None
    try:
        if ai_config.AI_PROVIDER in ["OpenAI", "OpenRouter", "Ollama"]:
            if respuesta_json.get("choices") and len(respuesta_json["choices"]) > 0:
                message = respuesta_json["choices"][0].get("message", {})
                descripcion = message.get("content", "").strip()
        elif ai_config.AI_PROVIDER == "Anthropic":
             if respuesta_json.get("content") and len(respuesta_json["content"]) > 0:
                 for block in respuesta_json["content"]:
                     if block.get("type") == "text":
                         descripcion = block.get("text", "").strip()
                         break
        elif ai_config.AI_PROVIDER == "Google":
             if respuesta_json.get("candidates") and len(respuesta_json["candidates"]) > 0:
                 content = respuesta_json["candidates"][0].get("content", {})
                 if content.get("parts") and len(content["parts"]) > 0:
                     descripcion = content["parts"][0].get("text", "").strip()

        if descripcion:
            print(f"  Descripción recibida de la IA.")
            return descripcion
        else:
            print(f"  Error: No se pudo extraer la descripción de la respuesta de {ai_config.AI_PROVIDER}.")
            print(f"  Respuesta recibida: {json.dumps(respuesta_json, indent=2)}")
            return f"Error al extraer descripción de la IA para '{nombre_modulo}'."

    except Exception as e:
        print(f"  Error inesperado al procesar la respuesta de la IA para '{nombre_modulo}': {e}")
        print(f"  Respuesta JSON cruda: {json.dumps(respuesta_json, indent=2)}")
        return f"Error al procesar respuesta de IA para '{nombre_modulo}': {e}"


def procesar_archivos_schema(directorio_actual):
    """
    Encuentra, procesa archivos *_schema.csv y genera descripciones.
    """
    resultados = []
    # Usamos glob para encontrar los archivos que coinciden con el patrón
    patron_archivos = os.path.join(directorio_actual, '*_schema.csv')
    archivos_schema = glob.glob(patron_archivos)

    if not archivos_schema:
        print("No se encontraron archivos *_schema.csv en el directorio.")
        return resultados

    print(f"Archivos encontrados: {len(archivos_schema)}")

    for ruta_archivo in archivos_schema:
        nombre_archivo = os.path.basename(ruta_archivo)
        # Extraemos el prefijo/módulo antes de '_schema.csv'
        if nombre_archivo.endswith('_schema.csv'):
            nombre_modulo = nombre_archivo[:-len('_schema.csv')]
            print(f"\nProcesando módulo: {nombre_modulo}")

            try:
                nombres_tablas = []
                num_tablas = 0
                with open(ruta_archivo, mode='r', encoding='utf-8', errors='ignore') as csvfile:
                    # Intentamos detectar el delimitador
                    try:
                        dialect = csv.Sniffer().sniff(csvfile.read(1024), delimiters=',;')
                        csvfile.seek(0)
                        reader = csv.reader(csvfile, dialect)
                    except csv.Error:
                        # Si falla la detección, volvemos a lo básico (coma)
                        csvfile.seek(0)
                        reader = csv.reader(csvfile, delimiter=',')
                        print(f"  Advertencia: No se pudo detectar el delimitador para {nombre_archivo}, usando ',' por defecto.")

                    # Omitimos la cabecera si existe
                    try:
                        header = next(reader)
                        print(f"  Cabecera detectada: {header}")
                    except StopIteration:
                        print(f"  Advertencia: Archivo {nombre_archivo} está vacío o no tiene cabecera.")
                        continue # Saltar al siguiente archivo si está vacío

                    # Contamos filas y extraemos nombres de tablas (asumiendo que están en la primera columna)
                    for i, row in enumerate(reader):
                        if row: # Asegurarse de que la fila no esté vacía
                            num_tablas += 1
                            # Intentamos obtener el nombre de la tabla de la primera columna
                            if len(row) > 0:
                                nombres_tablas.append(row[0].strip())
                            else:
                                print(f"  Advertencia: Fila {i+1} en {nombre_archivo} no tiene columnas.")
                        else:
                             print(f"  Advertencia: Fila {i+1} en {nombre_archivo} está vacía.")


                print(f"  Número de tablas encontradas: {num_tablas}")
                # print(f"  Nombres de tablas: {nombres_tablas[:5]}...") # Muestra solo las primeras 5

                if num_tablas > 0:
                    # Llamamos a la función refactorizada (ya no necesita el modelo como argumento)
                    descripcion = obtener_descripcion_ia(nombre_modulo, nombres_tablas)

                    resultados.append({
                        "modulo": nombre_modulo,
                        "cantidad_tablas": num_tablas,
                        "descripcion_ia": descripcion
                    })
                else:
                     print(f"  El archivo {nombre_archivo} no contiene tablas (después de la cabecera).")


            except FileNotFoundError:
                print(f"Error: No se pudo encontrar el archivo {ruta_archivo}")
            except Exception as e:
                print(f"Error procesando el archivo {ruta_archivo}: {e}")

    return resultados

def guardar_resultados(resultados, archivo_salida):
    """
    Guarda los resultados en un archivo JSON.
    """
    try:
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, indent=4, ensure_ascii=False)
        print(f"\nResultados guardados exitosamente en {archivo_salida}")
    except Exception as e:
        print(f"Error al guardar los resultados en {archivo_salida}: {e}")

if __name__ == "__main__":
    directorio = '.' # Directorio actual
    archivo_json_salida = 'descripciones_modulos.json'

    print("Iniciando proceso para generar descripciones de módulos...")
    datos_modulos = procesar_archivos_schema(directorio)

    if datos_modulos:
        guardar_resultados(datos_modulos, archivo_json_salida)
    else:
        print("No se generaron datos para guardar.")

    print("Proceso completado.")
