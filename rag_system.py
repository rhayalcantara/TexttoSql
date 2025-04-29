import os
import json
import mysql.connector
import requests
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener las credenciales de la base de datos desde las variables de entorno
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Obtener la URL del servidor Ollama desde las variables de entorno
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate") # Valor por defecto

# Modelo de Gemini 3 a usar
MODEL = "gemma3:12b"

def generate_sql_query(question, schema_file, relationships_file, ollama_url, model):
    """
    Genera una consulta SQL basada en una pregunta del usuario, el esquema de la base de datos,
    las relaciones entre las tablas y el modelo de IA.

    Args:
        question (str): Pregunta del usuario.
        schema_file (str): Ruta al archivo JSON que contiene el esquema de la base de datos.
        relationships_file (str): Ruta al archivo JSON que contiene las relaciones entre las tablas.
        ollama_url (str): URL del servidor Ollama.
        model (str): Nombre del modelo a usar en Ollama.

    Returns:
        str: Consulta SQL generada, o None si ocurre un error.
    """
    try:
        # Cargar el esquema y las relaciones desde los archivos JSON
        with open(schema_file, "r") as f:
            schema = json.load(f)
        with open(relationships_file, "r") as f:
            relationships = json.load(f)

        # Construir el prompt para Gemini 3
        prompt = f"""
        Genera una consulta SQL para responder la siguiente pregunta sobre una base de datos MySQL.
        Utiliza el esquema de la base de datos y las relaciones entre las tablas para generar la consulta.
        La pregunta es: {question}

        Esquema de la base de datos:
        {json.dumps(schema, indent=4)}

        Relaciones entre las tablas:
        {json.dumps(relationships, indent=4)}

        La consulta SQL debe ser válida y debe devolver la información solicitada.
        No incluyas comentarios en la consulta SQL.
        """

        # Enviar la solicitud a Ollama
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(ollama_url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes

        # Procesar la respuesta de Ollama
        response_json = response.json()
        # Extraer el texto de la respuesta
        response_text = response_json["response"].strip()

        # Extraer la consulta SQL (asumiendo que la respuesta es la consulta SQL)
        sql_query = response_text.strip()

        return sql_query

    except FileNotFoundError as e:
        print(f"Error: Archivo no encontrado: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con el servidor Ollama: {e}")
        return None
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        return None

def execute_sql_query(sql_query, host, user, password, database):
    """
    Ejecuta una consulta SQL en la base de datos MySQL.

    Args:
        sql_query (str): Consulta SQL a ejecutar.
        host (str): Host de la base de datos.
        user (str): Usuario de la base de datos.
        password (str): Contraseña del usuario.
        database (str): Nombre de la base de datos.

    Returns:
        list: Resultados de la consulta, o None si ocurre un error.
    """
    results = None
    try:
        # Conectarse a la base de datos
        cnx = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = cnx.cursor()

        # Ejecutar la consulta SQL
        cursor.execute(sql_query)
        results = cursor.fetchall()

    except mysql.connector.Error as err:
        print(f"Error al ejecutar la consulta SQL: {err}")
        return None
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()
    return results

def main():
    """
    Función principal del sistema RAG.
    """
    # Recibir la pregunta del usuario
    question = input("Ingrese su pregunta: ")

    # Generar la consulta SQL
    sql_query = generate_sql_query(question, "schema.json", "relationships.json", OLLAMA_URL, MODEL)

    if sql_query:
        print(f"Consulta SQL generada: {sql_query}")

        # Ejecutar la consulta SQL
        results = execute_sql_query(sql_query, DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)

        if results is not None:
            # Mostrar los resultados
            if results:
                print("Resultados:")
                for row in results:
                    print(row)
            else:
                print("No se encontraron resultados.")
        else:
            print("No se pudieron obtener los resultados.")
    else:
        print("No se pudo generar la consulta SQL.")

if __name__ == "__main__":
    main()
