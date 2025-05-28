import pygame
import sys

def pantalla_bienvenida(pantalla, ancho, alto):

    pygame.font.init()
    clock = pygame.time.Clock()

    title_font = pygame.font.Font(None, 72)
    button_font = pygame.font.Font(None, 36)

    titulo_text = title_font.render("CYBER PURSUIT", True, (0, 200, 255))
    titulo_rect = titulo_text.get_rect(center=(ancho // 2, alto // 3))

    button_text = button_font.render("INICIAR JUEGO", True, (255, 255, 255))
    button_rect = button_text.get_rect(center=(ancho // 2, alto // 2))
    button_color = (0, 150, 255)
    button_hover_color = (0, 200, 255)

    running = True
    while running:
        pantalla.fill((10, 10, 30))

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                if button_rect.collidepoint(mouse_pos):
                    running = False

        mouse_pos = pygame.mouse.get_pos()
        color_actual = button_hover_color if button_rect.collidepoint(mouse_pos) else button_color

        pantalla.blit(titulo_text, titulo_rect)

        padding_x, padding_y = 20, 10
        button_bg_rect = pygame.Rect(
            button_rect.left - padding_x,
            button_rect.top - padding_y,
            button_rect.width + 2 * padding_x,
            button_rect.height + 2 * padding_y
        )
        pygame.draw.rect(pantalla, color_actual, button_bg_rect, border_radius=8)
        pantalla.blit(button_text, button_rect)

        pygame.display.flip()
        clock.tick(60)