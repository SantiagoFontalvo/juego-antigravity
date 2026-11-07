"""
Cámara con desplazamiento suave (smooth lerp).
"""

import pygame

class Camara:
    def __init__(self, ancho_viewport, alto_viewport, mundo_ancho, mundo_alto):
        self.ancho_viewport = ancho_viewport
        self.alto_viewport = alto_viewport
        self.mundo_ancho = mundo_ancho
        self.mundo_alto = mundo_alto
        self.x = 0.0
        self.y = 0.0

    def seguir(self, objetivo_rect, suavizado=0.08):
        meta_x = objetivo_rect.centerx - self.ancho_viewport // 2
        meta_y = objetivo_rect.centery - self.alto_viewport // 2

        self.x += (meta_x - self.x) * suavizado
        self.y += (meta_y - self.y) * suavizado

        self.x = max(0, min(self.x, self.mundo_ancho - self.ancho_viewport))
        self.y = max(0, min(self.y, self.mundo_alto - self.alto_viewport))

    def aplicar_rect(self, rect):
        return pygame.Rect(rect.x - int(self.x), rect.y - int(self.y), rect.width, rect.height)

    def aplicar_pos(self, x, y):
        return int(x - self.x), int(y - self.y)

