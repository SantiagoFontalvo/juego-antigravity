"""
Módulo de Sonido y Efectos de Audio Sintetizados en Tiempo Real.
Genera efectos sonoros retro estilo 16-bit utilizando pygame.mixer y numpy/math,
sin requerir archivos .wav o .mp3 externos.
"""

import math
import pygame

class GestorAudio:
    def __init__(self):
        self.disponible = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.disponible = True
            self.sonidos = {
                "salto": self._generar_salto(),
                "doble_salto": self._generar_doble_salto(),
                "dash": self._generar_dash(),
                "ataque": self._generar_ataque(),
                "golpe": self._generar_golpe(),
                "reliquia": self._generar_reliquia(),
                "herido": self._generar_herido()
            }
        except Exception as e:
            print(f"Aviso: Audio no disponible ({e}), el juego continuará sin sonido.")

    def reproducir(self, nombre):
        if self.disponible and nombre in self.sonidos and self.sonidos[nombre]:
            try:
                self.sonidos[nombre].play()
            except Exception:
                pass

    def _crear_sound(self, muestras):
        bytes_data = bytearray()
        for s in muestras:
            val = int(max(-32767, min(32767, s)))
            bytes_data.extend(val.to_bytes(2, byteorder="little", signed=True))
            bytes_data.extend(val.to_bytes(2, byteorder="little", signed=True))  # Estéreo
        return pygame.mixer.Sound(buffer=bytes(bytes_data))

    def _generar_salto(self):
        # Tono ascendente rápido (250Hz -> 600Hz)
        sr = 22050
        dur = 0.14
        num_muestras = int(sr * dur)
        muestras = []
        fase = 0.0
        for i in range(num_muestras):
            prog = i / num_muestras
            freq = 250 + 350 * prog
            fase += 2 * math.pi * freq / sr
            amp = (1.0 - prog) * 12000
            muestras.append(amp * math.sin(fase))
        return self._crear_sound(muestras)

    def _generar_doble_salto(self):
        # Doble chirp armónico agudo (400Hz -> 850Hz)
        sr = 22050
        dur = 0.16
        num_muestras = int(sr * dur)
        muestras = []
        fase = 0.0
        for i in range(num_muestras):
            prog = i / num_muestras
            freq = 400 + 450 * (prog ** 0.8)
            fase += 2 * math.pi * freq / sr
            amp = (1.0 - prog) * 11000
            muestras.append(amp * (0.8 * math.sin(fase) + 0.2 * math.sin(fase * 2)))
        return self._crear_sound(muestras)

    def _generar_dash(self):
        # Ruido de ráfaga de viento / aire
        import random
        sr = 22050
        dur = 0.18
        num_muestras = int(sr * dur)
        muestras = []
        for i in range(num_muestras):
            prog = i / num_muestras
            amp = math.sin(prog * math.pi) * 9000
            muestras.append(random.uniform(-1, 1) * amp)
        return self._crear_sound(muestras)

    def _generar_ataque(self):
        # Sonido de espada cortando el aire (whoosh metálico)
        sr = 22050
        dur = 0.12
        num_muestras = int(sr * dur)
        muestras = []
        fase = 0.0
        for i in range(num_muestras):
            prog = i / num_muestras
            freq = 900 - 650 * prog
            fase += 2 * math.pi * freq / sr
            amp = (1.0 - prog ** 0.5) * 14000
            muestras.append(amp * math.sin(fase))
        return self._crear_sound(muestras)

    def _generar_golpe(self):
        # Impacto sordo con chasquido metálico
        import random
        sr = 22050
        dur = 0.10
        num_muestras = int(sr * dur)
        muestras = []
        fase = 0.0
        for i in range(num_muestras):
            prog = i / num_muestras
            fase += 2 * math.pi * 120 / sr
            amp = (1.0 - prog) * 16000
            ruido = random.uniform(-0.5, 0.5) * amp
            muestras.append(amp * math.sin(fase) + ruido)
        return self._crear_sound(muestras)

    def _generar_reliquia(self):
        # Arpegio brillante mágico (Do - Mi - Sol - Do agudo)
        sr = 22050
        dur = 0.35
        num_muestras = int(sr * dur)
        muestras = []
        fase = 0.0
        notas = [523.25, 659.25, 783.99, 1046.50]
        for i in range(num_muestras):
            prog = i / num_muestras
            idx_nota = min(int(prog * 4), 3)
            freq = notas[idx_nota]
            fase += 2 * math.pi * freq / sr
            amp = (1.0 - prog) * 13000
            muestras.append(amp * math.sin(fase))
        return self._crear_sound(muestras)

    def _generar_herido(self):
        # Golpe descendente grave de daño
        sr = 22050
        dur = 0.22
        num_muestras = int(sr * dur)
        muestras = []
        fase = 0.0
        for i in range(num_muestras):
            prog = i / num_muestras
            freq = 220 - 140 * prog
            fase += 2 * math.pi * freq / sr
            amp = (1.0 - prog) * 17000
            muestras.append(amp * math.sin(fase))
        return self._crear_sound(muestras)

