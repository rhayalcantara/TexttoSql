import os
import json
import csv
import argparse
# requests ya no es necesario aquí, se usa en ia_utils
# Importar la configuración centralizada
import ai_config
# Importar la función genérica de llamada a IA desde el nuevo archivo
from ia_utils import llamar_api_ia
# Importar la función refactorizada del otro script
from get_modulo_tabla_campos import main as obtener_contexto_bd
# Importar para conexión a BD y variables de entorno
import mysql.connector
from dotenv import load_dotenv


# Ya no se necesita OPENROUTER_API_BASE
# La función llamar_api_ia fue movida a ia_utils.py


# --------------------------------------------------------------------------
# Función Específica para Generar Consultas SQL (Usa la función genérica importada)
# --------------------------------------------------------------------------
def generar_consulta_con_ia(prompt_usuario, contexto_bd):
    """
    Prepara el prompt específico para SQL y llama a la función genérica de IA
    para generar la consulta. Extrae la consulta de la respuesta.
    """
    # --- Cargar Reglas Específicas ---
    reglas_contenido = ""
    try:
        with open("ReglasGeneracionConsulta.md", 'r', encoding='utf-8') as f_reglas:
            reglas_contenido = f_reglas.read()
        print("Reglas específicas cargadas desde ReglasGeneracionConsulta.md")
    except FileNotFoundError:
        print("Advertencia: No se encontró el archivo ReglasGeneracionConsulta.md. Se generará la consulta sin reglas específicas.")
    except Exception as e:
        print(f"Error al leer ReglasGeneracionConsulta.md: {e}. Se generará la consulta sin reglas específicas.")

    # --- Cargar Relaciones desde CSV ---
    relaciones_contenido = ""
    try:
        # Usar 'realaciones.csv' basado en la lista de archivos proporcionada
        with open("realaciones.csv", 'r', encoding='utf-8') as f_relaciones:
            relaciones_contenido = f_relaciones.read()
        print("Relaciones cargadas desde realaciones.csv")
    except FileNotFoundError:
        print("Advertencia: No se encontró el archivo realaciones.csv. Se generará la consulta sin información de relaciones.")
    except Exception as e:
        print(f"Error al leer realaciones.csv: {e}. Se generará la consulta sin información de relaciones.")

    # 1. Construir el prompt específico para SQL
    schema_context_str = f"""
Módulos: {json.dumps(contexto_bd.get('modulos', []))}
Tablas: {json.dumps(contexto_bd.get('tablas', []))}
Campos: {json.dumps(contexto_bd.get('campos', []))}
Tablas por Módulo: {json.dumps(contexto_bd.get('tablas_por_modulo', {}))}
Campos por Tabla: {json.dumps(contexto_bd.get('campos_por_tabla', {}))}
"""
    # Insertar las reglas en el prompt si se cargaron
    prompt_con_reglas = f"""
Esquema de la Base de Datos:
{schema_context_str}

---
Reglas Específicas de la Institución (¡IMPORTANTE SEGUIR ESTAS REGLAS!):
{reglas_contenido if reglas_contenido else "No se proporcionaron reglas específicas."}
---
Información Adicional sobre Relaciones entre Tablas (desde realaciones.csv):
{relaciones_contenido if relaciones_contenido else "No se proporcionó información adicional de relaciones."}
---

Consulta del Usuario:
{prompt_usuario}

Consulta SQL:
"""

    try:
        # Usamos la plantilla para formatear el contenido del mensaje de usuario
        # Modificamos la plantilla para incluir las reglas
        # Nota: Asumimos que PROMPT_TEMPLATE ahora solo contiene el rol y la estructura general,
        # y que el contenido principal se construye aquí.
        # Si PROMPT_TEMPLATE aún espera {schema} y {query}, necesitamos ajustar eso.
        # Por simplicidad, construiremos el prompt completo aquí.

        # El prompt completo ya está construido arriba como prompt_con_reglas
        prompt_para_ia = prompt_con_reglas # Usamos el prompt que incluye las reglas

    except KeyError as e:
        # Este error es menos probable ahora que construimos el prompt aquí,
        # pero lo dejamos por si PROMPT_TEMPLATE se usa de otra forma.
        print(f"Error: Problema al formatear el prompt (posiblemente en PROMPT_TEMPLATE si aún se usa): {e}")
        return None

    # 2. Preparar mensajes para la función genérica
    # El system prompt define el rol general
    system_prompt_sql = "Eres un experto generador de consultas SQL para MySQL Aurora AWS."
    # El user prompt ahora contiene el esquema, las reglas y la consulta del usuario
    messages_sql = [{"role": "user", "content": prompt_para_ia}]

    # 3. Llamar a la función genérica de IA
    respuesta_json = llamar_api_ia(messages=messages_sql, system_prompt=system_prompt_sql)

    if not respuesta_json:
        return None # El error ya se imprimió en llamar_api_ia

    # 4. Extraer la consulta SQL de la respuesta JSON (específico del proveedor)
    consulta_sql = None
    try:
        if ai_config.AI_PROVIDER in ["OpenAI", "OpenRouter", "Ollama"]:
            if respuesta_json.get("choices") and len(respuesta_json["choices"]) > 0:
                message = respuesta_json["choices"][0].get("message", {})
                consulta_sql = message.get("content", "").strip()
        elif ai_config.AI_PROVIDER == "Anthropic":
             if respuesta_json.get("content") and len(respuesta_json["content"]) > 0:
                 for block in respuesta_json["content"]:
                     if block.get("type") == "text":
                         consulta_sql = block.get("text", "").strip()
                         break
        elif ai_config.AI_PROVIDER == "Google":
             if respuesta_json.get("candidates") and len(respuesta_json["candidates"]) > 0:
                 content = respuesta_json["candidates"][0].get("content", {})
                 if content.get("parts") and len(content["parts"]) > 0:
                     consulta_sql = content["parts"][0].get("text", "").strip()

        if consulta_sql:
            # Limpiar posible markdown
            if consulta_sql.startswith("```sql"):
                consulta_sql = consulta_sql[6:]
            if consulta_sql.endswith("```"):
                consulta_sql = consulta_sql[:-3]
            consulta_sql = consulta_sql.strip()
            print(f"Consulta SQL generada:\n{consulta_sql}")
            return consulta_sql
        else:
            print(f"Error: No se pudo extraer la consulta SQL de la respuesta de {ai_config.AI_PROVIDER}.")
            print(f"Respuesta recibida: {json.dumps(respuesta_json, indent=2)}")
            return None
    except Exception as e:
        print(f"Error inesperado al procesar la respuesta de la IA: {e}")
        print(f"Respuesta recibida: {json.dumps(respuesta_json, indent=2)}")
        return None


def ejecutar_consulta_sql(consulta_sql):
    """
    Ejecuta la consulta SQL en la base de datos MySQL Aurora configurada en .env.
    Devuelve los resultados como una lista de diccionarios.
    """
    print("\n--- Ejecutando Consulta SQL ---")
    print(f"Consulta a ejecutar:\n{consulta_sql}")

    # Cargar variables de entorno desde .env
    load_dotenv()

    resultados = []
    conn = None
    cursor = None

    try:
        # Leer credenciales desde variables de entorno
        db_host = os.getenv("MYSQL_HOST")
        db_user = os.getenv("MYSQL_USER")
        db_password = os.getenv("MYSQL_PASSWORD")
        db_name = os.getenv("MYSQL_DATABASE")
        db_port = os.getenv("MYSQL_PORT", 3306) # Usar 3306 si MYSQL_PORT no está definida

        if not all([db_host, db_user, db_password, db_name]):
            print("Error: Faltan variables de entorno para la conexión a la base de datos (MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE).")
            return None

        # Convertir puerto a entero, manejando posible error si no es numérico
        try:
            # db_port es leído desde os.getenv arriba
            db_port_int = int(db_port)
        except ValueError:
            print(f"Error: El valor de MYSQL_PORT ('{db_port}') no es un número de puerto válido.")
            return None

        # Establecer conexión
        print(f"Conectando a {db_host}:{db_port_int} base de datos {db_name}...") # Usar db_port_int
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            port=db_port_int # Usar el puerto convertido a entero
        )
        print("Conexión exitosa.")

        # Crear cursor que devuelve diccionarios
        cursor = conn.cursor(dictionary=True)

        # Ejecutar la consulta
        cursor.execute(consulta_sql)

        # Obtener resultados
        resultados = cursor.fetchall()
        print(f"Consulta ejecutada. Se obtuvieron {len(resultados)} filas.")
        # print(f"Primeras filas (máx 5): {resultados[:5]}") # Descomentar para depurar

        return resultados

    except mysql.connector.Error as err:
        print(f"Error de MySQL al ejecutar la consulta: {err}")
        # Podríamos querer devolver None o una lista vacía dependiendo del manejo deseado
        return None
    except Exception as e:
        print(f"Error inesperado al ejecutar la consulta SQL: {e}")
        return None
    finally:
        # Asegurarse de cerrar cursor y conexión
        if cursor:
            cursor.close()
            # print("Cursor cerrado.")
        if conn and conn.is_connected():
            conn.close()
            print("Conexión a base de datos cerrada.")


def guardar_resultados_csv(resultados, nombre_archivo="resultados_consulta.csv"):
    """
    Guarda los resultados de la consulta en un archivo CSV.
    """
    if not resultados or len(resultados) == 0:
        print("No hay resultados para guardar.")
        return None

    # Asegurarse de que todos los diccionarios tengan las mismas claves (importante para CSV)
    # Tomar las claves del primer diccionario como cabeceras
    cabeceras = list(resultados[0].keys())

    print(f"\n--- Guardando resultados en {nombre_archivo} ---")
    try:
        with open(nombre_archivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=cabeceras)
            writer.writeheader()
            writer.writerows(resultados)
        print(f"Resultados guardados exitosamente en {nombre_archivo}")
        return nombre_archivo
    except Exception as e:
        print(f"Error al guardar el archivo CSV: {e}")
        return None

def flujo_principal(prompt_usuario):
    """
    Orquesta todo el proceso: obtener contexto, generar SQL, ejecutar, guardar CSV.
    """
    print("--- Iniciando Flujo ---")
    print(f"Prompt del usuario: {prompt_usuario}")

    # 1. Obtener contexto de la BD usando el script refactorizado
    # Usamos el modelo por defecto de ese script (gemma3:12b local)
    contexto_bd = obtener_contexto_bd(prompt_usuario=prompt_usuario)
    if not contexto_bd:
        print("Error: No se pudo obtener el contexto de la base de datos.")
        return

    # 2. Generar la consulta SQL usando la IA (Gemini vía OpenRouter)
    consulta_sql = generar_consulta_con_ia(prompt_usuario, contexto_bd)
    if not consulta_sql:
        print("Error: No se pudo generar la consulta SQL.")
        return

    # 3. Ejecutar la consulta SQL (Usando el placeholder)
    resultados_consulta = ejecutar_consulta_sql(consulta_sql)
    if resultados_consulta is None: # Puede ser None si la ejecución falla
         print("Error: La ejecución de la consulta (simulada) falló o no devolvió resultados.")
         return

    # 4. Guardar los resultados en un archivo CSV
    nombre_archivo_csv = f"resultado_{prompt_usuario[:20].replace(' ', '_')}.csv" # Nombre de archivo dinámico
    ruta_csv = guardar_resultados_csv(resultados_consulta, nombre_archivo_csv)

    if ruta_csv:
        print(f"\n--- Flujo Completado ---")
        print(f"La consulta generada se ejecutó (simuladamente) y los resultados se guardaron en: {ruta_csv}")
        return ruta_csv
    else:
        print("\n--- Flujo Incompleto ---")
        print("Hubo un error al guardar los resultados en CSV.")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Genera una consulta SQL con IA, la ejecuta (simulado) y guarda los resultados en CSV.")
    parser.add_argument("prompt", help="La solicitud del usuario para generar la consulta SQL.")
    args = parser.parse_args()

    # Ejecutar el flujo principal
    flujo_principal(args.prompt)
