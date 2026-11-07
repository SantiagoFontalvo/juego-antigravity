"""
Módulo del Personaje / Jugador.
Controla movimiento, salto, doble salto, plataformas flotantes, ataque y animaciones.
Integra spritesheets de personaje y sprites dedicados de corte de espada (Slash VFX).
"""

import math
import random
import pygame

class Jugador:
    def __init__(self, x, y, frames_movimiento, frames_ataque=None, frames_espada=None):
        self.frames = frames_movimiento

        self.anim_idle = frames_movimiento[0:4]
        self.anim_walk = frames_movimiento[4:12]
        self.frame_salto = frames_movimiento[12]
        self.frame_caida = frames_movimiento[13] if len(frames_movimiento) > 13 else frames_movimiento[12]

        # Sprites de ataque del jugador
        if frames_ataque and len(frames_ataque) > 0:
            self.anim_ataque = frames_ataque
        else:
            self.anim_ataque = self.anim_walk[0:4]

        # Sprites del efecto de corte de la espada (Slash VFX)
        if frames_espada and len(frames_espada) > 0:
            self.frames_espada = frames_espada
        else:
            self.frames_espada = self._generar_sprites_espada_default()

        # Dimensiones de colisión precisas
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

        # Temporizador para bajar plataformas atravesables con [Abajo + Salto]
        self.tiempo_bajar_plataforma = 0.0

        # Dash
        self.cooldown_dash = 0.0
        self.tiempo_dash = 0.0
        self.velocidad_dash = 780.0
        self.esta_haciendo_dash = False

        # Ataque
        self.duracion_total_ataque = 0.28  # Duración fluida del golpe
        self.tiempo_ataque = 0.0
        self.cooldown_ataque = 0.0
        self.hitbox_ataque = pygame.Rect(0, 0, 0, 0)
        self.ha_golpeado_en_este_ataque = False
        self.direccion_ataque = "horizontal"  # 'horizontal' o 'arriba'

        # Sistema de Vida
        self.vida_max = 100
        self.vida = 100
        self.tiempo_invulnerabilidad = 0.0
        self.punto_reaparicion = (x, y)

        # Animación
        self.estado_anim = "idle"
        self.indice_anim = 0.0

    def _generar_sprites_espada_default(self):
        """Genera sprites propios con efectos de corte de energía mágica y estela."""
        frames_slash = []

        # Frame 0: Arco inicial cargado
        s0 = pygame.Surface((128, 128), pygame.SRCALPHA)
        pygame.draw.arc(s0, (100, 200, 255, 180), pygame.Rect(35, 15, 80, 80), 0.6, 2.3, 5)
        pygame.draw.arc(s0, (255, 255, 255, 240), pygame.Rect(37, 17, 76, 76), 0.8, 2.1, 2)
        frames_slash.append(s0)

        # Frame 1: Corte amplio con media luna mágica
        s1 = pygame.Surface((128, 128), pygame.SRCALPHA)
        pygame.draw.arc(s1, (60, 160, 255, 210), pygame.Rect(30, 10, 92, 92), -0.5, 1.9, 7)
        pygame.draw.arc(s1, (180, 240, 255, 255), pygame.Rect(32, 12, 88, 88), -0.3, 1.7, 4)
        pygame.draw.arc(s1, (255, 255, 255, 255), pygame.Rect(34, 14, 84, 84), -0.1, 1.5, 2)
        puntos_corte = [(72, 15), (116, 42), (112, 75), (74, 80), (96, 58)]
        pygame.draw.polygon(s1, (140, 225, 255, 170), puntos_corte)
        frames_slash.append(s1)

        # Frame 2: Expansión frontal e impacto luminoso
        s2 = pygame.Surface((128, 128), pygame.SRCALPHA)
        pygame.draw.arc(s2, (80, 180, 255, 230), pygame.Rect(26, 20, 98, 86), -1.1, 0.9, 8)
        pygame.draw.arc(s2, (210, 250, 255, 255), pygame.Rect(28, 22, 94, 82), -0.9, 0.7, 4)
        pygame.draw.arc(s2, (255, 255, 255, 255), pygame.Rect(30, 24, 90, 78), -0.7, 0.5, 2)
        # Chispas afiladas
        pygame.draw.line(s2, (255, 255, 255), (105, 52), (126, 44), 3)
        pygame.draw.line(s2, (180, 230, 255), (110, 68), (127, 74), 2)
        frames_slash.append(s2)

        # Frame 3: Disipación sutil de la energía
        s3 = pygame.Surface((128, 128), pygame.SRCALPHA)
        pygame.draw.arc(s3, (120, 200, 255, 120), pygame.Rect(38, 30, 84, 72), -1.2, 0.2, 4)
        pygame.draw.arc(s3, (255, 255, 255, 180), pygame.Rect(40, 32, 80, 68), -1.0, 0.0, 2)
        frames_slash.append(s3)

        return frames_slash

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

        # Movimiento horizontal (si está atacando en tierra, reduce ligeramente la velocidad para mayor firmeza)
        factor_velocidad = 0.75 if (self.tiempo_ataque > 0 and self.en_suelo) else 1.0

        mover_izq = teclas[pygame.K_LEFT] or teclas[pygame.K_a]
        mover_der = teclas[pygame.K_RIGHT] or teclas[pygame.K_d]

        if mover_izq and not mover_der:
            self.vx = -self.velocidad_caminar * factor_velocidad
            # Solo gira si no está en medio del corte inicial
            if self.tiempo_ataque <= 0.12:
                self.mirando_derecha = False
        elif mover_der and not mover_izq:
            self.vx = self.velocidad_caminar * factor_velocidad
            if self.tiempo_ataque <= 0.12:
                self.mirando_derecha = True
        else:
            self.vx = 0.0

        if self.tiempo_buffer_salto > 0:
            self.tiempo_buffer_salto -= dt
        if self.tiempo_coyote > 0:
            self.tiempo_coyote -= dt

    def intentar_saltar(self, teclas, sistema_particulas, audio=None):
        if self.esta_haciendo_dash:
            return

        presiona_abajo = teclas[pygame.K_DOWN] or teclas[pygame.K_s]
        if presiona_abajo and self.en_suelo:
            self.tiempo_bajar_plataforma = 0.22
            self.rect.y += 4
            self.vy = 120.0
            self.en_suelo = False
            return

        self.tiempo_buffer_salto = 0.15
        if self.en_suelo or self.tiempo_coyote > 0:
            self.ejecutar_salto(sistema_particulas, es_doble=False, audio=audio)
            self.tiempo_buffer_salto = 0.0
            self.tiempo_coyote = 0.0
        elif self.puede_doble_salto and self.doble_salto_disponible:
            self.ejecutar_salto(sistema_particulas, es_doble=True, audio=audio)
            self.doble_salto_disponible = False
            self.tiempo_buffer_salto = 0.0

    def ejecutar_salto(self, sistema_particulas, es_doble=False, audio=None):
        self.vy = self.fuerza_salto * (0.92 if es_doble else 1.0)
        self.en_suelo = False
        color_part = (120, 240, 255) if es_doble else (210, 220, 240)
        sistema_particulas.emitir_polvo(self.rect.centerx, self.rect.bottom, cantidad=8, color=color_part)
        if audio:
            audio.reproducir("doble_salto" if es_doble else "salto")

    def cortar_salto(self):
        if self.vy < -150:
            self.vy = -150

    def intentar_dash(self, sistema_particulas, audio=None):
        if self.cooldown_dash <= 0 and not self.esta_haciendo_dash:
            self.esta_haciendo_dash = True
            self.tiempo_dash = 0.18
            self.cooldown_dash = 0.70
            sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=10, color=(100, 220, 255))
            if audio:
                audio.reproducir("dash")

    def intentar_atacar(self, teclas, sistema_particulas, audio=None):
        if self.cooldown_ataque <= 0 and self.tiempo_ataque <= 0:
            self.tiempo_ataque = self.duracion_total_ataque
            self.cooldown_ataque = self.duracion_total_ataque + 0.10
            self.ha_golpeado_en_este_ataque = False
            self.estado_anim = "attack"

            # Detectar si apunta hacia arriba con la flecha arriba o la tecla W
            apunta_arriba = teclas[pygame.K_UP] or teclas[pygame.K_w]

            if apunta_arriba:
                self.direccion_ataque = "arriba"
                # Caja de golpe vertical por encima de la cabeza
                ancho_corte = 64
                alto_corte = 68
                self.hitbox_ataque = pygame.Rect(self.rect.centerx - (ancho_corte // 2), self.rect.top - alto_corte + 10, ancho_corte, alto_corte)
            else:
                self.direccion_ataque = "horizontal"
                # Caja de golpe frontal estándar
                ancho_corte = 68
                alto_corte = 55
                if self.mirando_derecha:
                    self.hitbox_ataque = pygame.Rect(self.rect.right - 10, self.rect.centery - 28, ancho_corte, alto_corte)
                else:
                    self.hitbox_ataque = pygame.Rect(self.rect.left - ancho_corte + 10, self.rect.centery - 28, ancho_corte, alto_corte)

            # Efecto de chispas luminosas de desenvaine en el punto de impacto
            sistema_particulas.emitir_chispas_golpe(self.hitbox_ataque.centerx, self.hitbox_ataque.centery, cantidad=6, color=(140, 220, 255))
            if audio:
                audio.reproducir("ataque")

    def recibir_dano(self, cantidad, direccion_golpe, sistema_particulas, audio=None):
        if self.tiempo_invulnerabilidad > 0 or self.vida <= 0:
            return False

        self.vida = max(0, self.vida - cantidad)
        self.tiempo_invulnerabilidad = 0.8
        self.vx = direccion_golpe * 300.0
        self.vy = -350.0
        self.en_suelo = False
        sistema_particulas.emitir_chispas_golpe(self.rect.centerx, self.rect.centery, cantidad=14, color=(255, 60, 60))
        if audio:
            audio.reproducir("herido")

        return True

    def reiniciar_partida(self):
        """Reinicia por completo la salud y posición para una nueva partida tras Game Over."""
        self.rect.topleft = (120, 600)
        self.punto_reaparicion = (120, 600)
        self.vida = self.vida_max
        self.vx = 0.0
        self.vy = 0.0
        self.tiempo_invulnerabilidad = 1.0
        self.tiempo_ataque = 0.0
        self.tiempo_dash = 0.0
        self.cooldown_dash = 0.0
        self.cooldown_ataque = 0.0
        self.estado_anim = "idle"

    def actualizar(self, dt, plataformas, sistema_particulas, teclas):
        if not self.esta_haciendo_dash:
            self.vy += self.gravedad * dt
            if self.vy > self.velocidad_caida_max:
                self.vy = self.velocidad_caida_max

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

        # Actualizar ataque y posición de su hitbox según la dirección
        if self.tiempo_ataque > 0:
            self.tiempo_ataque -= dt
            if self.direccion_ataque == "arriba":
                ancho_corte = 64
                alto_corte = 68
                self.hitbox_ataque.x = self.rect.centerx - (ancho_corte // 2)
                self.hitbox_ataque.y = self.rect.top - alto_corte + 10
            else:
                if self.mirando_derecha:
                    self.hitbox_ataque.x = self.rect.right - 10
                else:
                    self.hitbox_ataque.x = self.rect.left - self.hitbox_ataque.width + 10
                self.hitbox_ataque.y = self.rect.centery - 28

            if self.tiempo_ataque <= 0:
                self.hitbox_ataque = pygame.Rect(0, 0, 0, 0)

        # Partículas de pasos
        if self.en_suelo and abs(self.vx) > 50 and random.random() < 0.25:
            sistema_particulas.emitir_polvo(
                self.rect.centerx - (10 if self.mirando_derecha else -10),
                self.rect.bottom, cantidad=2
            )

        self.actualizar_animacion(dt)

    def resolver_colisiones_horizontal(self, plataformas):
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

            if plat.es_flotante:
                if self.tiempo_bajar_plataforma <= 0 and self.vy >= 0 and prev_bottom <= plat.rect.top + 16:
                    self.rect.bottom = plat.rect.top
                    self.vy = 0
                    self.en_suelo = True
                    if not estaba_en_suelo:
                        sistema_particulas.emitir_polvo(self.rect.centerx, self.rect.bottom, cantidad=6, color=(140, 200, 255))
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
        if self.tiempo_ataque > 0:
            self.estado_anim = "attack"
        elif not self.en_suelo:
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
        if self.estado_anim == "attack":
            # Progreso del ataque de 0.0 a 1.0
            progreso = 1.0 - (self.tiempo_ataque / self.duracion_total_ataque)
            num_frames_atk = len(self.anim_ataque)
            idx = min(int(progreso * num_frames_atk), num_frames_atk - 1)
            img = self.anim_ataque[idx]
        elif self.estado_anim == "jump":
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

        # Dibujar sprite de la espada y el tajo de energía (Slash VFX)
        if self.tiempo_ataque > 0:
            progreso = 1.0 - (self.tiempo_ataque / self.duracion_total_ataque)
            num_espadas = len(self.frames_espada)
            idx_espada = min(int(progreso * num_espadas), num_espadas - 1)
            img_espada = self.frames_espada[idx_espada]

            if self.direccion_ataque == "arriba":
                # Rotar la espada 90 grados hacia arriba
                # Si mira a la izquierda, rotamos en sentido horario (-90); si mira a la derecha, en sentido antihorario (90)
                angulo = 90 if self.mirando_derecha else -90
                img_espada = pygame.transform.rotate(img_espada, angulo)
                espada_x = self.rect.centerx - (img_espada.get_width() // 2)
                espada_y = self.rect.top - img_espada.get_height() + 20
            else:
                # Invertir la espada si mira a la izquierda
                if not self.mirando_derecha:
                    img_espada = pygame.transform.flip(img_espada, True, False)

                # Posicionar el sprite de la espada enfrente del guerrero
                if self.mirando_derecha:
                    espada_x = self.rect.centerx - 15
                else:
                    espada_x = self.rect.centerx - img_espada.get_width() + 15
                espada_y = self.rect.centery - (img_espada.get_height() // 2) - 5

            pos_cam_espada = camara.aplicar_pos(espada_x, espada_y)
            superficie.blit(img_espada, pos_cam_espada)
