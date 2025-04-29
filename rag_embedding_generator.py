import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import subprocess # For running Ollama commands

# Load environment variables from .env file
load_dotenv()

# Database connection parameters from .env
PG_HOST = os.getenv("PG_HOST")
PG_DATABASE = os.getenv("PG_DATABASE")
PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")

# Ollama Model Name
OLLAM_MODEL = "gemma3:12b"


# Function to generate embeddings using Ollama
def generate_embedding(text):
   try:
       # Construct the Ollama command
       command = f"olama run --model {OLLAM_MODEL} --prompt '{text}' --instruct"

       # Execute the Ollama command and capture the output
       process = subprocess.run(command, shell=True, capture_output=True, text=True)

       # Check for errors
       if process.returncode != 0:
           print(f"Error running Ollama: {process.stderr}")
           return None

       # Extract the embedding from the Ollama output. This is highly dependent on the Ollama output format.
       # This is a placeholder and needs to be adjusted based on the actual Ollama output.
       # The following assumes the embedding is the entire output. This is unlikely.
       embedding = process.stdout.strip()

       return embedding

   except Exception as e:
       print(f"Error generating embedding for text: {text}. Error: {e}")
       return None


# Function to connect to PostgreSQL
def connect_to_db():
   try:
       conn = psycopg2.connect(
           host=PG_HOST,
           database=PG_DATABASE,
           user=PG_USER,
           password=PG_PASSWORD
       )
       return conn
   except Exception as e:
       print(f"Error connecting to database: {e}")
       return None


# Main script
if __name__ == "__main__":
   # Read foreign key data
   try:
       foreign_keys_df = pd.read_csv("FBS_Aspire_foreign_keys.csv")
   except FileNotFoundError:
       print("Error: FBS_Aspire_foreign_keys.csv not found.")
       exit(1)

   # Read schema data
   try:
       schema_df = pd.read_csv("FBS_Aspire_schema.csv")
   except FileNotFoundError:
       print("Error: FBS_Aspire_schema.csv not found.")
       exit(1)

   # Connect to PostgreSQL
   conn = connect_to_db()
   if conn is None:
       exit(1)

   try:
       cursor = conn.cursor()

       # Iterate through foreign keys and generate embeddings
       for index, row in foreign_keys_df.iterrows():
           # Construct the description string using the column names
           description = f"Table: {row['Table']}, Column: {row['Column']}, Referenced Table: {row['Referenced Table']}, Referenced Column: {row['Referenced Column']}, Constraint Name: {row['Constraint Name']}"
           embedding = generate_embedding(description)

           if embedding:
               try:
                   # Insert embedding into the database
                   insert_query = """
                        INSERT INTO embeddings (description, embedding)
                        VALUES (%s, %s);
                   """
                   cursor.execute(insert_query, (description, embedding))
                   conn.commit()
                   print(f"Inserted embedding for row {index + 1}")
               except Exception as e:
                   print(f"Error inserting embedding for row {index + 1}: {e}")
                   conn.rollback()

       # Iterate through schema and generate embeddings
       for index, row in schema_df.iterrows():
           # Construct the description string using the column names
           description = f"Table: {row['Table']}, Column: {row['Column']}, Referenced Table: {row['Referenced Table']}, Referenced Column: {row['Referenced Column']}, Constraint Name: {row['Constraint Name']}"
           embedding = generate_embedding(description)

           if embedding:
               try:
                   # Insert embedding into the database
                   insert_query = """
                        INSERT INTO embeddings (description, embedding)
                        VALUES (%s, %s);
                   """
                   cursor.execute(insert_query, (description, embedding))
                   conn.commit()
                   print(f"Inserted embedding for schema row {index + 1}")
               except Exception as e:
                   print(f"Error inserting embedding for schema row {index + 1}: {e}")
                   conn.rollback()

   except Exception as e:
       print(f"An error occurred: {e}")
       if conn:
           conn.rollback()

   finally:
       if conn:
           cursor.close()
           conn.close()
           print("Database connection closed.")