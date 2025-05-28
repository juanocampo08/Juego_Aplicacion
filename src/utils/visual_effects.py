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
