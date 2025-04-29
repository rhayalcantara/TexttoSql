import pygame
import random

# Inicialización de Pygame
pygame.init()

# Definiciones de colores
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)
VERDE = (0, 255, 0)
ROJO = (255, 0, 0)
AZUL = (0, 0, 255)
AMARILLO = (255, 255, 0)
GRIS = (128, 128, 128)

# Definiciones de tamaño de la pantalla
ANCHO = 800
ALTO = 600
TAMANO_VENTANA = (ANCHO, ALTO)

# Definiciones de tamaño de la serpiente y la comida
TAMANO_SERPIENTE = 20
TAMANO_COMIDA = 20

# Velocidad de la serpiente
VELOCIDAD = 15  # Aumenta para más rápido, disminuye para más lento

# Fuente para el texto
FUENTE = pygame.font.Font(None, 36)

# Clase para la serpiente
class Serpiente(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.direccion = 0  # 0: derecha, 1: arriba, 2: izquierda, 2: abajo
        self.imagen = pygame.Surface([TAMANO_SERPIENTE, TAMANO_SERPIENTE])
        self.imagen.fill(VERDE)
        self.rect = self.imagen.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.cuerpo = [(x, y)]  # Lista de coordenadas del cuerpo de la serpiente
        self.crecimiento = 0  # Cantidad de crecimiento de la serpiente

    def mover(self):
        nuevo_x = self.rect.x
        nuevo_y = self.rect.y

        if self.direccion == 0:  # Derecha
            nuevo_x += TAMANO_SERPIENTE
        elif self.direccion == 1:  # Arriba
            nuevo_y -= TAMANO_SERPIENTE
        elif self.direccion == 2:  # Izquierda
            nuevo_x -= TAMANO_SERPIENTE
        elif self.direccion == 3:  # Abajo
            nuevo_y += TAMANO_SERPIENTE

        self.rect.x = nuevo_x
        self.rect.y = nuevo_y

        # Actualizar el cuerpo de la serpiente
        self.cuerpo.insert(0, (self.rect.x, self.rect.y))
        if len(self.cuerpo) > self.crecimiento + 1:
            self.cuerpo.pop()

    def cambiar_direccion(self, direccion):
        if direccion == 0 and self.direccion != 2:  # Derecha
            self.direccion = 0
        elif direccion == 1 and self.direccion != 3:  # Arriba
            self.direccion = 1
        elif direccion == 2 and self.direccion != 0:  # Izquierda
            self.direccion = 2
        elif direccion == 3 and self.direccion != 1:  # Abajo
            self.direccion = 3

    def crecer(self):
        self.crecimiento += 1

# Clase para la comida
class Comida(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.imagen = pygame.Surface([TAMANO_COMIDA, TAMANO_COMIDA])
        self.imagen.fill(ROJO)
        self.rect = self.imagen.get_rect()
        self.generar_posicion()

    def generar_posicion(self):
        self.rect.x = random.randrange(0, ANCHO - TAMANO_COMIDA, TAMANO_SERPIENTE)
        self.rect.y = random.randrange(0, ALTO - TAMANO_COMIDA, TAMANO_SERPIENTE)

# Clase para el enemigo
class Enemigo(pygame.sprite.Sprite):
    def __init__(self, velocidad):
        super().__init__()
        self.imagen = pygame.Surface([TAMANO_SERPIENTE, TAMANO_SERPIENTE])
        self.imagen.fill(AZUL)
        self.rect = self.imagen.get_rect()
        self.velocidad = velocidad
        self.direccion = random.choice([0, 1, 2, 3])  # Dirección aleatoria inicial
        self.generar_posicion()

    def mover(self):
        nuevo_x = self.rect.x
        nuevo_y = self.rect.y

        if self.direccion == 0:  # Derecha
            nuevo_x += self.velocidad
        elif self.direccion == 1:  # Arriba
            nuevo_y -= self.velocidad
        elif self.direccion == 2:  # Izquierda
            nuevo_x -= self.velocidad
        elif self.direccion == 3:  # Abajo
            nuevo_y += self.velocidad

        self.rect.x = nuevo_x
        self.rect.y = nuevo_y

        # Rebotar en los bordes
        if self.rect.left < 0 or self.rect.right > ANCHO:
            self.direccion = 1 if self.direccion == 3 else 3
        if self.rect.top < 0 or self.rect.bottom > ALTO:
            self.direccion = 0 if self.direccion == 1 else 2

    def cambiar_direccion(self):
        self.direccion = random.choice([0, 1, 2, 3])

# Crear la ventana
pantalla = pygame.display.set_mode(TAMANO_VENTANA)
pygame.display.set_caption("Serpiente Moderna")

# Crear los sprites
serpiente = Serpiente(ANCHO // 2, ALTO // 2)
comida = Comida()
enemigo = Enemigo(2)  # Velocidad inicial del enemigo

# Crear grupos de sprites
todos_los_sprites = pygame.sprite.Group()
todos_los_sprites.add(serpiente)
todos_los_sprites.add(comida)
todos_los_sprites.add(enemigo)

# Variables del juego
puntaje = 0
nivel = 1
juego_terminado = False
reloj = pygame.time.Clock()

# Bucle principal del juego
while not juego_terminado:
    # Manejo de eventos
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            juego_terminado = True
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_UP:
                serpiente.cambiar_direccion(1)
            if evento.key == pygame.K_DOWN:
                serpiente.cambiar_direccion(3)
            if evento.key == pygame.K_LEFT:
                serpiente.cambiar_direccion(2)
            if evento.key == pygame.K_RIGHT:
                serpiente.cambiar_direccion(0)

    # Actualizar el juego
    if not juego_terminado:
        serpiente.mover()
        enemigo.mover()

        # Colisión con la comida
        if serpiente.rect.colliderect(comida.rect):
            serpiente.crecer()
            comida.generar_posicion()
            puntaje += 10
            nivel = min(puntaje // 20, 10)  # Aumentar el nivel gradualmente
            VELOCIDAD = 15 + nivel * 2  # Aumentar la velocidad gradualmente

        # Colisión con el enemigo
        if serpiente.rect.colliderect(enemigo.rect):
            juego_terminado = True

        # Colisión con el cuerpo de la serpiente
        for segmento in serpiente.cuerpo[:-1]:
            if serpiente.rect.colliderect(segmento):
                juego_terminado = True

    # Dibujar el juego
    pantalla.fill(BLANCO)
    todos_los_sprites.draw(pantalla)

    # Dibujar el puntaje y el nivel
    texto_puntaje = FUENTE.render(f"Puntaje: {puntaje}", True, NEGRO)
    pantalla.blit(texto_puntaje, (10, 10))
    texto_nivel = FUENE.render(f"Nivel: {nivel}", True, NEGRO)
    pantalla.blit(texto_nivel, (10, 30))

    # Actualizar la pantalla
    pygame.display.flip()

    # Control de la velocidad del juego
    reloj.tick(VELOCIDAD)

# Mensaje de fin de juego
pantalla.fill(BLANCO)
texto_fin = FUENTE.render("¡Juego Terminado! Presiona ESC para salir.", True, NEGRO)
pantalla.blit(texto_fin, (ANCHO // 2 - texto_fin.get_width() // 2, ALTO // 2 - texto_fin.get_height() // 2))
pygame.display.flip()

# Esperar a que el jugador presione ESC
while True:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            quit()
        if evento.type == pygame.KEYDOWN:
            if evento.key == pygame.K_ESCAPE:
                pygame.quit()
                quit()
                break