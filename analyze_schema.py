import os
import json
import requests
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener la URL del servidor Ollama desde las variables de entorno
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate") # Valor por defecto

# Modelo de Gemini 3 a usar
MODEL = "gemini"

def analyze_schema_with_ollama(schema_file, ollama_url, model):
    """
    Analiza el esquema de la base de datos utilizando Ollama y Gemini 3.

    Args:
        schema_file (str): Ruta al archivo JSON que contiene el esquema de la base de datos.
        ollama_url (str): URL del servidor Ollama.
        model (str): Nombre del modelo a usar en Ollama.

    Returns:
        dict: Un diccionario que representa las relaciones entre las tablas.
    """
    try:
        # Cargar el esquema desde el archivo JSON
        with open(schema_file, "r") as f:
            schema = json.load(f)

        # Construir el prompt para Gemini 3
        prompt = f"""
        Analiza el siguiente esquema de base de datos MySQL y determina las relaciones entre las tablas.
        Identifica grupos de tablas que están relacionadas entre sí, explicando la lógica de la relación.
        El esquema es el siguiente:
        {json.dumps(schema, indent=4)}

        Responde en formato JSON, con una clave "relationships" que contiene un diccionario.
        Las claves del diccionario deben ser los nombres de las tablas.
        Los valores deben ser listas de otras tablas relacionadas con la clave, junto con una breve explicación de la relación.
        Si no hay relaciones directas, la lista debe estar vacía.
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

        # Intentar parsear la respuesta como JSON
        try:
            relationships = json.loads(response_text)
            return relationships
        except json.JSONDecodeError:
            print(f"Error al decodificar la respuesta JSON de Ollama: {response_text}")
            return None

    except FileNotFoundError:
        print(f"Error: El archivo {schema_file} no fue encontrado.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con el servidor Ollama: {e}")
        return None
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        return None

if __name__ == "__main__":
    # Analizar el esquema de la base de datos
    relationships = analyze_schema_with_ollama("schema.json", OLLAMA_URL, MODEL)

    if relationships:
        # Guardar las relaciones en un archivo JSON
        with open("relationships.json", "w") as f:
            json.dump(relationships, f, indent=4)
        print("Relaciones de la base de datos guardadas en relationships.json")
    else:
        print("No se pudieron obtener las relaciones de la base de datos.")
