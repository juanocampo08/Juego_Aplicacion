import pygame
import math
import random
import sys

sys.path.append("src")


from model.proyectil import Proyectil
from utils.visual_effects import VisualEffects

class Agente:
    def __init__(self, x, y, color, radio = 10, velocidad =  5, agent_type = "basic", vida_maxima = 100):
        self.x = x
        self.y = y
        self.color = color
        self.radio = radio
        self.velocidad = velocidad
        self.agent_type = agent_type

        self.vida_maxima = vida_maxima
        self.vida_actual = vida_maxima
        self.esta_vivo = True
        self.tiempo_dano = 0

        self.pulse_phase = random.uniform(0, 2 * math.pi)
        self.trail_positions = [(x, y)] * 5
        self.energy_level = 1.0
        self.shield_rotation = 0

        self.glow_color = self._calculate_glow_color()
        self.core_color = self._calculate_core_color()

    def recibir_dano(self, cantidad = 20):
        if not self.esta_vivo:
            return False
        if pygame.time.get_ticks() - self.tiempo_dano < 500:
            return None

        self.vida_actual -= cantidad
        self.tiempo_dano = pygame.time.get_ticks()

        if self.vida_actual <= 0:
            self.vida_actual = 0
            self.esta_vivo = False
            return True
        return False





