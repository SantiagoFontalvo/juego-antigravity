"""
Módulo del Escenario, Niveles y Transiciones de Salas / Mapas (Estilo Metroidvania).
Soporta:
- Múltiples mapas / salas interconectadas (Sala 1: Cavernas Profundas, Sala 2: Santuario Elevado).
- Plataformas accesibles con escalonamiento óptimo de salto.
- Portales / Umbrales de transición en paredes y puertas clásicas de Metroidvania.
- Dibujado de entornos con fondos parallax específicos por zona.
"""

import math
import random
import pygame
from config import (
    ANCHO_PANTALLA, ALTO_PANTALLA, MUNDO_ANCHO, MUNDO_ALTO,
    COLOR_FONDO_LEJANO, COLOR_FONDO_MEDIO,
    COLOR_SOLIDO, COLOR_SOLIDO_BORDE, COLOR_SOLIDO_SOMBRA,
    COLOR_FLOTANTE, COLOR_FLOTANTE_BORDE, COLOR_FLOTANTE_BRILLO,
    COLOR_PINCHOS, COLOR_ORO
)
from enemigos import EnemigoPatrulla, EnemigoVolador

# ==============================================================================
# CLASES DE ESCENARIO
# ==============================================================================
class Plataforma:
    def __init__(self, rect, es_flotante=False):
        self.rect = rect
        self.es_flotante = es_flotante  # True = atravesable desde abajo (One-way)


class PortalTransicion:
    """Umbral en la pared/puerta que transporta al jugador a otra sala de estilo Metroidvania."""
    def __init__(self, rect, destino_mapa, spawn_x, spawn_y, nombre=""):
        self.rect = rect
        self.destino_mapa = destino_mapa
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.nombre = nombre
        self.tiempo_brillo = 0.0

    def actualizar(self, dt):
        self.tiempo_brillo += dt * 4.0

    def dibujar(self, superficie, camara):
        rect_cam = camara.aplicar_rect(self.rect)
        # Brillo místico que palpita en el portal / umbral
        alfa_brillo = int(140 + 70 * math.sin(self.tiempo_brillo))
        surf_portal = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(surf_portal, (100, 220, 255, alfa_brillo), (0, 0, self.rect.width, self.rect.height), border_radius=4)
        pygame.draw.rect(surf_portal, (255, 255, 255, 220), (0, 0, self.rect.width, self.rect.height), 2, border_radius=4)
        superficie.blit(surf_portal, rect_cam.topleft)


class Orbe:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.flotacion_y = float(y)
        self.rect = pygame.Rect(x - 14, y - 14, 28, 28)
        self.recolectado = False
        self.tiempo = random.uniform(0, 10)

    def actualizar(self, dt, jugador, sistema_particulas):
        if self.recolectado:
            return False
        self.tiempo += dt * 4.0
        self.flotacion_y = self.y + math.sin(self.tiempo) * 6
        self.rect.y = int(self.flotacion_y - 14)

        if self.rect.colliderect(jugador.rect):
            self.recolectado = True
            jugador.vida = min(jugador.vida_max, jugador.vida + 15)
            sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=20, color=COLOR_ORO)
            return True
        return False

    def dibujar(self, superficie, camara):
        if self.recolectado:
            return
        cx, cy = camara.aplicar_pos(self.rect.centerx, int(self.flotacion_y))
        pygame.draw.circle(superficie, (40, 120, 200), (cx, cy), 16)
        pygame.draw.circle(superficie, (100, 220, 255), (cx, cy), 10)
        pygame.draw.circle(superficie, (255, 255, 255), (cx, cy), 5)


class Moneda:
    """Moneda coleccionable pequeña que flota suavemente. Incrementa el contador de monedas del jugador."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.flotacion_y = float(y)
        self.rect = pygame.Rect(x - 8, y - 8, 16, 16)
        self.recolectada = False
        self.tiempo = random.uniform(0, 10)
        self.brillo = random.uniform(0, math.pi * 2)

    def actualizar(self, dt, jugador, sistema_particulas):
        if self.recolectada:
            return False
        self.tiempo += dt * 3.5
        self.brillo += dt * 6.0
        self.flotacion_y = self.y + math.sin(self.tiempo) * 4
        self.rect.y = int(self.flotacion_y - 8)

        if self.rect.colliderect(jugador.rect):
            self.recolectada = True
            sistema_particulas.emitir_chispas_golpe(
                self.rect.centerx, self.rect.centery, cantidad=10, color=(255, 215, 50)
            )
            return True
        return False

    def dibujar(self, superficie, camara):
        if self.recolectada:
            return
        cx, cy = camara.aplicar_pos(self.rect.centerx, int(self.flotacion_y))
        # Círculo dorado exterior
        pygame.draw.circle(superficie, (200, 150, 20), (cx, cy), 8)
        # Relleno interior
        pygame.draw.circle(superficie, (255, 215, 50), (cx, cy), 6)
        # Destello pulsante
        brillo_r = int(4 + 2 * math.sin(self.brillo))
        pygame.draw.circle(superficie, (255, 255, 180), (cx - 2, cy - 2), brillo_r)
        # Borde delgado
        pygame.draw.circle(superficie, (255, 240, 100), (cx, cy), 8, 1)


# ==============================================================================
# CONSTRUCTOR DE MAPAS Y SALAS METROIDVANIA
# ==============================================================================
def construir_sala_1():
    """SALA 1: Las Cavernas de Ruinas Subterráneas (con plataformas accesibles y salida derecha)."""
    plataformas = []
    pinchos = []
    portales = []

    # Bordes generales de la sala
    plataformas.append(Plataforma(pygame.Rect(-40, 0, 40, MUNDO_ALTO), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(0, -40, MUNDO_ANCHO, 40), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(0, MUNDO_ALTO - 50, MUNDO_ANCHO, 70), es_flotante=False))

    # Zona 1: Inicio
    plataformas.append(Plataforma(pygame.Rect(0, 720, 620, 50), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(260, 610, 150, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(460, 500, 160, 22), es_flotante=True))

    # Columna divisoria con paso
    plataformas.append(Plataforma(pygame.Rect(720, 0, 80, 560), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(720, 700, 80, 160), es_flotante=False))

    # Zona 2: Torre Vertical con escalonamiento alcanzable
    plataformas.append(Plataforma(pygame.Rect(870, 640, 170, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(1100, 530, 180, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(880, 420, 180, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(1120, 310, 200, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(910, 210, 190, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(1160, 140, 340, 28), es_flotante=True))

    # Zona 3: Templo Central
    plataformas.append(Plataforma(pygame.Rect(1380, 470, 460, 30), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(1530, 370, 170, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(1770, 280, 190, 22), es_flotante=True))

    plataformas.append(Plataforma(pygame.Rect(2000, 190, 70, 470), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(2000, 740, 70, 120), es_flotante=False))

    # Zona 4: El Abismo (con plataformas voladoras escalonadas de forma alcanzable)
    pinchos.append(pygame.Rect(2100, MUNDO_ALTO - 68, 650, 20))
    plataformas.append(Plataforma(pygame.Rect(2140, 640, 150, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(2340, 550, 160, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(2540, 460, 160, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(2740, 380, 160, 22), es_flotante=True))

    # Escalón intermedio para llegar cómodamente a la repisa del final sin quedar bloqueado
    plataformas.append(Plataforma(pygame.Rect(2860, 290, 140, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(2980, 210, 140, 22), es_flotante=True))

    # Pasillo final hacia la salida
    plataformas.append(Plataforma(pygame.Rect(2760, 480, 560, 40), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(3020, 370, 300, 30), es_flotante=False))

    # Pared derecha con puerta / umbral de cambio de mapa
    plataformas.append(Plataforma(pygame.Rect(MUNDO_ANCHO - 30, 0, 40, 300), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(MUNDO_ANCHO - 30, 460, 40, MUNDO_ALTO - 460), es_flotante=False))

    # Portal en la pared derecha (cambia a la Sala 2)
    portales.append(PortalTransicion(
        pygame.Rect(MUNDO_ANCHO - 36, 300, 36, 160),
        destino_mapa=2,
        spawn_x=90,
        spawn_y=550,
        nombre="Hacia el Santuario Sagrado ->"
    ))

    enemigos = [
        EnemigoPatrulla(280, 568, 260, 410),
        EnemigoPatrulla(900, 378, 880, 1060),
        EnemigoPatrulla(1420, 428, 1380, 1840),
        EnemigoPatrulla(2780, 438, 2760, 3200),
    ]

    orbes = [
        Orbe(330, 570),
        Orbe(530, 460),
        Orbe(960, 170),
        Orbe(1300, 100),
        Orbe(1610, 330),
        Orbe(1860, 240),
        Orbe(2220, 600),
        Orbe(2600, 420),
        Orbe(2930, 250),
        Orbe(3160, 330),
    ]

    # Monedas dispersas en sala 1
    monedas = [
        Moneda(150, 690), Moneda(220, 690), Moneda(290, 580),
        Moneda(380, 580), Moneda(500, 470), Moneda(570, 470),
        Moneda(950, 600), Moneda(1020, 600), Moneda(1150, 490),
        Moneda(1200, 280), Moneda(1350, 110), Moneda(1420, 110),
        Moneda(1600, 340), Moneda(1700, 340), Moneda(1820, 250),
        Moneda(2200, 610), Moneda(2270, 610), Moneda(2420, 520),
        Moneda(2600, 430), Moneda(2850, 260), Moneda(2960, 180),
        Moneda(3080, 340), Moneda(3150, 340),
    ]

    return plataformas, pinchos, enemigos, orbes, portales, monedas


def construir_sala_2():
    """
    SALA 2: El Santuario Elevado de Cristal.
    Entorno vertical con:
    - 20+ plataformas escalonadas (accesibles con salto + doble salto)
    - 7 EnemigoVolador distribuidos en diferentes alturas
    - 3 EnemigoPatrulla en terrazas
    - Monedas dispersas (25+)
    - Pinchos en zonas bajas y fosos
    - Dos portales: regreso a Sala 1 (izq) y zona interior de cristal (der)
    """
    plataformas = []
    pinchos = []
    portales = []

    # ── Bordes de sala ──────────────────────────────────────────────────────
    plataformas.append(Plataforma(pygame.Rect(0, -40, MUNDO_ANCHO, 40), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(MUNDO_ANCHO, 0, 40, MUNDO_ALTO), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(0, MUNDO_ALTO - 50, MUNDO_ANCHO, 70), es_flotante=False))

    # Pared izquierda con hueco para portal de regreso
    plataformas.append(Plataforma(pygame.Rect(-40, 0, 40, 400), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(-40, 560, 40, MUNDO_ALTO - 560), es_flotante=False))

    # Portal de regreso a Sala 1 (pared izquierda)
    portales.append(PortalTransicion(
        pygame.Rect(0, 400, 36, 160),
        destino_mapa=1,
        spawn_x=MUNDO_ANCHO - 110,
        spawn_y=380,
        nombre="<- Regreso a las Cavernas"
    ))

    # ── ZONA A: Entrada — suelo de cristal (x 0–600) ────────────────────────
    plataformas.append(Plataforma(pygame.Rect(0, 620, 500, 40), es_flotante=False))   # Suelo entrada
    plataformas.append(Plataforma(pygame.Rect(100, 510, 140, 22), es_flotante=True))  # Repisa baja A
    plataformas.append(Plataforma(pygame.Rect(290, 420, 150, 22), es_flotante=True))  # Repisa media A
    plataformas.append(Plataforma(pygame.Rect(460, 320, 160, 22), es_flotante=True))  # Repisa alta A

    pinchos.append(pygame.Rect(520, MUNDO_ALTO - 68, 180, 20))                        # Foso entrada

    # ── ZONA B: Columnas de Cristal (x 600–1300) ────────────────────────────
    plataformas.append(Plataforma(pygame.Rect(650, 540, 130, 22), es_flotante=True))  # Repisa B1
    plataformas.append(Plataforma(pygame.Rect(830, 440, 150, 22), es_flotante=True))  # Repisa B2
    plataformas.append(Plataforma(pygame.Rect(1010, 350, 160, 22), es_flotante=True)) # Repisa B3
    plataformas.append(Plataforma(pygame.Rect(1200, 260, 170, 22), es_flotante=True)) # Repisa B4

    # Pilares decorativos (sólidos, no atravesables)
    plataformas.append(Plataforma(pygame.Rect(600, 460, 36, 440), es_flotante=False)) # Pilar izq B
    plataformas.append(Plataforma(pygame.Rect(1300, 380, 36, 520), es_flotante=False))# Pilar der B

    pinchos.append(pygame.Rect(636, MUNDO_ALTO - 68, 660, 20))                        # Foso cristal

    # ── ZONA C: Terraza Sagrada (x 1300–2100) ───────────────────────────────
    plataformas.append(Plataforma(pygame.Rect(1340, 490, 440, 30), es_flotante=False)) # Terraza C suelo
    plataformas.append(Plataforma(pygame.Rect(1420, 390, 160, 22), es_flotante=True))  # Repisa C1
    plataformas.append(Plataforma(pygame.Rect(1640, 300, 170, 22), es_flotante=True))  # Repisa C2
    plataformas.append(Plataforma(pygame.Rect(1850, 210, 180, 22), es_flotante=True))  # Repisa C3
    plataformas.append(Plataforma(pygame.Rect(2020, 130, 220, 28), es_flotante=True))  # Repisa C cima

    # Foso bajo la terraza C
    pinchos.append(pygame.Rect(1340, MUNDO_ALTO - 68, 400, 20))

    # ── ZONA D: Abismo de los Espíritus (x 2100–2800) ───────────────────────
    plataformas.append(Plataforma(pygame.Rect(2130, 580, 140, 22), es_flotante=True))  # Repisa D1
    plataformas.append(Plataforma(pygame.Rect(2320, 480, 150, 22), es_flotante=True))  # Repisa D2
    plataformas.append(Plataforma(pygame.Rect(2510, 390, 150, 22), es_flotante=True))  # Repisa D3
    plataformas.append(Plataforma(pygame.Rect(2700, 300, 160, 22), es_flotante=True))  # Repisa D4

    pinchos.append(pygame.Rect(2100, MUNDO_ALTO - 68, 760, 20))                        # Gran abismo

    # ── ZONA E: Gran Altar de Cristal (x 2800–3400) ─────────────────────────
    plataformas.append(Plataforma(pygame.Rect(2820, 420, 540, 40), es_flotante=False)) # Altar base
    plataformas.append(Plataforma(pygame.Rect(2900, 310, 170, 22), es_flotante=True))  # Repisa altar 1
    plataformas.append(Plataforma(pygame.Rect(3100, 220, 200, 28), es_flotante=False)) # Altar cima
    plataformas.append(Plataforma(pygame.Rect(3220, 130, 150, 22), es_flotante=True))  # Plataforma secreta

    # ── ENEMIGOS ─────────────────────────────────────────────────────────────
    enemigos = [
        # Patrulleros terrestres
        EnemigoPatrulla(300, 378, 290, 440),          # Zona A repisa media
        EnemigoPatrulla(1400, 448, 1340, 1780),       # Terraza C
        EnemigoPatrulla(2870, 378, 2820, 3300),       # Altar base

        # Voladores: distribuidos a distintas alturas por toda la sala
        EnemigoVolador(400,  260, rango_patrulla_x=180),  # Zona A, alto
        EnemigoVolador(750,  350, rango_patrulla_x=200),  # Zona B columnas
        EnemigoVolador(1100, 200, rango_patrulla_x=220),  # Zona B, muy alto
        EnemigoVolador(1700, 160, rango_patrulla_x=200),  # Zona C, cima
        EnemigoVolador(2200, 420, rango_patrulla_x=240),  # Abismo D1
        EnemigoVolador(2600, 300, rango_patrulla_x=200),  # Abismo D3
        EnemigoVolador(3050, 160, rango_patrulla_x=180),  # Altar cima
    ]

    # ── ORBES DE VIDA ────────────────────────────────────────────────────────
    orbes = [
        Orbe(180, 470),
        Orbe(380, 380),
        Orbe(560, 280),
        Orbe(900, 400),
        Orbe(1100, 310),
        Orbe(1320, 160),
        Orbe(1690, 260),
        Orbe(1920, 170),
        Orbe(2340, 440),
        Orbe(2580, 350),
        Orbe(3000, 270),
        Orbe(3200, 180),
    ]

    # ── MONEDAS ──────────────────────────────────────────────────────────────
    monedas = [
        # Zona A entrada
        Moneda(80, 590),  Moneda(160, 590), Moneda(240, 590),
        Moneda(140, 480), Moneda(200, 480),
        Moneda(330, 390), Moneda(390, 390),
        Moneda(500, 290), Moneda(560, 290),
        # Zona B columnas
        Moneda(690, 510), Moneda(750, 510),
        Moneda(870, 410), Moneda(930, 410),
        Moneda(1050, 320), Moneda(1110, 320),
        Moneda(1240, 230), Moneda(1300, 230),
        # Zona C terraza
        Moneda(1380, 460), Moneda(1460, 460), Moneda(1540, 460),
        Moneda(1470, 360), Moneda(1550, 360),
        Moneda(1680, 270), Moneda(1760, 270),
        Moneda(1890, 180), Moneda(1960, 180),
        Moneda(2060, 100), Moneda(2140, 100),
        # Zona D abismo
        Moneda(2170, 550), Moneda(2230, 550),
        Moneda(2360, 450), Moneda(2420, 450),
        Moneda(2550, 360), Moneda(2610, 360),
        # Zona E altar
        Moneda(2860, 390), Moneda(2940, 390), Moneda(3020, 390),
        Moneda(2940, 280), Moneda(3000, 280),
        Moneda(3140, 190), Moneda(3230, 100),
    ]

    return plataformas, pinchos, enemigos, orbes, portales, monedas


def construir_mundo(id_mapa=1):
    if id_mapa == 2:
        return construir_sala_2()
    return construir_sala_1()


# ==============================================================================
# RENDERIZADO DEL ENTORNO
# ==============================================================================
def dibujar_fondo_parallax(superficie, camara, id_mapa=1, tiempo_global=0.0):
    if id_mapa == 2:
        # ── SALA 2: Santuario de Cristal — fondo vívido y atmosférico ──────
        superficie.fill((6, 10, 22))

        # --- CAPA 1 (más lejana, muy lenta): Espiras de cristal gigantes ----
        offset_x1 = int(camara.x * 0.08)
        offset_y1 = int(camara.y * 0.08)
        colores_espira = [(14, 28, 55), (18, 36, 70), (22, 44, 85)]
        for i in range(-1, (ANCHO_PANTALLA // 180) + 4):
            base_x = i * 180 - (offset_x1 % 180)
            altura_espira = 220 + (i % 4) * 55
            color_e = colores_espira[i % 3]
            pygame.draw.polygon(superficie, color_e, [
                (base_x + 30, ALTO_PANTALLA + 30 - int(offset_y1 * 0.3)),
                (base_x + 55, ALTO_PANTALLA + 30 - int(offset_y1 * 0.3) - altura_espira),
                (base_x + 80, ALTO_PANTALLA + 30 - int(offset_y1 * 0.3)),
            ])
            # Borde luminoso en la espira
            pygame.draw.line(superficie, (30, 70, 130),
                             (base_x + 55, ALTO_PANTALLA + 30 - int(offset_y1 * 0.3) - altura_espira),
                             (base_x + 55, ALTO_PANTALLA + 30 - int(offset_y1 * 0.3)), 1)

        # --- CAPA 2 (media): Plataformas flotantes silhouetted ---------------
        offset_x2 = int(camara.x * 0.22)
        offset_y2 = int(camara.y * 0.22)
        for i in range(-1, (ANCHO_PANTALLA // 240) + 4):
            fx = i * 240 - (offset_x2 % 240)
            fy = 90 + (i % 3) * 55 - int(offset_y2 * 0.5)
            pygame.draw.ellipse(superficie, (12, 24, 46), (fx, fy, 160, 28))
            pygame.draw.ellipse(superficie, (22, 50, 90), (fx + 10, fy + 2, 140, 10))

        # --- Brillo ambiental de luz cenital (rayos) -------------------------
        offset_x3 = int(camara.x * 0.12)
        rayo_base_alpha = int(18 + 8 * math.sin(tiempo_global * 0.9))
        surf_rayos = pygame.Surface((ANCHO_PANTALLA, ALTO_PANTALLA), pygame.SRCALPHA)
        for i in range(-1, (ANCHO_PANTALLA // 320) + 3):
            rx = i * 320 - (offset_x3 % 320) + 60
            fase = math.sin(tiempo_global * 0.7 + i * 1.2)
            alpha = max(0, min(60, int(rayo_base_alpha + fase * 12)))
            puntos_rayo = [
                (rx - 25, 0),
                (rx + 25, 0),
                (rx + 60, ALTO_PANTALLA),
                (rx - 60, ALTO_PANTALLA),
            ]
            pygame.draw.polygon(surf_rayos, (60, 140, 255, alpha), puntos_rayo)
        superficie.blit(surf_rayos, (0, 0))

        # --- CAPA 3 (cerca): Bruma luminosa de cristal en la base -----------
        offset_x4 = int(camara.x * 0.45)
        for i in range(-1, (ANCHO_PANTALLA // 130) + 4):
            bx = i * 130 - (offset_x4 % 130)
            by = int(ALTO_PANTALLA - 60 - int(camara.y * 0.3))
            pygame.draw.ellipse(superficie, (18, 45, 90), (bx - 30, by, 120, 32))

        # --- Estrellas / partículas de luz flotantes en el fondo ------------
        random.seed(42)
        for _ in range(55):
            sx = random.randint(0, ANCHO_PANTALLA)
            sy = random.randint(0, ALTO_PANTALLA)
            radio = random.randint(1, 2)
            brillo_e = int(120 + 80 * math.sin(tiempo_global * random.uniform(0.5, 2.0) + random.uniform(0, 6)))
            brillo_e = max(60, min(220, brillo_e))
            pygame.draw.circle(superficie, (brillo_e, brillo_e + 20, 255), (sx, sy), radio)
        random.seed()  # Restaurar aleatoriedad

    else:
        # ── SALA 1: Cavernas Góticas (original) ──────────────────────────────
        superficie.fill(COLOR_FONDO_LEJANO)
        offset_x1 = int(camara.x * 0.15)
        offset_y1 = int(camara.y * 0.15)
        for i in range(-1, (ANCHO_PANTALLA // 260) + 3):
            x = i * 260 - (offset_x1 % 260)
            pygame.draw.rect(superficie, (18, 22, 34), (x, 80 - offset_y1 * 0.3, 75, ALTO_PANTALLA + 200))
            pygame.draw.circle(superficie, (25, 30, 48), (x + 37, int(200 - offset_y1 * 0.2)), 45)

        offset_x2 = int(camara.x * 0.40)
        for i in range(-1, (ANCHO_PANTALLA // 180) + 3):
            x = i * 180 - (offset_x2 % 180)
            h = 180 + (i % 3) * 60
            y = ALTO_PANTALLA - h + 20 - int(camara.y * 0.25)
            pygame.draw.polygon(superficie, COLOR_FONDO_MEDIO, [
                (x, ALTO_PANTALLA),
                (x + 90, y),
                (x + 180, ALTO_PANTALLA)
            ])


def dibujar_plataformas_y_pinchos(superficie, plataformas, pinchos, camara):
    for plat in plataformas:
        rect_cam = camara.aplicar_rect(plat.rect)
        if not rect_cam.colliderect(pygame.Rect(0, 0, ANCHO_PANTALLA, ALTO_PANTALLA)):
            continue

        if plat.es_flotante:
            pygame.draw.rect(superficie, COLOR_FLOTANTE, rect_cam, border_radius=4)
            pygame.draw.rect(superficie, COLOR_FLOTANTE_BORDE, rect_cam, 2, border_radius=4)
            pygame.draw.line(superficie, COLOR_FLOTANTE_BRILLO,
                             (rect_cam.left + 4, rect_cam.top + 2),
                             (rect_cam.right - 4, rect_cam.top + 2), 2)
            for rx in range(rect_cam.left + 20, rect_cam.right - 20, 35):
                pygame.draw.circle(superficie, COLOR_FLOTANTE_BORDE, (rx, rect_cam.centery), 2)
        else:
            pygame.draw.rect(superficie, COLOR_SOLIDO, rect_cam)
            pygame.draw.rect(superficie, COLOR_SOLIDO_BORDE, (rect_cam.x, rect_cam.y, rect_cam.width, 4))
            pygame.draw.rect(superficie, COLOR_SOLIDO_SOMBRA, (rect_cam.x, rect_cam.bottom - 4, rect_cam.width, 4))
            for dx in range(0, rect_cam.width, 40):
                pygame.draw.line(superficie, COLOR_SOLIDO_SOMBRA,
                                 (rect_cam.x + dx, rect_cam.y + 4),
                                 (rect_cam.x + dx, rect_cam.bottom - 4), 1)

    for p in pinchos:
        rect_cam = camara.aplicar_rect(p)
        paso = 18
        num_pinchos = rect_cam.width // paso
        for i in range(num_pinchos):
            px = rect_cam.x + i * paso
            py = rect_cam.bottom
            puntos = [(px, py), (px + paso // 2, rect_cam.y), (px + paso, py)]
            pygame.draw.polygon(superficie, COLOR_PINCHOS, puntos)
            pygame.draw.polygon(superficie, (255, 120, 120), puntos, 1)
