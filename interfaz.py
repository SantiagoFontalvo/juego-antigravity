"""
Módulo de Interfaz de Usuario (HUD) y Mini-mapa en tiempo real.
"""

import pygame
from config import (
    ANCHO_PANTALLA, ALTO_PANTALLA, MUNDO_ANCHO, MUNDO_ALTO,
    COLOR_VIDA, COLOR_ESTAMINA, COLOR_ORO
)

def dibujar_hud(superficie, jugador, orbes_obtenidos, total_orbes, camara, fuente, fuente_titulos, nombre_sala="Cavernas"):
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

    txt_controles = fuente.render(f"Zona: {nombre_sala}  |  A/D: Mover | W: Saltar | J: Espada", True, (170, 185, 210))
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

    # Dibujar viewport de la cámara dentro del marco del minimapa con recorte (clipping)
    cam_vx = mapa_x + int(camara.x * escala_mx)
    cam_vy = mapa_y + int(camara.y * escala_my)
    cam_vw = int(ANCHO_PANTALLA * escala_mx)
    cam_vh = int(ALTO_PANTALLA * escala_my)

    rect_minimapa = pygame.Rect(mapa_x, mapa_y, mapa_w, mapa_h)
    rect_cam_mapa = pygame.Rect(cam_vx, cam_vy, cam_vw, cam_vh).clamp(rect_minimapa)
    pygame.draw.rect(superficie, (40, 55, 80), rect_cam_mapa)

    # Posición del jugador dentro del minimapa
    jugador_mx = max(mapa_x + 3, min(mapa_x + int(jugador.rect.centerx * escala_mx), mapa_x + mapa_w - 3))
    jugador_my = max(mapa_y + 3, min(mapa_y + int(jugador.rect.centery * escala_my), mapa_y + mapa_h - 3))
    pygame.draw.circle(superficie, (255, 70, 70), (jugador_mx, jugador_my), 3)


def dibujar_game_over(superficie, fuente_grande, fuente_media, pos_mouse=None):
    """
    Renderiza la pantalla oscura de Game Over con opciones interactivas de reintento.
    Retorna el pygame.Rect del botón de reintentar para detección de clic.
    """
    # Capa de oscurecimiento translúcida con tinte rojizo gótico
    overlay = pygame.Surface((ANCHO_PANTALLA, ALTO_PANTALLA), pygame.SRCALPHA)
    overlay.fill((10, 4, 8, 205))
    superficie.blit(overlay, (0, 0))

    # Título principal de Game Over
    txt_titulo = fuente_grande.render("GAME OVER", True, (240, 50, 60))
    rect_titulo = txt_titulo.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2 - 80))
    # Sombra del texto
    txt_sombra = fuente_grande.render("GAME OVER", True, (0, 0, 0))
    superficie.blit(txt_sombra, (rect_titulo.x + 3, rect_titulo.y + 3))
    superficie.blit(txt_titulo, rect_titulo)

    # Subtítulo explicativo
    txt_sub = fuente_media.render("Has caído en las ruinas...", True, (200, 205, 220))
    rect_sub = txt_sub.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2 - 25))
    superficie.blit(txt_sub, rect_sub)

    # Botón [VOLVER A JUGAR]
    btn_w = 260
    btn_h = 52
    btn_rect = pygame.Rect((ANCHO_PANTALLA - btn_w) // 2, ALTO_PANTALLA // 2 + 30, btn_w, btn_h)

    # Resaltar si el cursor está encima
    hover = btn_rect.collidepoint(pos_mouse) if pos_mouse else False
    color_btn = (180, 45, 55) if hover else (70, 30, 40)
    color_borde = (255, 120, 130) if hover else (180, 70, 80)

    pygame.draw.rect(superficie, color_btn, btn_rect, border_radius=8)
    pygame.draw.rect(superficie, color_borde, btn_rect, 2, border_radius=8)

    txt_btn = fuente_media.render("Volver a Jugar [ENTER]", True, (255, 255, 255))
    rect_txt_btn = txt_btn.get_rect(center=btn_rect.center)
    superficie.blit(txt_btn, rect_txt_btn)

    txt_r = fuente_media.render("o presiona la tecla [R]", True, (160, 170, 185))
    rect_r = txt_r.get_rect(center=(ANCHO_PANTALLA // 2, ALTO_PANTALLA // 2 + 105))
    superficie.blit(txt_r, rect_r)

    return btn_rect


def dibujar_barra_jefe(superficie, jefe, fuente_titulos):
    """
    Dibuja una barra de salud cinematográfica para el Jefe en la parte inferior de la pantalla.
    """
    if not jefe or not jefe.activo or not jefe.vivo:
        return

    ancho_barra = 460
    alto_barra = 16
    bx = (ANCHO_PANTALLA - ancho_barra) // 2
    by = ALTO_PANTALLA - 45

    # Marco de fondo
    pygame.draw.rect(superficie, (15, 10, 18), (bx - 10, by - 26, ancho_barra + 20, alto_barra + 36), border_radius=6)
    pygame.draw.rect(superficie, (180, 50, 70), (bx - 10, by - 26, ancho_barra + 20, alto_barra + 36), 2, border_radius=6)

    # Nombre del Jefe
    txt_boss = fuente_titulos.render("GUARDIÁN DE LAS RUINAS", True, (255, 100, 110))
    rect_txt = txt_boss.get_rect(center=(ANCHO_PANTALLA // 2, by - 14))
    superficie.blit(txt_boss, rect_txt)

    # Fondo de la barra
    pygame.draw.rect(superficie, (45, 20, 28), (bx, by, ancho_barra, alto_barra), border_radius=3)

    # Relleno de vida del jefe
    factor_vida = max(0.0, jefe.vida / jefe.vida_max)
    ancho_actual = int(ancho_barra * factor_vida)
    if ancho_actual > 0:
        pygame.draw.rect(superficie, (220, 40, 55), (bx, by, ancho_actual, alto_barra), border_radius=3)
        # Brillo superior
        pygame.draw.line(superficie, (255, 140, 160), (bx, by + 1), (bx + ancho_actual, by + 1), 2)


