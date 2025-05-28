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

