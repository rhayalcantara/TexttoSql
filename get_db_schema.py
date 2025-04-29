import os
import json
import mysql.connector
from dotenv import load_dotenv
import csv
# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener las credenciales de la base de datos desde las variables de entorno
DB_HOST = os.getenv("MYSQL_HOST")
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DATABASE")

def get_db_schema(host, user, password, database):
    """
    Connects to a MySQL database and retrieves the table schema.

    Args:
        host (str): The database host.
        user (str): The database user.
        password (str): The database password.
        database (str): The database name.

    Returns:
        list: A list of tuples, where each tuple represents a table and its columns.
              Returns None if the connection fails.
    """
    cnx = None  # Initialize cnx to None
    try:
        cnx = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=3470
        )
        cursor = cnx.cursor()
        print("Fetching table list...")
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"Found {len(tables)} tables.")
        schema = []
        for i, table in enumerate(tables):
            print(f"Processing table {i+1}/{len(tables)}: {table}")
            cursor.execute(f"SHOW COLUMNS FROM `{table}`")
            columns = cursor.fetchall()
            schema.append((table, columns))
            print(f"Finished processing table: {table}")
        print("Finished fetching all table schemas.")
        return schema
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None  # Return None if connection fails
    finally:
        if cnx and cnx.is_connected():
            cursor.close()
            cnx.close()
            print("Connection closed.")

def save_schema_to_csv(schema, filename):
    """
    Saves the database schema to a specified CSV file.

    Args:
        schema (list): The database schema to save.
        filename (str): The name of the CSV file to save the schema to.
    """
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)

            # Write header row
            csv_writer.writerow(['Table', 'Column Name', 'Data Type', 'Nullable', 'Key', 'Default', 'Extra'])

            # Write data rows
            for table, columns in schema:
                for column in columns:
                    csv_writer.writerow([
                        table,
                        column[0],
                        column[1],
                        column[2],
                        column[3],
                        column[4],
                        column[5]
                    ])

        print(f"Schema saved to {filename}")
    except Exception as e:
        print(f"Error saving schema to CSV: {e}")


if __name__ == "__main__":
    schema = get_db_schema(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    if schema:
        print("Grouping schemas by prefix...")
        schemas_by_prefix = {}
        # Group tables by prefix
        for table, columns in schema:
            table_name = table
            print(f"Processing table: {table_name}")
            prefix = '_noprefix_' # Default prefix for tables without the pattern
            if table_name.startswith("FBS_") and '.' in table_name:
                dot_index = table_name.find('.')
                prefix = table_name[:dot_index] # Extract prefix up to (but not including) the dot

            if prefix not in schemas_by_prefix:
                schemas_by_prefix[prefix] = []
            schemas_by_prefix[prefix].append((table, columns))

        # Save each group to a separate file
        for prefix, grouped_schema in schemas_by_prefix.items():
            if prefix == '_noprefix_':
                filename = f"{DB_NAME}_noprefix_schema.csv"
            else:
                # Use prefix (without dot) as part of the filename
                filename = f"{prefix}_schema.csv" 
            print(f"Saving schema to {filename}...")
            save_schema_to_csv(grouped_schema, filename)

        print("Schema retrieved and saved successfully by prefix.")
    else:
        print("Failed to retrieve database schema.")
