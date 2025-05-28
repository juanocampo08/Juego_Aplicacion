import pygame
import math
import sys

sys.path.append("src")

from utils.visual_effects import VisualEffects

class Proyectil:
    def __init__(self, x, y, target_x, target_y, velocidad=8):

        self.x = x
        self.y = y
        self.velocidad = velocidad
        self.radio = 3
        self.activo = True

        dx = target_x - x
        dy = target_y - y
        distancia = math.hypot(dx, dy)

        if distancia > 0:
            self.vel_x = (dx / distancia) * velocidad
            self.vel_y = (dy / distancia) * velocidad
        else:
            self.vel_x = 0
            self.vel_y = 0

        self.trail_positions = [(x, y)] * 3
        self.pulse_phase = 0

    def update(self, ancho_pantalla, alto_pantalla, obstaculos = []):
        if not self.activo:
            return

        self.x += self.vel_x
        self.y += self.vel_y

        proyectil_rect = pygame.Rect(int(self.x - self.radio), int(self.y - self.radio), self.radio * 2, self.radio * 2)
        for obstaculo in obstaculos:
            if proyectil_rect.colliderect(obstaculo.rect):
                self.activo = False
                return

        self.pulse_phase += 0.3
        self.trail_positions.pop()
        self.trail_positions.insert(0, (self.x, self.y))

        if (self.x < 0 or self.x > ancho_pantalla or
                self.y < 0 or self.y > alto_pantalla):
            self.activo = False

