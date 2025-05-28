import pygame
import math
import time
import random
import sys

sys.path.append("src")
from utils.visual_effects import VisualEffects

class ObstaculoFuturista:
    def __init__(self, x, y, ancho, alto):

        self.x = x
        self.y = y
        self.ancho = ancho
        self.alto = alto
        # `rect` se utiliza para la detección de colisiones de forma eficiente.
        self.rect = pygame.Rect(x, y, ancho, alto)
        # `energy_pulse` controla la fase de animación para los efectos de energía.
        self.energy_pulse = random.uniform(0, 2 * math.pi)
        # Asigna un tipo de obstáculo aleatorio para variar la apariencia.
        self.obstacle_type = random.choice(["tech", "crystal", "barrier"])

    def update(self):
        self.energy_pulse += 0.05

    def dibujar(self, superficie):
        shadow_rect = pygame.Rect(self.rect.x + 4, self.rect.y + 4, self.rect.width, self.rect.height)
        pygame.draw.rect(superficie, (20, 20, 30), shadow_rect)

        if self.obstacle_type == "tech":
            self._draw_tech_obstacle(superficie)
        elif self.obstacle_type == "crystal":
            self._draw_crystal_obstacle(superficie)
        else:
            self._draw_barrier_obstacle(superficie)
    def _draw_tech_obstacle(self, superficie):
        pygame.draw.rect(superficie, (60, 80, 120), self.rect)

        VisualEffects.draw_tech_border(superficie, self.rect, (100, 150, 200), 2)

        pulse_intensity = (math.sin(self.energy_pulse) + 1) / 2
        energy_color = (int(100 + pulse_intensity * 100), int(150 + pulse_intensity * 50), 200)

        for i in range(3):
            y_pos = self.rect.y + (i + 1) * self.rect.height // 4
            pygame.draw.line(superficie, energy_color,(self.rect.x + 5, y_pos),(self.rect.x + self.rect.width - 5, y_pos), 2)

    def _draw_crystal_obstacle(self, superficie):
        center = self.rect.center

        crystal_points = []
        for i in range(6):
            angle = i * math.pi / 3
            x = center[0] + (self.rect.width // 3) * math.cos(angle)
            y = center[1] + (self.rect.height // 3) * math.sin(angle)
            crystal_points.append((x, y))

        pygame.draw.polygon(superficie, (80, 120, 180), crystal_points)
        pygame.draw.polygon(superficie, (120, 160, 220), crystal_points, 3)

        pulse_intensity = (math.sin(self.energy_pulse * 2) + 1) / 2
        inner_color = (int(150 + pulse_intensity * 105), int(180 + pulse_intensity * 75), 255)
        inner_size = int((self.rect.width // 6) * (0.5 + pulse_intensity * 0.5))
        pygame.draw.circle(superficie, inner_color, center, inner_size)

    def _draw_barrier_obstacle(self, superficie):
        pygame.draw.rect(superficie, (40, 60, 80), self.rect)


        for i in range(5):
            alpha = int(50 + 30 * (math.sin(self.energy_pulse + i * 0.5) + 1) / 2)
            barrier_surface = pygame.Surface((self.rect.width, 4), pygame.SRCALPHA)
            barrier_color = (0, 150, 255, alpha)
            pygame.draw.rect(barrier_surface, barrier_color, (0, 0, self.rect.width, 4))
            y_pos = self.rect.y + i * (self.rect.height // 5)
            superficie.blit(barrier_surface, (self.rect.x, y_pos))

class PowerUpSalud:
    def __init__(self, x, y, duracion=5):
        self.x = x
        self.y = y
        self.radio = 10
        self.tiempo_creacion = time.time()
        self.duracion = duracion
        self.activo = True

    def rect(self):
        return pygame.Rect(self.x - self.radio, self.y - self.radio, self.radio * 2, self.radio * 2)
