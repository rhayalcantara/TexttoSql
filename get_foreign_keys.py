# get_foreign_keys.py
import os
import json
import mysql.connector
from dotenv import load_dotenv
import csv

# Carg load environment variables from .env
load_dotenv()

# Get database credentials from environment variables
DB_HOST = os.getenv("MYSQL_HOST")
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DATABASE")


def get_foreign_keys(host, user, password, database):
    """
    Connects to a MySQL database and retrieves foreign key information.

    Args:
        host (str): The database host.
        user (str): The database user.
        password (str): The database password.
        database (str): The database name.

    Returns:
        list: A list of tuples, where each tuple represents a foreign key relationship.
              Each tuple contains (table, column, referenced_table, referenced_column).
              Returns None if the connection fails.
    """
    cnx = None
    try:
        cnx = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=3470
        )
        cursor = cnx.cursor()
        cursor.execute(
            """
            SELECT
                TABLE_NAME,
                COLUMN_NAME,
                CONSTRAINT_NAME,
               REFERENCED_TABLE_NAME,
               REFERENCED_COLUMN_NAME
           FROM
               information_schema.KEY_COLUMN_USAGE
           WHERE
               REFERENCED_TABLE_NAME IS NOT NULL
            """
        )
        foreign_keys = cursor.fetchall()
        return foreign_keys
    except mysql.connector.Error as err:
        print(f"Error connecting to the database: {err}")
        return None
    finally:
        if cnx and cnx.is_connected():
            cursor.close()
            cnx.close()
            print("Connection closed.")


def save_foreign_keys_to_csv(foreign_keys, db_name):
    """
    Saves the foreign key information to a CSV file.

    Args:
        foreign_keys (list): The list of foreign key relationships.
        db_name (str): The name of the database (used for the CSV file name).
    """
    filename = f"{db_name}_foreign_keys.csv"
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            # Write header row
            csv_writer.writerow(['Table', 'Column', 'Referenced Table', 'Referenced Column', 'Constraint Name'])
            # Write data rows
            for table, column, constraint_name, referenced_table, referenced_column in foreign_keys:
                csv_writer.writerow([
                    table,
                    column,
                    referenced_table,
                    referenced_column,
                    constraint_name
                ])

        print(f"Foreign keys saved to {filename}")
    except Exception as e:
        print(f"Error saving foreign keys to CSV: {e}")


if __name__ == "__main__":
    foreign_keys = get_foreign_keys(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
    if foreign_keys:
        save_foreign_keys_to_csv(foreign_keys, DB_NAME)
        # Optional: Print the foreign keys to the console
        # for table, column, referenced_table, referenced_column in foreign_keys:
        #     print(f"Table: {table}, Column: {column}, Ref Table: {referenced_table}, Ref Column: {referenced_column}")
        print("Foreign keys retrieved successfully.")
    else:
        print("Failed to retrieve foreign keys.")