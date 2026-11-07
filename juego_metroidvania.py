"""
Juego Metroidvania 2D con Plataformas Atravesables desde Abajo (One-Way Platforms)
---------------------------------------------------------------------------------
Mecánicas completas de Metroidvania:
1. Movimiento fluido horizontal (A / D o Flechas Izq / Der).
2. Salto físico variable + Doble Salto aéreo + Coyote Time + Jump Buffering.
3. PLATAFORMAS FLOTANTES SEMISÓLIDAS / ATRAVESABLES:
   - Se pueden atravesar libremente desde abajo hacia arriba y por los lados.
   - Al caer o aterrizar sobre ellas por encima, se convierten en superficie sólida.
   - Además, puedes bajarte de ellas presionando [S] o [Flecha Abajo] + Salto.
4. Habilidad de Esquiva / Dash con LSHIFT o K (con estela translúcida).
5. Sistema de Ataque con J o X (caja de golpe frontal activa y efecto visual de arco).
6. Enemigos de patrulla en plataformas con IA básica, barras de vida, daño y retroceso.
7. Sistema de Salud del Jugador (100 HP) con parpadeo invulnerable al recibir impacto.
8. Pinchos y fosos en abismos que reinician en un punto seguro.
9. Reliquias coleccionables y mini-mapa en tiempo real.
"""

import os
import sys
import math
import random
import pygame

# ==============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ==============================================================================
ANCHO_PANTALLA = 960
ALTO_PANTALLA = 540
FPS = 60

# Dimensiones del Mundo Metroidvania
MUNDO_ANCHO = 3400
MUNDO_ALTO = 950

# Paleta Metroidvania
COLOR_FONDO_LEJANO = (12, 14, 22)
COLOR_FONDO_MEDIO = (20, 24, 38)
COLOR_SOLIDO = (38, 45, 64)
COLOR_SOLIDO_BORDE = (70, 110, 170)
COLOR_SOLIDO_SOMBRA = (22, 26, 38)

# Colores para las plataformas flotantes atravesables (estilo místico / madera rúnica)
COLOR_FLOTANTE = (55, 75, 110)
COLOR_FLOTANTE_BORDE = (120, 210, 255)
COLOR_FLOTANTE_BRILLO = (180, 240, 255)

COLOR_PINCHOS = (220, 60, 60)
COLOR_ORO = (255, 215, 0)
COLOR_VIDA = (240, 60, 80)
COLOR_ESTAMINA = (70, 200, 250)


# ==============================================================================
# CLASE DE PLATAFORMA (Distingue entre bloques sólidos y flotantes atravesables)
# ==============================================================================
class Plataforma:
    def __init__(self, rect, es_flotante=False):
        self.rect = rect
        self.es_flotante = es_flotante  # True = atravesable desde abajo (One-way)


# ==============================================================================
# CÁMARA CON INTERPOLACIÓN SUAVE (SMOOTH LERP)
# ==============================================================================
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


# ==============================================================================
# SISTEMA DE PARTÍCULAS Y ESTELAS
# ==============================================================================
class SistemaParticulas:
    def __init__(self):
        self.particulas = []
        self.estelas_dash = []

    def emitir_polvo(self, x, y, cantidad=6, color=(160, 180, 210)):
        for _ in range(cantidad):
            self.particulas.append({
                "x": x, "y": y,
                "vx": random.uniform(-1.8, 1.8),
                "vy": random.uniform(-1.6, -0.2),
                "radio": random.uniform(2.5, 4.5),
                "vida": random.uniform(0.2, 0.45),
                "vida_max": 0.45,
                "color": color
            })

    def emitir_chispas_golpe(self, x, y, cantidad=12, color=(255, 230, 100)):
        for _ in range(cantidad):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(2.0, 5.0)
            self.particulas.append({
                "x": x, "y": y,
                "vx": math.cos(ang) * spd,
                "vy": math.sin(ang) * spd,
                "radio": random.uniform(2.0, 4.0),
                "vida": random.uniform(0.2, 0.4),
                "vida_max": 0.4,
                "color": color
            })

    def agregar_estela_dash(self, img, pos_x, pos_y, mirando_derecha):
        self.estelas_dash.append({
            "img": img,
            "x": pos_x,
            "y": pos_y,
            "flip": mirando_derecha,
            "alfa": 180
        })

    def actualizar(self, dt):
        vivas = []
        for p in self.particulas:
            p["vida"] -= dt
            if p["vida"] > 0:
                p["x"] += p["vx"] * (dt * 60)
                p["y"] += p["vy"] * (dt * 60)
                p["radio"] = max(0.5, p["radio"] * 0.95)
                vivas.append(p)
        self.particulas = vivas

        estelas_vivas = []
        for e in self.estelas_dash:
            e["alfa"] -= 800 * dt
            if e["alfa"] > 0:
                estelas_vivas.append(e)
        self.estelas_dash = estelas_vivas

    def dibujar(self, superficie, camara):
        for e in self.estelas_dash:
            cx, cy = camara.aplicar_pos(e["x"], e["y"])
            img_copia = e["img"].copy()
            if not e["flip"]:
                img_copia = pygame.transform.flip(img_copia, True, False)
            img_copia.set_alpha(int(max(0, e["alfa"])))
            superficie.blit(img_copia, (cx, cy))

        for p in self.particulas:
            cx, cy = camara.aplicar_pos(p["x"], p["y"])
            factor = max(0.1, p["vida"] / p["vida_max"])
            radio = max(1, int(p["radio"] * factor))
            pygame.draw.circle(superficie, p["color"], (cx, cy), radio)


# ==============================================================================
# JUGADOR (CON COLISIONES ONE-WAY / ATRAVESABLES DESDE ABAJO)
# ==============================================================================
class Jugador:
    def __init__(self, x, y, frames):
        self.frames = frames

        self.anim_idle = frames[0:4]
        self.anim_walk = frames[4:12]
        self.frame_salto = frames[12]
        self.frame_caida = frames[13] if len(frames) > 13 else frames[12]

        # Dimensiones de colisión
        self.rect = pygame.Rect(x, y, 36, 70)

        # Físicas
        self.vx = 0.0
        self.vy = 0.0
        self.velocidad_caminar = 320.0
        self.fuerza_salto = -680.0
        self.gravedad = 1650.0
        self.velocidad_caida_max = 900.0

        # Estados de control y salto
        self.en_suelo = False
        self.mirando_derecha = True
        self.tiempo_coyote = 0.0
        self.tiempo_buffer_salto = 0.0
        self.puede_doble_salto = True
        self.doble_salto_disponible = False

        # Temporizador para atravesar intencionalmente hacia abajo con [Abajo + Salto]
        self.tiempo_bajar_plataforma = 0.0

        # Dash
        self.cooldown_dash = 0.0
        self.tiempo_dash = 0.0
        self.velocidad_dash = 780.0
        self.esta_haciendo_dash = False

        # Ataque
        self.tiempo_ataque = 0.0
        self.cooldown_ataque = 0.0
        self.hitbox_ataque = pygame.Rect(0, 0, 0, 0)
        self.ha_golpeado_en_este_ataque = False

        # Sistema de Vida
        self.vida_max = 100
        self.vida = 100
        self.tiempo_invulnerabilidad = 0.0
        self.punto_reaparicion = (x, y)

        # Animación
        self.estado_anim = "idle"
        self.indice_anim = 0.0

    def procesar_entrada(self, teclas, dt, sistema_particulas):
        if self.cooldown_dash > 0:
            self.cooldown_dash -= dt
        if self.cooldown_ataque > 0:
            self.cooldown_ataque -= dt
        if self.tiempo_invulnerabilidad > 0:
            self.tiempo_invulnerabilidad -= dt
        if self.tiempo_bajar_plataforma > 0:
            self.tiempo_bajar_plataforma -= dt

        # Estado de Dash
        if self.tiempo_dash > 0:
            self.tiempo_dash -= dt
            dir_signo = 1 if self.mirando_derecha else -1
            self.vx = dir_signo * self.velocidad_dash
            self.vy = 0

            img = self.obtener_imagen_actual()
            dib_x = self.rect.centerx - (img.get_width() // 2)
            dib_y = self.rect.bottom - img.get_height() + 10
            sistema_particulas.agregar_estela_dash(img, dib_x, dib_y, self.mirando_derecha)

            if self.tiempo_dash <= 0:
                self.esta_haciendo_dash = False
            return

        # Movimiento horizontal
        mover_izq = teclas[pygame.K_LEFT] or teclas[pygame.K_a]
        mover_der = teclas[pygame.K_RIGHT] or teclas[pygame.K_d]

        if mover_izq and not mover_der:
            self.vx = -self.velocidad_caminar
            self.mirando_derecha = False
        elif mover_der and not mover_izq:
            self.vx = self.velocidad_caminar
            self.mirando_derecha = True
        else:
            self.vx = 0.0

        if self.tiempo_buffer_salto > 0:
            self.tiempo_buffer_salto -= dt
        if self.tiempo_coyote > 0:
            self.tiempo_coyote -= dt

    def intentar_saltar(self, teclas, sistema_particulas):
        if self.esta_haciendo_dash:
            return

        # Mecánica de dejarse caer de una plataforma flotante: [Abajo / S] + [Salto]
        presiona_abajo = teclas[pygame.K_DOWN] or teclas[pygame.K_s]
        if presiona_abajo and self.en_suelo:
            self.tiempo_bajar_plataforma = 0.22  # Ignora colisión con flotantes temporalmente
            self.rect.y += 4
            self.vy = 120.0
            self.en_suelo = False
            return

        # Salto estándar
        self.tiempo_buffer_salto = 0.15
        if self.en_suelo or self.tiempo_coyote > 0:
            self.ejecutar_salto(sistema_particulas, es_doble=False)
            self.tiempo_buffer_salto = 0.0
            self.tiempo_coyote = 0.0
        elif self.puede_doble_salto and self.doble_salto_disponible:
            self.ejecutar_salto(sistema_particulas, es_doble=True)
            self.doble_salto_disponible = False
            self.tiempo_buffer_salto = 0.0

    def ejecutar_salto(self, sistema_particulas, es_doble=False):
        self.vy = self.fuerza_salto * (0.92 if es_doble else 1.0)
        self.en_suelo = False
        color_part = (120, 240, 255) if es_doble else (210, 220, 240)
        sistema_particulas.emitir_polvo(self.rect.centerx, self.rect.bottom, cantidad=8, color=color_part)

    def cortar_salto(self):
        if self.vy < -150:
            self.vy = -150

    def intentar_dash(self, sistema_particulas):
        if self.cooldown_dash <= 0 and not self.esta_haciendo_dash:
            self.esta_haciendo_dash = True
            self.tiempo_dash = 0.18
            self.cooldown_dash = 0.70
            sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=10, color=(100, 220, 255))

    def intentar_atacar(self, sistema_particulas):
        if self.cooldown_ataque <= 0 and self.tiempo_ataque <= 0:
            self.tiempo_ataque = 0.22
            self.cooldown_ataque = 0.38
            self.ha_golpeado_en_este_ataque = False

            ancho_corte = 55
            alto_corte = 50
            if self.mirando_derecha:
                self.hitbox_ataque = pygame.Rect(self.rect.right - 5, self.rect.centery - 25, ancho_corte, alto_corte)
            else:
                self.hitbox_ataque = pygame.Rect(self.rect.left - ancho_corte + 5, self.rect.centery - 25, ancho_corte, alto_corte)

            sistema_particulas.emitir_chispas_golpe(self.hitbox_ataque.centerx, self.hitbox_ataque.centery, cantidad=5, color=(200, 230, 255))

    def recibir_dano(self, cantidad, direccion_golpe, sistema_particulas):
        if self.tiempo_invulnerabilidad > 0:
            return False

        self.vida = max(0, self.vida - cantidad)
        self.tiempo_invulnerabilidad = 0.8
        self.vx = direccion_golpe * 300.0
        self.vy = -350.0
        self.en_suelo = False
        sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=14, color=(255, 60, 60))

        if self.vida <= 0:
            self.reaparecer()
        return True

    def reaparecer(self):
        self.rect.topleft = self.punto_reaparicion
        self.vida = self.vida_max
        self.vx = 0
        self.vy = 0
        self.tiempo_invulnerabilidad = 1.0

    def actualizar(self, dt, plataformas, sistema_particulas, teclas):
        if not self.esta_haciendo_dash:
            self.vy += self.gravedad * dt
            if self.vy > self.velocidad_caida_max:
                self.vy = self.velocidad_caida_max

        # Guardar posición Y previa exacta antes de aplicar el movimiento vertical
        prev_bottom = self.rect.bottom

        # 1. Movimiento horizontal
        self.rect.x += int(self.vx * dt)
        self.resolver_colisiones_horizontal(plataformas)

        # 2. Movimiento vertical
        estaba_en_suelo = self.en_suelo
        self.rect.y += int(self.vy * dt)
        self.en_suelo = False
        self.resolver_colisiones_vertical(plataformas, sistema_particulas, estaba_en_suelo, prev_bottom)

        if estaba_en_suelo and not self.en_suelo and self.vy >= 0:
            self.tiempo_coyote = 0.12

        if self.en_suelo and self.tiempo_buffer_salto > 0:
            self.intentar_saltar(teclas, sistema_particulas)

        if self.en_suelo:
            self.doble_salto_disponible = True
            if abs(self.vx) < 50:
                self.punto_reaparicion = (self.rect.x, self.rect.y - 10)

        # Actualizar ataque
        if self.tiempo_ataque > 0:
            self.tiempo_ataque -= dt
            if self.mirando_derecha:
                self.hitbox_ataque.x = self.rect.right - 5
            else:
                self.hitbox_ataque.x = self.rect.left - self.hitbox_ataque.width + 5
            self.hitbox_ataque.y = self.rect.centery - 25
            if self.tiempo_ataque <= 0:
                self.hitbox_ataque = pygame.Rect(0, 0, 0, 0)

        if self.en_suelo and abs(self.vx) > 50 and random.random() < 0.25:
            sistema_particulas.emitir_polvo(
                self.rect.centerx - (10 if self.mirando_derecha else -10),
                self.rect.bottom, cantidad=2
            )

        self.actualizar_animacion(dt)

    def resolver_colisiones_horizontal(self, plataformas):
        # Las plataformas flotantes (one-way) NO bloquean lateralmente: se pueden atravesar
        for plat in plataformas:
            if plat.es_flotante:
                continue
            if self.rect.colliderect(plat.rect):
                if self.vx > 0:
                    self.rect.right = plat.rect.left
                elif self.vx < 0:
                    self.rect.left = plat.rect.right

    def resolver_colisiones_vertical(self, plataformas, sistema_particulas, estaba_en_suelo, prev_bottom):
        for plat in plataformas:
            if not self.rect.colliderect(plat.rect):
                continue

            # CASO A: Plataforma FLOTANTE (One-Way)
            # Solo colisiona si el jugador está CAYENDO (vy >= 0),
            # si en el frame anterior estaba por encima o a la altura del borde superior,
            # y si no está forzando la bajada intencional con [Abajo + Salto].
            if plat.es_flotante:
                if self.tiempo_bajar_plataforma <= 0 and self.vy >= 0 and prev_bottom <= plat.rect.top + 16:
                    self.rect.bottom = plat.rect.top
                    self.vy = 0
                    self.en_suelo = True
                    if not estaba_en_suelo:
                        sistema_particulas.emitir_polvo(self.rect.centerx, self.rect.bottom, cantidad=6, color=(140, 200, 255))
                # Si sube desde abajo (vy < 0) o ya estaba dentro: ¡LA ATRAVIESA SIN CHOCAR!

            # CASO B: Estructura sólida tradicional (bloquea desde arriba y abajo)
            else:
                if self.vy > 0:
                    self.rect.bottom = plat.rect.top
                    self.vy = 0
                    self.en_suelo = True
                    if not estaba_en_suelo:
                        sistema_particulas.emitir_polvo(self.rect.centerx, self.rect.bottom, cantidad=7)
                elif self.vy < 0:
                    self.rect.top = plat.rect.bottom
                    self.vy = 0

    def actualizar_animacion(self, dt):
        if not self.en_suelo:
            self.estado_anim = "jump" if self.vy < -50 else "fall"
        elif abs(self.vx) > 10:
            self.estado_anim = "run"
        else:
            self.estado_anim = "idle"

        if self.estado_anim == "run":
            self.indice_anim += 11.0 * dt
        elif self.estado_anim == "idle":
            self.indice_anim += 4.5 * dt

    def obtener_imagen_actual(self):
        if self.estado_anim == "jump":
            img = self.frame_salto
        elif self.estado_anim == "fall":
            img = self.frame_caida
        elif self.estado_anim == "run":
            idx = int(self.indice_anim) % len(self.anim_walk)
            img = self.anim_walk[idx]
        else:
            idx = int(self.indice_anim) % len(self.anim_idle)
            img = self.anim_idle[idx]

        if not self.mirando_derecha:
            img = pygame.transform.flip(img, True, False)
        return img

    def dibujar(self, superficie, camara):
        if self.tiempo_invulnerabilidad > 0 and int(self.tiempo_invulnerabilidad * 20) % 2 == 0:
            return

        img = self.obtener_imagen_actual()
        sombra_x, sombra_y = camara.aplicar_pos(self.rect.centerx, self.rect.bottom)
        pygame.draw.ellipse(superficie, (10, 12, 18), (sombra_x - 22, sombra_y - 5, 44, 11))

        dib_x = self.rect.centerx - (img.get_width() // 2)
        dib_y = self.rect.bottom - img.get_height() + 10
        pos_cam = camara.aplicar_pos(dib_x, dib_y)
        superficie.blit(img, pos_cam)

        if self.tiempo_ataque > 0:
            arc_rect = camara.aplicar_rect(self.hitbox_ataque)
            pygame.draw.arc(superficie, (200, 240, 255), arc_rect, -1.2, 1.2, 5)
            pygame.draw.arc(superficie, (255, 255, 255), arc_rect.inflate(-4, -4), -1.2, 1.2, 2)


# ==============================================================================
# ENEMIGO PATRULLERO
# ==============================================================================
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

        self.rect.x += int(self.direccion * self.velocidad * dt)
        if self.rect.right >= self.limite_der:
            self.rect.right = self.limite_der
            self.direccion = -1
        elif self.rect.left <= self.limite_izq:
            self.rect.left = self.limite_izq
            self.direccion = 1

        if jugador.tiempo_ataque > 0 and not jugador.ha_golpeado_en_este_ataque:
            if self.rect.colliderect(jugador.hitbox_ataque):
                jugador.ha_golpeado_en_este_ataque = True
                self.recibir_dano(15, 1 if jugador.mirando_derecha else -1, sistema_particulas)

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

        color_cuerpo = (230, 230, 230) if self.tiempo_herido > 0 else (75, 45, 60)
        pygame.draw.rect(superficie, color_cuerpo, rect_cam, border_radius=6)
        pygame.draw.rect(superficie, (180, 50, 70), rect_cam, 2, border_radius=6)

        ojo_x = rect_cam.centerx + (8 if self.direccion == 1 else -8)
        ojo_y = rect_cam.centery - 4
        pygame.draw.circle(superficie, (255, 220, 50), (ojo_x, ojo_y), 5)
        pygame.draw.circle(superficie, (180, 20, 20), (ojo_x, ojo_y), 2)

        bw = rect_cam.width
        bh = 5
        bx = rect_cam.x
        by = rect_cam.top - 9
        pygame.draw.rect(superficie, (30, 30, 30), (bx, by, bw, bh))
        vida_w = int((self.vida / self.vida_max) * bw)
        pygame.draw.rect(superficie, (240, 70, 70), (bx, by, vida_w, bh))


# ==============================================================================
# ORBE RECOLECTABLE (RELIQUIAS)
# ==============================================================================
class Orbe:
    def __init__(self, x, y):
        self.x = x
        self.y = y
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


# ==============================================================================
# CREACIÓN DEL MUNDO (Distinguiendo Sólidos de Plataformas Flotantes)
# ==============================================================================
def construir_mundo():
    plataformas = []
    pinchos = []

    # 1. Bordes y Suelo General Sólido
    plataformas.append(Plataforma(pygame.Rect(-40, 0, 40, MUNDO_ALTO), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(MUNDO_ANCHO, 0, 40, MUNDO_ALTO), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(0, -40, MUNDO_ANCHO, 40), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(0, MUNDO_ALTO - 50, MUNDO_ANCHO, 70), es_flotante=False))

    # 2. Zona 1: Caverna Inicial
    plataformas.append(Plataforma(pygame.Rect(0, 720, 620, 50), es_flotante=False))  # Suelo sólido
    # Plataformas que están volando (atravesables desde abajo):
    plataformas.append(Plataforma(pygame.Rect(260, 610, 150, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(460, 500, 160, 22), es_flotante=True))

    # Columnas sólidas conectadas al techo/suelo
    plataformas.append(Plataforma(pygame.Rect(720, 0, 80, 560), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(720, 700, 80, 160), es_flotante=False))

    # 3. Zona 2: Torre Vertical (Plataformas suspendidas en el aire atravesables)
    plataformas.append(Plataforma(pygame.Rect(870, 640, 170, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(1100, 530, 180, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(880, 420, 180, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(1120, 310, 200, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(910, 200, 190, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(1160, 130, 340, 28), es_flotante=True))

    # 4. Zona 3: Templo Central (Plataforma principal sólida y repisas flotantes)
    plataformas.append(Plataforma(pygame.Rect(1380, 470, 460, 30), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(1530, 370, 170, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(1770, 280, 190, 22), es_flotante=True))

    # Muro divisor sólido
    plataformas.append(Plataforma(pygame.Rect(2000, 190, 70, 470), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(2000, 740, 70, 120), es_flotante=False))

    # 5. Zona 4: El Abismo de Ruinas Flotantes
    pinchos.append(pygame.Rect(2100, MUNDO_ALTO - 68, 650, 20))

    # Plataformas voladoras sobre el abismo (atravesables desde abajo)
    plataformas.append(Plataforma(pygame.Rect(2160, 640, 150, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(2380, 550, 160, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(2600, 450, 170, 22), es_flotante=True))
    plataformas.append(Plataforma(pygame.Rect(2820, 350, 190, 22), es_flotante=True))

    # Santuario Final
    plataformas.append(Plataforma(pygame.Rect(2740, 200, 480, 40), es_flotante=False))
    plataformas.append(Plataforma(pygame.Rect(3040, 100, 160, 22), es_flotante=True))

    enemigos = [
        EnemigoPatrulla(280, 568, 260, 410),
        EnemigoPatrulla(900, 378, 880, 1060),
        EnemigoPatrulla(1420, 428, 1380, 1840),
        EnemigoPatrulla(2770, 158, 2740, 3220),
    ]

    orbes = [
        Orbe(330, 570),
        Orbe(530, 460),
        Orbe(960, 160),
        Orbe(1300, 90),
        Orbe(1610, 330),
        Orbe(1860, 240),
        Orbe(2230, 600),
        Orbe(2680, 410),
        Orbe(2940, 160),
        Orbe(3110, 60),
    ]

    return plataformas, pinchos, enemigos, orbes


# ==============================================================================
# CARGA DE RECURSOS
# ==============================================================================
def cargar_frames_jugador():
    posibles_rutas = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ImagenesJuego", "spriteJugador.png"),
        os.path.join("ImagenesJuego", "spriteJugador.png"),
        os.path.join("..", "proyecto", "ImagenesJuego", "spriteJugador.png")
    ]
    ruta_encontrada = None
    for r in posibles_rutas:
        if os.path.exists(r):
            ruta_encontrada = r
            break

    if not ruta_encontrada:
        print(f"Error: No se encontró la imagen en {posibles_rutas}")
        pygame.quit()
        sys.exit(1)

    spritesheet = pygame.image.load(ruta_encontrada).convert_alpha()
    frame_ancho = 64
    frame_alto = 64
    escala = 2
    frames = []

    for fila in range(4):
        for col in range(4):
            rect = pygame.Rect(col * frame_ancho, fila * frame_alto, frame_ancho, frame_alto)
            sub = spritesheet.subsurface(rect)
            if sub.get_bounding_rect().width > 0:
                frame_escalado = pygame.transform.scale(sub, (frame_ancho * escala, frame_alto * escala))
                frames.append(frame_escalado)

    return frames


# ==============================================================================
# RENDERIZADO DEL ENTORNO
# ==============================================================================
def dibujar_fondo_parallax(superficie, camara):
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
            # Diseño distintivo para plataformas voladoras atravesables:
            # Barra estilizada con borde brillante y esquinas redondeadas
            pygame.draw.rect(superficie, COLOR_FLOTANTE, rect_cam, border_radius=4)
            pygame.draw.rect(superficie, COLOR_FLOTANTE_BORDE, rect_cam, 2, border_radius=4)
            # Línea de brillo en la cara superior (indica que es la superficie para pisar)
            pygame.draw.line(superficie, COLOR_FLOTANTE_BRILLO,
                             (rect_cam.left + 4, rect_cam.top + 2),
                             (rect_cam.right - 4, rect_cam.top + 2), 2)
            # Pequeñas runas/marcas decorativas
            for rx in range(rect_cam.left + 20, rect_cam.right - 20, 35):
                pygame.draw.circle(superficie, COLOR_FLOTANTE_BORDE, (rx, rect_cam.centery), 2)
        else:
            # Estructura sólida masiva
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


# ==============================================================================
# INTERFAZ HUD (VIDA, HABILIDADES Y MINI-MAPA)
# ==============================================================================
def dibujar_hud(superficie, jugador, orbes_obtenidos, total_orbes, camara, fuente, fuente_titulos):
    panel_w = 340
    panel_h = 88
    pygame.draw.rect(superficie, (16, 20, 30), (16, 14, panel_w, panel_h), border_radius=8)
    pygame.draw.rect(superficie, (65, 85, 125), (16, 14, panel_w, panel_h), 2, border_radius=8)

    # Barra de Vida
    pygame.draw.rect(superficie, (40, 15, 20), (30, 26, 160, 14), border_radius=4)
    vida_px = int((jugador.vida / jugador.vida_max) * 160)
    if vida_px > 0:
        pygame.draw.rect(superficie, COLOR_VIDA, (30, 26, vida_px, 14), border_radius=4)
    txt_hp = fuente.render(f"HP {jugador.vida}/{jugador.vida_max}", True, (255, 255, 255))
    superficie.blit(txt_hp, (35, 26))

    # Dash
    color_dash = COLOR_ESTAMINA if jugador.cooldown_dash <= 0 else (120, 130, 140)
    estado_dash = "Listo [LSHIFT/K]" if jugador.cooldown_dash <= 0 else f"{jugador.cooldown_dash:.1f}s"
    txt_dash = fuente.render(f"Dash: {estado_dash}", True, color_dash)
    superficie.blit(txt_dash, (200, 26))

    # Orbes y Doble Salto
    txt_orbes = fuente.render(f"Reliquias: {orbes_obtenidos}/{total_orbes}", True, COLOR_ORO)
    superficie.blit(txt_orbes, (30, 48))

    color_ds = (110, 255, 180) if jugador.doble_salto_disponible else (140, 150, 160)
    txt_ds = fuente.render(f"Doble Salto: {'Activo' if jugador.doble_salto_disponible else 'En Espera'}", True, color_ds)
    superficie.blit(txt_ds, (170, 48))

    txt_controles = fuente.render("A/D: Mover | W/Espacio: Saltar | S+Salto: Bajar plataforma", True, (170, 185, 210))
    superficie.blit(txt_controles, (30, 70))

    # Mini-mapa
    mapa_w = 170
    mapa_h = 55
    mapa_x = ANCHO_PANTALLA - mapa_w - 20
    mapa_y = 16
    pygame.draw.rect(superficie, (14, 16, 24), (mapa_x, mapa_y, mapa_w, mapa_h), border_radius=6)
    pygame.draw.rect(superficie, (60, 75, 110), (mapa_x, mapa_y, mapa_w, mapa_h), 2, border_radius=6)

    escala_mx = mapa_w / MUNDO_ANCHO
    escala_my = mapa_h / MUNDO_ALTO

    cam_vx = mapa_x + int(camara.x * escala_mx)
    cam_vy = mapa_y + int(camara.y * escala_my)
    cam_vw = int(ANCHO_PANTALLA * escala_mx)
    cam_vh = int(ALTO_PANTALLA * escala_my)
    pygame.draw.rect(superficie, (40, 55, 80), (cam_vx, cam_vy, cam_vw, cam_vh))

    jugador_mx = mapa_x + int(jugador.rect.centerx * escala_mx)
    jugador_my = mapa_y + int(jugador.rect.centery * escala_my)
    pygame.draw.circle(superficie, (255, 70, 70), (jugador_mx, jugador_my), 3)


# ==============================================================================
# BUCLE PRINCIPAL
# ==============================================================================
def main():
    pygame.init()
    pygame.display.set_caption("Metroidvania 2D - Plataformas Flotantes Atravesables")
    pantalla = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))
    reloj = pygame.time.Clock()

    fuente = pygame.font.Font(None, 20)
    fuente_titulos = pygame.font.Font(None, 26)
    fuente_victoria = pygame.font.Font(None, 46)

    frames_jugador = cargar_frames_jugador()
    plataformas, pinchos, enemigos, orbes = construir_mundo()

    jugador = Jugador(120, 600, frames_jugador)
    camara = Camara(ANCHO_PANTALLA, ALTO_PANTALLA, MUNDO_ANCHO, MUNDO_ALTO)
    sistema_particulas = SistemaParticulas()

    orbes_recolectados = 0
    total_orbes = len(orbes)
    ejecutando = True

    while ejecutando:
        dt = reloj.tick(FPS) / 1000.0
        dt = min(dt, 0.05)
        teclas = pygame.key.get_pressed()

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

            elif evento.type == pygame.KEYDOWN:
                if evento.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    jugador.intentar_saltar(teclas, sistema_particulas)
                elif evento.key in (pygame.K_j, pygame.K_x):
                    jugador.intentar_atacar(sistema_particulas)
                elif evento.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_k):
                    jugador.intentar_dash(sistema_particulas)
                elif evento.key == pygame.K_r:
                    jugador.reaparecer()

            elif evento.type == pygame.KEYUP:
                if evento.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    jugador.cortar_salto()

        # Actualización de jugador
        jugador.procesar_entrada(teclas, dt, sistema_particulas)
        jugador.actualizar(dt, plataformas, sistema_particulas, teclas)

        # Colisión con pinchos
        for pincho in pinchos:
            if jugador.rect.colliderect(pincho):
                jugador.recibir_dano(25, -1 if jugador.mirando_derecha else 1, sistema_particulas)
                jugador.rect.topleft = jugador.punto_reaparicion
                jugador.vx = 0
                jugador.vy = 0

        if jugador.rect.top > MUNDO_ALTO + 50:
            jugador.reaparecer()

        # Actualizar enemigos
        for ene in enemigos:
            ene.actualizar(dt, jugador, sistema_particulas)

        # Actualizar cámara
        camara.seguir(jugador.rect)

        # Actualizar orbes
        for orbe in orbes:
            if orbe.actualizar(dt, jugador, sistema_particulas):
                orbes_recolectados += 1

        # Actualizar partículas
        sistema_particulas.actualizar(dt)

        # RENDERIZADO
        dibujar_fondo_parallax(pantalla, camara)
        dibujar_plataformas_y_pinchos(pantalla, plataformas, pinchos, camara)

        for orbe in orbes:
            orbe.dibujar(pantalla, camara)

        for ene in enemigos:
            ene.dibujar(pantalla, camara)

        sistema_particulas.dibujar(pantalla, camara)
        jugador.dibujar(pantalla, camara)
        dibujar_hud(pantalla, jugador, orbes_recolectados, total_orbes, camara, fuente, fuente_titulos)

        if orbes_recolectados == total_orbes:
            txt_win = fuente_victoria.render("¡ZONA EXPLORADA AL 100%!", True, COLOR_ORO)
            rect_win = txt_win.get_rect(center=(ANCHO_PANTALLA // 2, 70))
            pygame.draw.rect(pantalla, (10, 15, 25), rect_win.inflate(30, 14), border_radius=8)
            pygame.draw.rect(pantalla, COLOR_ORO, rect_win.inflate(30, 14), 2, border_radius=8)
            pantalla.blit(txt_win, rect_win)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
