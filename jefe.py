"""
Módulo de Jefes y Enemigos Especiales.
Implementa al 'Guardian de las Ruinas' (Boss del Santuario Final):
- Fases de ataque: patrulla pesada, embestida de fuego (charge) y salto aplastante (slam).
- Proyectiles de energía / magma dirigidos o en abanico.
- Barra de vida de jefe estilo Metroidvania en el HUD inferior.
"""

import math
import random
import pygame

class ProyectilBoss:
    def __init__(self, x, y, vx, vy):
        self.rect = pygame.Rect(x - 8, y - 8, 16, 16)
        self.vx = vx
        self.vy = vy
        self.tiempo_vida = 3.5
        self.activo = True

    def actualizar(self, dt, plataformas, jugador, sistema_particulas, audio=None):
        if not self.activo:
            return False

        self.tiempo_vida -= dt
        if self.tiempo_vida <= 0:
            self.activo = False
            return False

        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)

        # Destruirse contra plataformas sólidas
        for plat in plataformas:
            if not plat.es_flotante and self.rect.colliderect(plat.rect):
                self.activo = False
                sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=8, color=(255, 140, 50))
                return False

        # Impacto contra el jugador
        if self.rect.colliderect(jugador.rect):
            self.activo = False
            dir_golpe = 1 if self.vx > 0 else -1
            jugador.recibir_dano(18, dir_golpe, sistema_particulas, audio=audio)
            return False

        return True

    def dibujar(self, superficie, camara):
        if not self.activo:
            return
        cx, cy = camara.aplicar_pos(self.rect.centerx, self.rect.centery)
        pygame.draw.circle(superficie, (255, 80, 40), (cx, cy), 9)
        pygame.draw.circle(superficie, (255, 220, 80), (cx, cy), 5)
        pygame.draw.circle(superficie, (255, 255, 255), (cx, cy), 2)


class GuardianRuinas:
    def __init__(self, x, y, limite_izq, limite_der):
        self.ancho = 64
        self.alto = 78
        self.rect = pygame.Rect(x, y, self.ancho, self.alto)
        self.limite_izq = limite_izq
        self.limite_der = limite_der

        self.vida_max = 180
        self.vida = 180
        self.vivo = True
        self.activo = False  # Se activa cuando el jugador entra al Santuario

        # Físicas y movimiento
        self.vx = 0.0
        self.vy = 0.0
        self.velocidad_patrulla = 85.0
        self.velocidad_embestida = 380.0
        self.gravedad = 1500.0
        self.direccion = -1

        # Estados: 'patrulla', 'embestida', 'salto', 'descanso'
        self.estado = "patrulla"
        self.temporizador_estado = 2.0
        self.cooldown_disparo = 2.5
        self.tiempo_herido = 0.0

        self.proyectiles = []

    def actualizar(self, dt, plataformas, jugador, sistema_particulas, audio=None):
        if not self.vivo:
            return

        # Activación al acercarse el jugador al Santuario (X > 2600)
        dist_x = abs(jugador.rect.centerx - self.rect.centerx)
        if not self.activo:
            if jugador.rect.centerx > 2600 and dist_x < 550:
                self.activo = True
                sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=25, color=(255, 100, 50))
            return

        if self.tiempo_herido > 0:
            self.tiempo_herido -= dt

        self.temporizador_estado -= dt
        self.cooldown_disparo -= dt

        # Máquina de estados del Jefe
        if self.estado == "patrulla":
            self.vx = self.direccion * self.velocidad_patrulla
            if self.rect.right >= self.limite_der:
                self.rect.right = self.limite_der
                self.direccion = -1
            elif self.rect.left <= self.limite_izq:
                self.rect.left = self.limite_izq
                self.direccion = 1

            # Transición a ataque aleatorio
            if self.temporizador_estado <= 0:
                ataque = random.choice(["embestida", "salto", "disparar"])
                if ataque == "embestida":
                    self.estado = "embestida"
                    self.direccion = 1 if jugador.rect.centerx > self.rect.centerx else -1
                    self.temporizador_estado = 1.3
                    if audio:
                        audio.reproducir("dash")
                elif ataque == "salto":
                    self.estado = "salto"
                    self.vy = -620.0
                    self.direccion = 1 if jugador.rect.centerx > self.rect.centerx else -1
                    self.vx = self.direccion * 220.0
                    self.temporizador_estado = 1.8
                else:
                    self.disparar_proyectiles(jugador, audio)
                    self.estado = "descanso"
                    self.temporizador_estado = 0.8

        elif self.estado == "embestida":
            self.vx = self.direccion * self.velocidad_embestida
            sistema_particulas.emitir_polvo(self.rect.centerx, self.rect.bottom, cantidad=3, color=(255, 120, 60))
            if self.rect.right >= self.limite_der or self.rect.left <= self.limite_izq or self.temporizador_estado <= 0:
                self.estado = "descanso"
                self.temporizador_estado = 0.9

        elif self.estado == "salto":
            if self.temporizador_estado <= 0 or self.rect.bottom >= 200:
                if self.temporizador_estado < 1.0:
                    self.estado = "descanso"
                    self.temporizador_estado = 0.7

        elif self.estado == "descanso":
            self.vx = 0
            if self.temporizador_estado <= 0:
                self.estado = "patrulla"
                self.temporizador_estado = random.uniform(1.8, 3.0)

        # Disparo periódico secundario
        if self.cooldown_disparo <= 0:
            self.disparar_proyectiles(jugador, audio)
            self.cooldown_disparo = random.uniform(2.6, 4.0)

        # Físicas y gravedad
        self.vy += self.gravedad * dt
        self.rect.x += int(self.vx * dt)
        self.rect.y += int(self.vy * dt)

        # Colisión con la plataforma del Santuario
        for plat in plataformas:
            if not plat.es_flotante and self.rect.colliderect(plat.rect):
                if self.vy > 0:
                    self.rect.bottom = plat.rect.top
                    self.vy = 0

        # Detección de ataque del jugador
        if jugador.tiempo_ataque > 0 and not jugador.ha_golpeado_en_este_ataque:
            if self.rect.colliderect(jugador.hitbox_ataque):
                jugador.ha_golpeado_en_este_ataque = True
                self.recibir_dano(14, 1 if jugador.mirando_derecha else -1, sistema_particulas, audio)

        # Colisión de daño por contacto con el jugador
        if self.rect.colliderect(jugador.rect):
            dir_empuje = 1 if jugador.rect.centerx > self.rect.centerx else -1
            jugador.recibir_dano(24, dir_empuje, sistema_particulas, audio)

        # Actualizar proyectiles
        self.proyectiles = [p for p in self.proyectiles if p.actualizar(dt, plataformas, jugador, sistema_particulas, audio)]

    def disparar_proyectiles(self, jugador, audio=None):
        # Disparo de 3 proyectiles de fuego en abanico hacia la posición del jugador
        dx = jugador.rect.centerx - self.rect.centerx
        dy = jugador.rect.centery - self.rect.centery
        dist = max(1.0, math.hypot(dx, dy))
        vel_base = 280.0
        vx = (dx / dist) * vel_base
        vy = (dy / dist) * vel_base

        ang_centro = math.atan2(vy, vx)
        for desvio in (-0.26, 0.0, 0.26):
            ang = ang_centro + desvio
            p_vx = math.cos(ang) * vel_base
            p_vy = math.sin(ang) * vel_base
            self.proyectiles.append(ProyectilBoss(self.rect.centerx, self.rect.centery - 10, p_vx, p_vy))

        if audio:
            audio.reproducir("ataque")

    def recibir_dano(self, cantidad, empuje_x, sistema_particulas, audio=None):
        self.vida -= cantidad
        self.tiempo_herido = 0.25
        self.rect.x += empuje_x * 10
        sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=16, color=(255, 180, 60))
        if audio:
            audio.reproducir("golpe")

        if self.vida <= 0:
            self.vivo = False
            sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=50, color=(255, 215, 0))

    def dibujar(self, superficie, camara):
        # Dibujar proyectiles
        for p in self.proyectiles:
            p.dibujar(superficie, camara)

        if not self.vivo:
            return

        rect_cam = camara.aplicar_rect(self.rect)

        # Sombra
        sombra_x, sombra_y = camara.aplicar_pos(self.rect.centerx, self.rect.bottom)
        pygame.draw.ellipse(superficie, (10, 10, 15), (sombra_x - 36, sombra_y - 8, 72, 16))

        # Cuerpo del Titán/Gólem de las Ruinas
        color_cuerpo = (245, 245, 245) if self.tiempo_herido > 0 else (65, 38, 52)
        pygame.draw.rect(superficie, color_cuerpo, rect_cam, border_radius=10)
        pygame.draw.rect(superficie, (200, 70, 80), rect_cam, 3, border_radius=10)

        # Placas de armadura y núcleo brillante
        pygame.draw.rect(superficie, (180, 50, 70), (rect_cam.centerx - 14, rect_cam.centery - 10, 28, 20), border_radius=4)
        pygame.draw.circle(superficie, (255, 220, 60), (rect_cam.centerx, rect_cam.centery), 6)

        # Cuernos / Corona de piedra
        puntos_corona = [
            (rect_cam.left + 8, rect_cam.top),
            (rect_cam.left + 16, rect_cam.top - 14),
            (rect_cam.centerx, rect_cam.top - 4),
            (rect_cam.right - 16, rect_cam.top - 14),
            (rect_cam.right - 8, rect_cam.top)
        ]
        pygame.draw.polygon(superficie, (85, 50, 65), puntos_corona)

        # Ojos demoníacos
        ojo1_x = rect_cam.centerx - 12 if self.direccion == -1 else rect_cam.centerx - 2
        ojo2_x = ojo1_x + 14
        ojo_y = rect_cam.top + 22
        pygame.draw.circle(superficie, (255, 60, 60), (ojo1_x, ojo_y), 4)
        pygame.draw.circle(superficie, (255, 60, 60), (ojo2_x, ojo_y), 4)

