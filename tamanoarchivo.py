import os
import hashlib

def obtener_informacion_archivos(directorio):
    """
    Recorre un directorio y devuelve un diccionario con información de cada archivo.

    Args:
        directorio: La ruta al directorio que se va a escanear.

    Returns:
        Un diccionario donde las claves son las rutas de los archivos
        y los valores son sus tamaños en bytes.
    """

    archivos = {}
    for ruta, subdirectorios, nombres_archivos in os.walk(directorio):
        for nombre_archivo in nombres_archivos:
            ruta_completa = os.path.join(ruta, nombre_archivo)
            try:
                tamano = os.path.getsize(ruta_completa)
                if tamano > 0:  # Excluye archivos con tamaño cero
                    archivos[ruta_completa] = tamano
            except OSError:
                # Maneja errores de permisos u otros problemas al acceder a archivos
                pass
    return archivos

def buscar_duplicados(directorio):
    """
    Busca archivos duplicados en un directorio basado en su hash MD5.

    Args:
        directorio: La ruta al directorio que se va a escanear.

    Returns:
        Un diccionario donde las claves son hashes MD5 y los valores son listas de rutas de archivo.
    """
    hashes = {}
    for ruta in obtener_informacion_archivos(directorio):
        try:
            with open(ruta, 'rb') as f:
                contenido = f.read()
                hash_md5 = hashlib.md5(contenido).hexdigest()
                if hash_md5 in hashes:
                    hashes[hash_md5].append(ruta)
                else:
                    hashes[hash_md5] = [ruta]
        except OSError:
            # Maneja errores de permisos u otros problemas al acceder a archivos
            pass
    return {hash_val: files for hash_val, files in hashes.items() if len(files) > 1}


def main():
    directorio = input("Ingresa el directorio a escanear: ")
    archivo_salida = input("Ingresa el nombre del archivo de salida (.txt): ")

    archivos = obtener_informacion_archivos(directorio)

    # Ordena los archivos por tamaño de forma descendente
    archivos_ordenados = sorted(archivos.items(), key=lambda item: item[1], reverse=True)

    with open(archivo_salida, "w", encoding="utf-8") as f:
        f.write("Archivos ordenados por tamaño (descendente):\n")
        for ruta, tamano in archivos_ordenados:
            f.write(f"Ruta: {ruta}, Tamaño: {tamano} bytes\n")
        f.write("\n")

        duplicados = buscar_duplicados(directorio)
        if duplicados:
            f.write("Archivos duplicados:\n")
            for hash_val, archivos in duplicados.items():
                f.write(f"Hash MD5: {hash_val}\n")
                for archivo in archivos:
                    f.write(f"  - {archivo}\n")
            f.write("\n")
        else:
            f.write("No se encontraron archivos duplicados.\n")

    print(f"Resultados escritos en {archivo_salida}")


if __name__ == "__main__":
    main()