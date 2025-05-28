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
