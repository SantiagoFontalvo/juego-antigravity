"""
Módulo Generador de Sprites Visuales para la Espada (Slash VFX).
Diseña fotogramas nítidos en pixel art con brillo estelar, hojas afiladas
y arcos de energía mística estilo Metroidvania.
"""

import pygame

def crear_sprites_espada(escala=1.0):
    """
    Genera 4 fotogramas secuenciales de alta calidad que representan:
    - Fotograma 0: Desenfundado rápido y destello inicial.
    - Fotograma 1: Tajo expansivo con filo de hoja y arco luminoso turquesa.
    - Fotograma 2: Impacto frontal de máximo alcance con chispas de corte.
    - Fotograma 3: Estela residual que se disipa con elegancia.
    """
    frames = []

    # Frame 0: Inicio de arco y brillo superior
    s0 = pygame.Surface((130, 130), pygame.SRCALPHA)
    # Brillo exterior
    pygame.draw.arc(s0, (70, 160, 255, 160), pygame.Rect(35, 15, 80, 80), 0.7, 2.3, 6)
    # Filo central
    pygame.draw.arc(s0, (180, 240, 255, 230), pygame.Rect(37, 17, 76, 76), 0.9, 2.1, 3)
    # Núcleo blanco
    pygame.draw.arc(s0, (255, 255, 255, 255), pygame.Rect(39, 19, 72, 72), 1.1, 1.9, 2)
    frames.append(s0)

    # Frame 1: Corte amplio de media luna con hoja metálica
    s1 = pygame.Surface((130, 130), pygame.SRCALPHA)
    # Silueta de filo
    puntos_hoja = [(65, 18), (112, 38), (118, 72), (80, 82), (98, 58)]
    pygame.draw.polygon(s1, (130, 220, 255, 170), puntos_hoja)
    # Resplandor exterior
    pygame.draw.arc(s1, (40, 140, 255, 210), pygame.Rect(28, 10, 94, 94), -0.5, 1.9, 8)
    # Hoja de acero luminosa
    pygame.draw.arc(s1, (170, 240, 255, 255), pygame.Rect(30, 12, 90, 90), -0.3, 1.7, 4)
    # Filo blanco puro
    pygame.draw.arc(s1, (255, 255, 255, 255), pygame.Rect(32, 14, 86, 86), -0.1, 1.5, 2)
    frames.append(s1)

    # Frame 2: Máxima extensión y chispas cortantes frontales
    s2 = pygame.Surface((130, 130), pygame.SRCALPHA)
    pygame.draw.arc(s2, (60, 160, 255, 230), pygame.Rect(24, 18, 100, 90), -1.1, 0.9, 9)
    pygame.draw.arc(s2, (200, 250, 255, 255), pygame.Rect(26, 20, 96, 86), -0.9, 0.7, 5)
    pygame.draw.arc(s2, (255, 255, 255, 255), pygame.Rect(28, 22, 92, 82), -0.7, 0.5, 2)

    # Chispas y estelas de velocidad en la punta de la espada
    pygame.draw.line(s2, (255, 255, 255), (105, 52), (128, 44), 3)
    pygame.draw.line(s2, (180, 235, 255), (110, 68), (129, 74), 2)
    pygame.draw.circle(s2, (255, 255, 255), (124, 48), 3)
    frames.append(s2)

    # Frame 3: Disipación suave de la estela
    s3 = pygame.Surface((130, 130), pygame.SRCALPHA)
    pygame.draw.arc(s3, (100, 190, 255, 130), pygame.Rect(36, 28, 86, 76), -1.2, 0.2, 4)
    pygame.draw.arc(s3, (220, 245, 255, 190), pygame.Rect(38, 30, 82, 72), -1.0, 0.0, 2)
    frames.append(s3)

    return frames

