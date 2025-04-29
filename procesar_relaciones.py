# archivo: procesar_relaciones.py
import os
import yaml
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

def cargar_relaciones(nombre_archivo="relaciones.yaml"):
   """Carga las relaciones de las tablas desde un archivo YAML."""
   with open(nombre_archivo, 'r') as f:
       return yaml.safe_load(f)

def main():
   relaciones = cargar_relaciones()

   # Accede a las relaciones para PostgreSQL
   if relaciones and 'postgresql' in relaciones:
       relaciones_pg = relaciones['postgresql']['tablas']
       print("Relaciones de PostgreSQL:")
       for tabla1, tablas_relacionadas in relaciones_pg.items():
           for tabla2, detalles in tablas_relacionadas.items():
               print(f" {tabla1} se relaciona con {tabla2} vía {detalles['campo1']} y {detalles['campo2']}")

   # Accede a las relaciones para MySQL
   if relaciones and 'mysql' in relaciones:
       relaciones_mysql = relaciones['mysql']['tablas']
       print("\nRelaciones de MySQL:")
       for tabla1, tablas_relacionadas in relaciones_mysql.items():
           for tabla2, detalles in tablas_relacionadas.items():
               print(f" {tabla1} se relaciona con {tabla2} vía {detalles['campo1']} y {detalles['campo2']}")

if __name__ == "__main__":
   main()