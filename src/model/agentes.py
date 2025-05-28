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

    def _calculate_glow_color(self):
        r, g, b = self.color[:3]
        return (min(255, r + 50), min(255, g + 50), min(255, b + 50))

    def _draw_basic(self, superficie, center):
        pygame.draw.circle(superficie, self.color, center, self.radio)
        pygame.draw.circle(superficie, self.core_color, center, self.radio - 3)

    def _draw_player(self, superficie, center):
        shield_points = []
        for i in range(8):
            angle = (i * math.pi / 4) + math.radians(self.shield_rotation)
            x = center[0] + (self.radio + 8) * math.cos(angle)
            y = center[1] + (self.radio + 8) * math.sin(angle)
            shield_points.append((x, y))

        for i in range(0, len(shield_points), 2):
            start = shield_points[i]
            end = shield_points[(i + 1) % len(shield_points)]
            pygame.draw.line(superficie, (0, 150, 255), start, end, 3)  # Azul claro para el escudo.

        VisualEffects.draw_hexagon(superficie, (0, 100, 255), center, self.radio - 2)  # Hexágono exterior
        VisualEffects.draw_hexagon(superficie, (100, 200, 255), center, self.radio - 5)  # Hexágono interior

        pygame.draw.circle(superficie, (200, 230, 255), center, 3)

        for i in range(4):
            angle = i * math.pi / 2 + self.pulse_phase  # Desfase para que roten.
            energy_x = center[0] + 6 * math.cos(angle)
            energy_y = center[1] + 6 * math.sin(angle)
            pygame.draw.circle(superficie, (0, 255, 255), (int(energy_x), int(energy_y)), 2)

    def _draw_enemy(self, superficie, center):
        diamond_size = self.radio
        diamond_points = [
            (center[0], center[1] - diamond_size),
            (center[0] + diamond_size, center[1]),
            (center[0], center[1] + diamond_size),
            (center[0] - diamond_size, center[1])
        ]

        shadow_points = [(p[0] + 2, p[1] + 2) for p in diamond_points]
        pygame.draw.polygon(superficie, (100, 0, 0), shadow_points)

        pygame.draw.polygon(superficie, self.color, diamond_points)
        pygame.draw.polygon(superficie, (255, 100, 100), diamond_points, 2)

        inner_points = []
        for i in range(3):
            angle = (i * 2 * math.pi / 3) + math.radians(self.shield_rotation * 2)
            x = center[0] + 5 * math.cos(angle)
            y = center[1] + 5 * math.sin(angle)
            inner_points.append((x, y))
        pygame.draw.polygon(superficie, (255, 0, 0), inner_points)

        for i in range(6):
            angle = i * math.pi / 3 + self.pulse_phase
            line_start = (
                center[0] + 4 * math.cos(angle),
                center[1] + 4 * math.sin(angle)
            )
            line_end = (
                center[0] + (self.radio - 2) * math.cos(angle),
                center[1] + (self.radio - 2) * math.sin(angle)
            )
            pygame.draw.line(superficie, (255, 50, 50), line_start, line_end, 1)
    def mover(self, dx, dy, obstaculos = None, otros_agentes = None):
        factor_diag = 0.707 if dx != 0 and dy != 0 else 1.0
        nueva_x = self.x + dx * self.velocidad * factor_diag
        nueva_y = self.y + dy * self.velocidad * factor_diag

        rect_futuro = pygame.Rect(
            int(nueva_x - self.radio), int(nueva_y - self.radio),
            self.radio * 2, self.radio * 2
        )

        colision = False

        if obstaculos:
            for obst in obstaculos:
                if rect_futuro.colliderect(obst.rect):
                    colision = True
                    break

        if not colision and otros_agentes:
            for otro in otros_agentes:
                if otro is self:
                    continue
                rect_otro = pygame.Rect(
                    int(otro.x - otro.radio), int(otro.y - otro.radio),
                    otro.radio * 2, otro.radio * 2
                )
                if rect_futuro.colliderect(rect_otro):
                    colision = True
                    break

        if not colision:
            self.x = max(self.radio, min(nueva_x, 800 - self.radio))
            self.y = max(self.radio, min(nueva_y, 600 - self.radio))
            self.update_effects()


class Enemigo(Agente):
    def __init__(self, x, y):
        super().__init__(x, y, (255, 50, 50), radio=12, velocidad=3, agent_type="enemy", vida_maxima=60)
        self.scan_angle = 0
        self.alert_level = 0

        self.dano_contacto = 15

    def update_ai_effects(self):
        self.scan_angle += 5

class Jugador(Agente):
    def __init__(self, x, y):
        super().__init__(x, y, (50, 100, 255), radio=10, velocidad=5, agent_type="player", vida_maxima=100)
        self.boost_energy = 100
        self.shield_active = False
        self.boost_locked = False

        self.proyectiles = []
        self.tiempo_ultimo_disparo = 0
        self.cadencia_disparo = 200

    def disparar(self, target_x, target_y):
        tiempo_actual = pygame.time.get_ticks()
        if tiempo_actual - self.tiempo_ultimo_disparo >= self.cadencia_disparo:
            proyectil = Proyectil(self.x, self.y, target_x, target_y)
            self.proyectiles.append(proyectil)
            self.tiempo_ultimo_disparo = tiempo_actual

    def dibujar_proyectiles(self, superficie):
        for proyectil in self.proyectiles:
            proyectil.dibujar(superficie)


