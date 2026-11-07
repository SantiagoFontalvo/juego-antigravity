"""
Módulo de Enemigos.
Contiene:
- EnemigoPatrulla: Criaturas terrestres que patrullan plataformas.
- EnemigoVolador: Murciélagos/Espectros celestes que vuelan con movimiento ondulatorio,
  persiguen al jugador al acercarse y son ideales para derrotar con el ataque hacia arriba.
"""

import math
import random
import pygame

class EnemigoPatrulla:
    def __init__(self, x, y, limite_izq, limite_der):
        self.rect = pygame.Rect(x, y, 42, 42)
        self.limite_izq = limite_izq
        self.limite_der = limite_der
        self.velocidad = 110.0
        self.direccion = 1
        self.vida = 30
        self.vida_max = 30
        self.vivo = True
        self.tiempo_herido = 0.0

    def actualizar(self, dt, jugador, sistema_particulas):
        if not self.vivo:
            return

        if self.tiempo_herido > 0:
            self.tiempo_herido -= dt

        # Movimiento de patrulla entre dos extremos
        self.rect.x += int(self.direccion * self.velocidad * dt)
        if self.rect.right >= self.limite_der:
            self.rect.right = self.limite_der
            self.direccion = -1
        elif self.rect.left <= self.limite_izq:
            self.rect.left = self.limite_izq
            self.direccion = 1

        # Detección de golpe del ataque del jugador
        if jugador.tiempo_ataque > 0 and not jugador.ha_golpeado_en_este_ataque:
            if self.rect.colliderect(jugador.hitbox_ataque):
                jugador.ha_golpeado_en_este_ataque = True
                self.recibir_dano(15, 1 if jugador.mirando_derecha else -1, sistema_particulas)

        # Colisión con el jugador (daño por contacto)
        if self.rect.colliderect(jugador.rect):
            dir_empuje = 1 if jugador.rect.centerx > self.rect.centerx else -1
            jugador.recibir_dano(20, dir_empuje, sistema_particulas)

    def recibir_dano(self, cantidad, empuje_x, sistema_particulas):
        self.vida -= cantidad
        self.tiempo_herido = 0.25
        self.rect.x += empuje_x * 20
        sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=14, color=(255, 120, 60))

        if self.vida <= 0:
            self.vivo = False
            sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=25, color=(255, 80, 50))

    def dibujar(self, superficie, camara):
        if not self.vivo:
            return
        rect_cam = camara.aplicar_rect(self.rect)

        # Monstruo de piedra y magma
        color_cuerpo = (230, 230, 230) if self.tiempo_herido > 0 else (75, 45, 60)
        pygame.draw.rect(superficie, color_cuerpo, rect_cam, border_radius=6)
        pygame.draw.rect(superficie, (180, 50, 70), rect_cam, 2, border_radius=6)

        # Ojo
        ojo_x = rect_cam.centerx + (8 if self.direccion == 1 else -8)
        ojo_y = rect_cam.centery - 4
        pygame.draw.circle(superficie, (255, 220, 50), (ojo_x, ojo_y), 5)
        pygame.draw.circle(superficie, (180, 20, 20), (ojo_x, ojo_y), 2)

        # Barra de salud superior
        bw = rect_cam.width
        bh = 5
        bx = rect_cam.x
        by = rect_cam.top - 9
        pygame.draw.rect(superficie, (30, 30, 30), (bx, by, bw, bh))
        vida_w = int((self.vida / self.vida_max) * bw)
        pygame.draw.rect(superficie, (240, 70, 70), (bx, by, vida_w, bh))


class EnemigoVolador:
    """Criatura alada/espectro que flota con aleteo sinusoidal y acecha al jugador."""
    def __init__(self, x, y, rango_patrulla_x=220):
        self.centro_x = float(x)
        self.centro_y = float(y)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.rango_x = rango_patrulla_x
        self.rect = pygame.Rect(x - 18, y - 18, 36, 36)

        self.velocidad = 120.0
        self.tiempo_vuelo = random.uniform(0.0, 10.0)
        self.vida = 25
        self.vida_max = 25
        self.vivo = True
        self.tiempo_herido = 0.0
        self.aleteo = 0.0

    def actualizar(self, dt, jugador, sistema_particulas):
        if not self.vivo:
            return

        if self.tiempo_herido > 0:
            self.tiempo_herido -= dt

        self.tiempo_vuelo += dt * 3.5
        self.aleteo += dt * 14.0

        # Si el jugador está cerca (menos de 400px), el volador lo acecha suavemente
        dist_x = jugador.rect.centerx - self.pos_x
        dist_y = (jugador.rect.centery - 35) - self.pos_y
        dist = math.hypot(dist_x, dist_y)

        if dist < 380:
            # Persecución en picada suave
            self.pos_x += (dist_x / dist) * self.velocidad * dt
            self.pos_y += (dist_y / dist) * (self.velocidad * 0.8) * dt
        else:
            # Patrulla ondulante en reposo
            self.pos_x = self.centro_x + math.sin(self.tiempo_vuelo * 0.7) * self.rango_x
            self.pos_y = self.centro_y + math.sin(self.tiempo_vuelo * 2.0) * 35

        self.rect.center = (int(self.pos_x), int(self.pos_y))

        # Detección de impacto del ataque del jugador (horizontal o hacia arriba)
        if jugador.tiempo_ataque > 0 and not jugador.ha_golpeado_en_este_ataque:
            if self.rect.colliderect(jugador.hitbox_ataque):
                jugador.ha_golpeado_en_este_ataque = True
                empuje = 1 if jugador.mirando_derecha else -1
                if jugador.direccion_ataque == "arriba":
                    empuje = 0
                    self.pos_y -= 35  # Rebote hacia arriba al ser golpeado desde abajo
                self.recibir_dano(20, empuje, sistema_particulas)

        # Daño por contacto con el jugador
        if self.rect.colliderect(jugador.rect):
            dir_empuje = 1 if jugador.rect.centerx > self.rect.centerx else -1
            jugador.recibir_dano(16, dir_empuje, sistema_particulas)

    def recibir_dano(self, cantidad, empuje_x, sistema_particulas):
        self.vida -= cantidad
        self.tiempo_herido = 0.25
        self.pos_x += empuje_x * 25
        sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=14, color=(140, 220, 255))

        if self.vida <= 0:
            self.vivo = False
            sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=25, color=(120, 240, 255))

    def dibujar(self, superficie, camara):
        if not self.vivo:
            return
        rect_cam = camara.aplicar_rect(self.rect)

        # Sombra en el suelo si hay espacio
        sombra_x, sombra_y = camara.aplicar_pos(self.rect.centerx, self.rect.centery + 70)
        pygame.draw.ellipse(superficie, (10, 12, 20), (sombra_x - 16, sombra_y - 4, 32, 8))

        # Color con parpadeo al ser herido
        color_cuerpo = (255, 255, 255) if self.tiempo_herido > 0 else (45, 65, 110)

        # Alas batientes
        ala_altura = math.sin(self.aleteo) * 14
        cx, cy = rect_cam.centerx, rect_cam.centery

        # Ala izquierda y derecha
        puntos_ala_izq = [(cx - 4, cy - 2), (cx - 24, cy - 10 + int(ala_altura)), (cx - 14, cy + 8)]
        puntos_ala_der = [(cx + 4, cy - 2), (cx + 24, cy - 10 + int(ala_altura)), (cx + 14, cy + 8)]

        pygame.draw.polygon(superficie, (80, 140, 220), puntos_ala_izq)
        pygame.draw.polygon(superficie, (80, 140, 220), puntos_ala_der)
        pygame.draw.polygon(superficie, (180, 230, 255), puntos_ala_izq, 1)
        pygame.draw.polygon(superficie, (180, 230, 255), puntos_ala_der, 1)

        # Cuerpo central esférico / espectral
        pygame.draw.circle(superficie, color_cuerpo, (cx, cy), 13)
        pygame.draw.circle(superficie, (100, 200, 255), (cx, cy), 13, 2)

        # Ojos brillantes místicos (celeste/turquesa)
        pygame.draw.circle(superficie, (160, 245, 255), (cx - 4, cy - 2), 3)
        pygame.draw.circle(superficie, (160, 245, 255), (cx + 4, cy - 2), 3)

        # Barra de vida
        bw = 30
        bh = 4
        bx = cx - bw // 2
        by = rect_cam.top - 8
        pygame.draw.rect(superficie, (20, 20, 30), (bx, by, bw, bh))
        v_w = int((self.vida / self.vida_max) * bw)
        pygame.draw.rect(superficie, (70, 200, 255), (bx, by, v_w, bh))
