import pygame
import random
import time

# Inicialización de Pygame
pygame.init()

# Dimensiones de la ventana
ancho_ventana = 600
alto_ventana = 400
tamano_celda = 10

# Colores
blanco = (255, 255, 255)
negro = (0, 0, 0)

# Creación de la ventana
ventana = pygame.display.set_mode((ancho_ventana, alto_ventana))
pygame.display.set_caption("Juego de la Vida con Pygame")

# Parámetros del juego
ancho = ancho_ventana // tamano_celda
alto = alto_ventana // tamano_celda
generaciones = 100
delay = 0.1

def crear_tablero(ancho, alto):
    """Crea un tablero inicial aleatorio."""
    tablero = []
    for _ in range(alto):
        fila = [random.choice([0, 1]) for _ in range(ancho)]
        tablero.append(fila)
    return tablero

def dibujar_tablero(tablero):
    """Dibuja el tablero en la ventana."""
    for y in range(alto):
        for x in range(ancho):
            if tablero[y][x] == 1:
                pygame.draw.rect(ventana, negro, (x * tamano_celda, y * tamano_celda, tamano_celda, tamano_celda))
            else:
                pygame.draw.rect(ventana, blanco, (x * tamano_celda, y * tamano_celda, tamano_celda, tamano_celda))
    pygame.display.flip()

def contar_vecinos(tablero, x, y):
    """Cuenta el número de vecinos vivos de una celda."""
    vecinos = 0
    for i in range(max(0, x - 1), min(ancho, x + 2)):
        for j in range(max(0, y - 1), min(alto, y + 2)):
            if (i, j) != (x, y):
                vecinos += tablero[j][i]
    return vecinos

def siguiente_generacion(tablero):
    """Calcula la siguiente generación del tablero."""
    nueva_generacion = [[0 for _ in range(ancho)] for _ in range(alto)]
    for y in range(alto):
        for x in range(ancho):
            vecinos = contar_vecinos(tablero, x, y)
            if tablero[y][x] == 1:
                if vecinos < 2 or vecinos > 3:
                    nueva_generacion[y][x] = 0
                else:
                    nueva_generacion[y][x] = 1
            else:
                if vecinos == 3:
                    nueva_generacion[y][x] = 1
                else:
                    nueva_generacion[y][x] = 0
    return nueva_generacion

# Creación del tablero inicial
tablero = crear_tablero(ancho, alto)

# Bucle principal del juego
ejecutando = True
reloj = pygame.time.Clock()

while ejecutando:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            ejecutando = False

    # Dibujar el tablero
    dibujar_tablero(tablero)

    # Calcular la siguiente generación
    tablero = siguiente_generacion(tablero)

    # Control de la velocidad del juego
    reloj.tick(10)  # Ajusta este valor para cambiar la velocidad

# Finalización de Pygame
pygame.quit()