import pygame
import math


class VisualEffects:

    @staticmethod
    def draw_glow_circle(surface, color, center, radius, glow_radius=None):
        if glow_radius is None:
            glow_radius = radius + 15

        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)

        for i in range(glow_radius, radius, -2):
            alpha = int(255 * (radius / i) * 0.3)
            glow_color = (min(255, max(0, color[0])),
                          min(255, max(0, color[1])),
                          min(255, max(0, color[2])),
                          max(0, min(255, alpha)))

            pygame.draw.circle(glow_surface, glow_color, (glow_radius, glow_radius), i)

        pygame.draw.circle(glow_surface, color, (glow_radius, glow_radius), radius)

        surface.blit(glow_surface, (center[0] - glow_radius, center[1] - glow_radius))

    @staticmethod
    def draw_hexagon(surface, color, center, radius):

        points = []
        for i in range(6):
            angle_rad = math.pi / 3 * i - math.pi / 6
            x = center[0] + radius * math.cos(angle_rad)
            y = center[1] + radius * math.sin(angle_rad)
            points.append((int(x), int(y)))

        pygame.draw.polygon(surface, color, points)
        return points

    @staticmethod
    def draw_tech_border(surface, rect, color, thickness=2):

        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        corner_size = 8
        points = [
            (x + corner_size, y), (x + w - corner_size, y),
            (x + w, y + corner_size), (x + w, y + h - corner_size),
            (x + w - corner_size, y + h), (x + corner_size, y + h),
            (x, y + h - corner_size), (x, y + corner_size)
        ]
        pygame.draw.polygon(surface, color, points, thickness)

    @staticmethod
    def draw_particle_trail(surface, start_pos, end_pos, color, particles=8):

        for i in range(particles):
            t = i / particles
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * t
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * t

            alpha = int(255 * (1 - t) * 0.7)  # Factor 0.7 para que no sea completamente opaco.

            particle_surface = pygame.Surface((4, 4), pygame.SRCALPHA)  # Pequeña superficie de 4x4 píxeles.
            particle_color = (*color[:3], alpha)  # Combina el color RGB con el alfa calculado.

            pygame.draw.circle(particle_surface, particle_color, (2, 2), 2)

            surface.blit(particle_surface, (int(x - 2), int(y - 2)))
