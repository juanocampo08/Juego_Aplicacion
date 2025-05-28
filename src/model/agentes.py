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

    def update_effects(self):
        self.pulse_phase += 0.1
        self.shield_rotation += 2

        self.trail_positions.pop()
        self.trail_positions.insert(0, (self.x, self.y))

    def dibujar(self, superficie):
        if not self.esta_vivo:
            return

        center = (int(self.x), int(self.y))
        tiempo_actual = pygame.time.get_ticks()
        dano_reciente = (tiempo_actual - self.tiempo_dano) < 200

        for i, pos in enumerate(self.trail_positions[1:]):
            alpha = int(100 * (1 - i / len(self.trail_positions)))
            trail_surface = pygame.Surface((self.radio, self.radio), pygame.SRCALPHA)
            trail_color = (*self.color[:3], alpha)
            pygame.draw.circle(trail_surface, trail_color, (self.radio // 2, self.radio // 2), max(1, self.radio - i * 2))
            superficie.blit(trail_surface, (int(pos[0] - self.radio // 2), int(pos[1] - self.radio // 2)))

        pulse_intensity = (math.sin(self.pulse_phase) + 1) / 2
        glow_radius = int(self.radio + 10 + pulse_intensity * 8)

        if dano_reciente and (tiempo_actual // 50) % 2:
            glow_color = (255, 100, 100)
        else:
            glow_color = self.glow_color
        VisualEffects.draw_glow_circle(superficie, glow_color, center, self.radio, glow_radius)


        if self.agent_type == "player":
            self._draw_player(superficie, center)
        elif self.agent_type == "enemy":
            self._draw_enemy(superficie, center)
            self._draw_health_bar(superficie, center)
        else:
            self._draw_basic(superficie, center)

    def _draw_health_bar(self, superficie, center):
        if self.vida_actual == self.vida_maxima:
            return

        bar_width = self.radio * 2 + 10
        bar_height = 4

        bar_x = center[0] - bar_width // 2
        bar_y = center[1] - self.radio - 30

        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(superficie, (50, 50, 50), bg_rect)

        vida_porcentaje = self.vida_actual / self.vida_maxima
        vida_width = int(bar_width * vida_porcentaje)

        if vida_width > 0:
            if vida_porcentaje > 0.6:
                color_vida = (0, 255, 0)  # Verde
            elif vida_porcentaje > 0.3:
                color_vida = (255, 255, 0)  # Amarillo
            else:
                color_vida = (255, 0, 0)  # Rojo

            vida_rect = pygame.Rect(bar_x, bar_y, vida_width, bar_height)
            pygame.draw.rect(superficie, color_vida, vida_rect)

        pygame.draw.rect(superficie, (150, 150, 150), bg_rect, 1)

    def _calculate_core_color(self):
        r, g, b = self.color[:3]
        return (min(255, r + 100), min(255, g + 100), min(255, b + 100))





