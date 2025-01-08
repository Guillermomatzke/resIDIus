import pygame
import cv2
import mediapipe as mp
import random

# Inicialización de Pygame
pygame.init()

# Configuración de pantalla
screen_width, screen_height = 1280, 720
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Clasificación de Residuos")

# Cargar imágenes de residuos (deben ser PNG con fondo transparente)
residuos = ['img/botella.png', 'img/lata.png', 'img/papel.png']  # Asegúrate de que las rutas sean correctas
residuos_imgs = [pygame.transform.scale(pygame.image.load(res).convert_alpha(), (80, 80)) for res in residuos]
residuos_pos = [(random.randint(50, screen_width - 100), random.randint(50, 100)) for _ in residuos]

# Cargar imágenes de cestos
cestos_imgs = {
    'plastico': pygame.image.load('img/cesto rojo plastico.png').convert_alpha(),
    'metal': pygame.image.load('img/cesto amarillo latas.png').convert_alpha(),
    'papel': pygame.image.load('img/cesto azul papeles.png').convert_alpha()
}

# Definir posiciones y rectángulos para colisión de cestos (ajustar tamaño para hacerlos más grandes)
cestos_rects = {
    'plastico': pygame.Rect(200, screen_height - 200, 150, 150),
    'metal': pygame.Rect(600, screen_height - 200, 150, 150),
    'papel': pygame.Rect(1000, screen_height - 200, 150, 150)
}

# Configuración de la cámara y Mediapipe
cap = cv2.VideoCapture(0)
mp_hands = mp.solutions.hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Variables de control
residuos_clasificados = [False] * len(residuos)
residuos_en_mano = [False] * len(residuos)
clasificacion_correcta = [False] * len(residuos)
puño_cerrado = False

# Función para mostrar los cestos
def dibujar_cestos():
    screen.blit(pygame.transform.scale(cestos_imgs['plastico'], (150, 150)), (200, screen_height - 200))
    screen.blit(pygame.transform.scale(cestos_imgs['metal'], (150, 150)), (600, screen_height - 200))
    screen.blit(pygame.transform.scale(cestos_imgs['papel'], (150, 150)), (1000, screen_height - 200))

# Función para detectar la posición de la mano y arrastrar el residuo
def mover_residuo(mano_pos, residuos_pos):
    for i, pos in enumerate(residuos_pos):
        if residuos_en_mano[i] and puño_cerrado:
            residuos_pos[i] = mano_pos
    return residuos_pos

# Función para comprobar si el residuo está en el cesto correcto
def verificar_clasificacion(mano_pos, residuos_index):
    if cestos_rects['plastico'].collidepoint(mano_pos) and residuos_index == 0:
        return True
    elif cestos_rects['metal'].collidepoint(mano_pos) and residuos_index == 1:
        return True
    elif cestos_rects['papel'].collidepoint(mano_pos) and residuos_index == 2:
        return True
    return False

# Función para determinar si la mano está cerrada (puño)
def mano_esta_cerrada(hand_landmarks):
    indice_abierto = hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y
    pulgar_abierto = hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x
    return not (indice_abierto or pulgar_abierto)

# Ciclo principal del juego
running = True
while running:
    # Captura de eventos de Pygame
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Captura de la cámara
    success, image = cap.read()
    if not success:
        break

    # Voltear la imagen de la cámara horizontalmente (para simular un espejo)
    image = cv2.flip(image, 1)

    # Procesar la imagen con Mediapipe
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = mp_hands.process(image_rgb)

    # Mostrar imagen de la cámara como fondo
    frame_surface = pygame.surfarray.make_surface(image_rgb)
    frame_surface = pygame.transform.rotate(frame_surface, -90)
    frame_surface = pygame.transform.scale(frame_surface, (screen_width, screen_height))
    screen.blit(frame_surface, (0, 0))

    # Dibujar cestos de basura
    dibujar_cestos()

    # Dibujar residuos
    for i, img in enumerate(residuos_imgs):
        if not residuos_clasificados[i]:
            screen.blit(img, residuos_pos[i])

    # Si se detectan manos
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Invertir el eje X de la posición de la mano para corregir el movimiento
            mano_pos = (screen_width - int(hand_landmarks.landmark[9].x * screen_width), 
                        int(hand_landmarks.landmark[9].y * screen_height))
            puño_cerrado = mano_esta_cerrada(hand_landmarks)
            
            # Verificar si se mueve algún residuo
            for i in range(len(residuos_imgs)):
                if residuos_pos[i][0] - 50 < mano_pos[0] < residuos_pos[i][0] + 50 and residuos_pos[i][1] - 50 < mano_pos[1] < residuos_pos[i][1] + 50:
                    if puño_cerrado:
                        residuos_en_mano[i] = True
                    else:
                        residuos_en_mano[i] = False
                        if cestos_rects['plastico'].collidepoint(mano_pos) or cestos_rects['metal'].collidepoint(mano_pos) or cestos_rects['papel'].collidepoint(mano_pos):
                            if verificar_clasificacion(mano_pos, i):
                                print("¡Clasificación correcta!")
                                residuos_clasificados[i] = True
                                clasificacion_correcta[i] = True
                            else:
                                print("Clasificación incorrecta. Inténtalo de nuevo.")
                                residuos_pos[i] = (random.randint(50, screen_width - 100), random.randint(50, 100))

            # Actualizar posición de residuos
            residuos_pos = mover_residuo(mano_pos, residuos_pos)

    # Verificar si todos los residuos han sido clasificados
    if all(residuos_clasificados):
        correctas = clasificacion_correcta.count(True)
        incorrectas = clasificacion_correcta.count(False)
        print(f"Juego terminado. Correctas: {correctas}, Incorrectas: {incorrectas}")
        running = False

    # Actualizar la pantalla
    pygame.display.flip()

# Finalizar Pygame
cap.release()
pygame.quit()