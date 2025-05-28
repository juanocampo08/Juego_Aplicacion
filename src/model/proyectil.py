import pygame
import math
import sys

sys.path.append("src")

from src.utils.visual_effects import VisualEffects

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

    def dibujar(self, superficie):
        if not self.activo:
            return

        for i, pos in enumerate(self.trail_positions[1:]):
            alpha = int(150 * (1 - i / len(self.trail_positions)))
            trail_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
            trail_color = (0, 255, 255, alpha)
            pygame.draw.circle(trail_surface, trail_color, (3, 3), max(1, 3 - i))
            superficie.blit(trail_surface, (int(pos[0] - 3), int(pos[1] - 3)))

        center = (int(self.x), int(self.y))
        pulse_intensity = (math.sin(self.pulse_phase) + 1) / 2
        glow_radius = int(3 + pulse_intensity * 4)

        VisualEffects.draw_glow_circle(superficie, (0, 255, 255), center, self.radio, glow_radius)
        pygame.draw.circle(superficie, (255, 255, 255), center, 1)

    def colisiona_con(self, agente):
        if not self.activo:
            return False

        distancia = math.hypot(self.x - agente.x, self.y - agente.y)
        return distancia < (self.radio + agente.radio)
