"""
Punto de Entrada Principal del Juego Metroidvania 2D.
Integra y coordina todos los módulos:
- config.py          -> Parámetros de pantalla, mundo y colores.
- personaje.py       -> Lógica del jugador, movimiento, saltos, ataque y animaciones.
- sprites_espada.py  -> Generador de sprites del tajo de la espada (Slash VFX).
- escenario.py       -> Plataformas (sólidas y flotantes/one-way), pinchos y orbes.
- enemigos.py        -> Patrullaje de criaturas, daño e inteligencia artificial.
- camara.py          -> Desplazamiento cinemático de la vista.
- particulas.py      -> Efectos visuales de polvo, impactos y estelas.
- interfaz.py        -> HUD, vida, estamina de dash y mini-mapa.
- audio.py           -> Efectos sonoros retro en tiempo real.
"""

import os
import sys
import pygame

from config import ANCHO_PANTALLA, ALTO_PANTALLA, FPS, MUNDO_ANCHO, MUNDO_ALTO, COLOR_ORO
from camara import Camara
from particulas import SistemaParticulas
from personaje import Jugador
from sprites_espada import crear_sprites_espada
from escenario import construir_mundo, dibujar_fondo_parallax, dibujar_plataformas_y_pinchos
from interfaz import dibujar_hud, dibujar_game_over
from audio import GestorAudio


def cargar_frames_jugador():
    """Carga los fotogramas de movimiento (caminar/idle/salto) del spritesheet de 256x256."""
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


def cargar_frames_ataque():
    """Carga los fotogramas del spritesheet de ataque del jugador (spriteJugadorAtaque.png)."""
    posibles_rutas = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ImagenesJuego", "spriteJugadorAtaque.png"),
        os.path.join("ImagenesJuego", "spriteJugadorAtaque.png"),
        os.path.join("..", "proyecto", "ImagenesJuego", "spriteJugadorAtaque.png")
    ]
    ruta_encontrada = None
    for r in posibles_rutas:
        if os.path.exists(r):
            ruta_encontrada = r
            break

    if not ruta_encontrada:
        print(f"Aviso: No se encontró spriteJugadorAtaque.png en {posibles_rutas}")
        return []

    spritesheet = pygame.image.load(ruta_encontrada).convert_alpha()
    frame_ancho = 64
    frame_alto = 64
    escala = 2
    frames_atk = []

    # La hoja de ataque es de 128x128 con 4 cuadros (2x2 de 64x64)
    for fila in range(2):
        for col in range(2):
            rect = pygame.Rect(col * frame_ancho, fila * frame_alto, frame_ancho, frame_alto)
            sub = spritesheet.subsurface(rect)
            if sub.get_bounding_rect().width > 0:
                frame_escalado = pygame.transform.scale(sub, (frame_ancho * escala, frame_alto * escala))
                frames_atk.append(frame_escalado)

    return frames_atk


def main():
    pygame.init()
    pygame.display.set_caption("Metroidvania 2D - Combate Fluido y Espada")
    pantalla = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))
    reloj = pygame.time.Clock()

    fuente = pygame.font.Font(None, 20)
    fuente_titulos = pygame.font.Font(None, 26)
    fuente_victoria = pygame.font.Font(None, 46)
    fuente_gameover = pygame.font.Font(None, 64)
    fuente_media = pygame.font.Font(None, 28)

    # Cargar recursos gráficos y de audio
    frames_jugador = cargar_frames_jugador()
    frames_ataque = cargar_frames_ataque()
    frames_espada = crear_sprites_espada()
    # Estado del Mundo y Carga de la Sala Inicial
    sala_actual = 1
    plataformas, pinchos, enemigos, orbes, portales, monedas = construir_mundo(sala_actual)

    # Instanciar personaje con soporte completo de animación de ataque y espada
    jugador = Jugador(120, 600, frames_jugador, frames_ataque=frames_ataque, frames_espada=frames_espada)
    camara = Camara(ANCHO_PANTALLA, ALTO_PANTALLA, MUNDO_ANCHO, MUNDO_ALTO)
    sistema_particulas = SistemaParticulas()
    audio = GestorAudio()

    orbes_recolectados = 0
    total_orbes = len(orbes)
    monedas_recolectadas = 0
    ejecutando = True
    boton_reintentar_rect = None

    # Efecto de fundido entre salas (Screen Fade)
    alfa_fade = 0.0
    cambiando_sala = False
    info_transicion = None

    def reiniciar_todo():
        nonlocal orbes_recolectados, plataformas, pinchos, enemigos, orbes, portales, sala_actual, cambiando_sala, alfa_fade
        sala_actual = 1
        cambiando_sala = False
        alfa_fade = 0.0
        jugador.reiniciar_partida()
        plataformas, pinchos, enemigos, orbes, portales = construir_mundo(sala_actual)
        orbes_recolectados = 0
        total_orbes_mapa = len(orbes)
        camara.seguir(jugador.rect, suavizado=1.0)
        sistema_particulas.particulas.clear()
        sistema_particulas.estelas_dash.clear()

    while ejecutando:
        dt = reloj.tick(FPS) / 1000.0
        dt = min(dt, 0.05)
        teclas = pygame.key.get_pressed()
        pos_mouse = pygame.mouse.get_pos()
        en_game_over = (jugador.vida <= 0)

        # 1. GESTIÓN DE EVENTOS
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                # Clic en el botón de volver a jugar
                if en_game_over and boton_reintentar_rect and boton_reintentar_rect.collidepoint(evento.pos):
                    reiniciar_todo()

            elif evento.type == pygame.KEYDOWN:
                # Si está en Game Over, permite reiniciar con ENTER, R o ESPACIO
                if en_game_over:
                    if evento.key in (pygame.K_RETURN, pygame.K_r, pygame.K_SPACE):
                        reiniciar_todo()
                    continue

                # Salto y descenso de plataformas
                if evento.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    jugador.intentar_saltar(teclas, sistema_particulas, audio=audio)
                # Ataque con espada (J o X) tanto en tierra como en el aire, apuntando arriba con Flecha Arriba / W
                elif evento.key in (pygame.K_j, pygame.K_x):
                    jugador.intentar_atacar(teclas, sistema_particulas, audio=audio)
                # Esquiva rápida / Dash (Shift o K)
                elif evento.key in (pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_k):
                    jugador.intentar_dash(sistema_particulas, audio=audio)
                # Reinicio manual opcional
                elif evento.key == pygame.K_r:
                    reiniciar_todo()

            elif evento.type == pygame.KEYUP:
                if not en_game_over and evento.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    jugador.cortar_salto()

        # 2. ACTUALIZACIÓN DE ESTADOS Y FÍSICA (Solo si sigue vivo)
        if not en_game_over:
            jugador.procesar_entrada(teclas, dt, sistema_particulas)
            jugador.actualizar(dt, plataformas, sistema_particulas, teclas)

            # Colisión con pinchos del abismo
            for pincho in pinchos:
                if jugador.rect.colliderect(pincho):
                    jugador.recibir_dano(25, -1 if jugador.mirando_derecha else 1, sistema_particulas, audio=audio)
                    if jugador.vida > 0:
                        jugador.rect.topleft = jugador.punto_reaparicion
                        jugador.vx = 0
                        jugador.vy = 0

            # Caída al vacío fuera del mapa
            if jugador.rect.top > MUNDO_ALTO + 50:
                jugador.recibir_dano(35, 0, sistema_particulas, audio=audio)
                if jugador.vida > 0:
                    jugador.rect.topleft = jugador.punto_reaparicion
                    jugador.vx = 0
                    jugador.vy = 0

            # Verificación de Umbral / Pared de Cambio de Mapa (Metroidvania door)
            if not cambiando_sala:
                for portal in portales:
                    if jugador.rect.colliderect(portal.rect):
                        cambiando_sala = True
                        info_transicion = portal
                        audio.reproducir("dash")
                        break

            # Actualizar portales
            for portal in portales:
                portal.actualizar(dt)

            # Transición suave entre mapas (Fade In / Fade Out)
            if cambiando_sala and info_transicion:
                alfa_fade += 600 * dt
                if alfa_fade >= 255:
                    # Cambiar al destino
                    sala_actual = info_transicion.destino_mapa
                    plataformas, pinchos, enemigos, orbes, portales = construir_mundo(sala_actual)
                    jugador.rect.x = info_transicion.spawn_x
                    jugador.rect.y = info_transicion.spawn_y
                    jugador.punto_reaparicion = (info_transicion.spawn_x, info_transicion.spawn_y)
                    jugador.vx = 0
                    jugador.vy = 0
                    camara.seguir(jugador.rect, suavizado=1.0)
                    cambiando_sala = False
                    info_transicion = None
            elif alfa_fade > 0:
                alfa_fade = max(0.0, alfa_fade - 500 * dt)

            # Actualizar enemigos
            for ene in enemigos:
                ene.actualizar(dt, jugador, sistema_particulas)

            # Seguimiento de cámara
            camara.seguir(jugador.rect)

            # Actualizar orbes
            for orbe in orbes:
                if orbe.actualizar(dt, jugador, sistema_particulas):
                    orbes_recolectados += 1
                    audio.reproducir("reliquia")

        # Actualizar partículas y estelas
        sistema_particulas.actualizar(dt)

        # 3. RENDERIZADO
        dibujar_fondo_parallax(pantalla, camara, id_mapa=sala_actual)
        dibujar_plataformas_y_pinchos(pantalla, plataformas, pinchos, camara)

        # Portales de paso entre paredes
        for portal in portales:
            portal.dibujar(pantalla, camara)

        for orbe in orbes:
            orbe.dibujar(pantalla, camara)

        for ene in enemigos:
            ene.dibujar(pantalla, camara)

        sistema_particulas.dibujar(pantalla, camara)
        if not en_game_over:
            jugador.dibujar(pantalla, camara)

        nombre_zona = "Cavernas Subterráneas" if sala_actual == 1 else "Santuario Sagrado"
        dibujar_hud(pantalla, jugador, orbes_recolectados, total_orbes, camara, fuente, fuente_titulos, nombre_sala=nombre_zona)

        # Cortina de transición entre mapas (Metroidvania room change fade)
        if alfa_fade > 0:
            surf_fade = pygame.Surface((ANCHO_PANTALLA, ALTO_PANTALLA))
            surf_fade.fill((0, 0, 0))
            surf_fade.set_alpha(int(min(255, alfa_fade)))
            pantalla.blit(surf_fade, (0, 0))

        # Pantalla de GAME OVER cuando la vida es <= 0
        if en_game_over:
            boton_reintentar_rect = dibujar_game_over(pantalla, fuente_gameover, fuente_media, pos_mouse)

        # Victoria al explorar 100%
        elif orbes_recolectados == total_orbes:
            txt_win = fuente_victoria.render("¡ZONA EXPLORADA AL 100%!", True, COLOR_ORO)
            rect_win = txt_win.get_rect(center=(ANCHO_PANTALLA // 2, 70))
            pygame.draw.rect(pantalla, (10, 15, 25), rect_win.inflate(30, 14), border_radius=8)
            pygame.draw.rect(pantalla, COLOR_ORO, rect_win.inflate(30, 14), 2, border_radius=8)
            pantalla.blit(txt_win, rect_win)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
