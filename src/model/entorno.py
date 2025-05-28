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
