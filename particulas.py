"""
Sistema de efectos visuales: partículas y estelas de dash.
"""

import math
import random
import pygame

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

