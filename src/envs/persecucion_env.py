import pygame
import random
import math
import time
import numpy as np
import gymnasium as gym
from gymnasium import spaces

import sys
sys.path.append("src")

from src.utils.mapa_utils import GeneradorDeMapas
from src.ia.smart_chase_algorithm import AlgoritmoPersecucionInteligente, calcular_accion_inteligente
from src.model.agentes import Jugador, Enemigo
from src.model.entorno import ObstaculoFuturista, PowerUpSalud
from src.utils.visual_effects import VisualEffects
from src.utils.pantallas import pantalla_bienvenida, pantalla_game_over



generador_mapa = GeneradorDeMapas()

class PersecucionPygameEnv(gym.Env):

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}

    def __init__(self, ancho_pantalla=600, alto_pantalla=400, render_mode=None,
                 modo_entrenamiento=False, modo_ia="hibrido", velocidad_juego=60, num_enemigos=4):

        super().__init__()
        self.ancho_pantalla = ancho_pantalla
        self.alto_pantalla = alto_pantalla
        self.render_mode = render_mode
        self.modo_entrenamiento = modo_entrenamiento
        self.modo_ia = modo_ia
        self.velocidad_juego = velocidad_juego
        self.num_enemigos = num_enemigos

        self.juego_terminado = False
        self.victoria = False
        self.puntos = 0


        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(5 * self.num_enemigos + 3,),
            dtype=np.float32
        )

        self.tiempo_ultimo_mapa = [time.time()]
        self.INTERVALO_MAPA = 15

        self.powerups_salud = []
        self.tiempo_ultimo_powerup = time.time()
        self.INTERVALO_POWERUP = 11


        self.action_space = spaces.Discrete(9)


        self.pantalla = None
        self.clock = None
        self.font = None
        self.jugador = None
        self.enemigos = []
        self.obstaculos = []
        self.distancia_anterior = None
        self.pasos = 0
        self.max_pasos = 1500 if self.modo_entrenamiento else float("inf")
        self.score = 0
        self.capturas = 0


        self.algoritmo_ia = AlgoritmoPersecucionInteligente(ancho_pantalla, alto_pantalla)
        self.usar_ia_inteligente = True
        self.tiempo_captura_promedio = []
        self.efectividad_ia = 0.0

    def _get_obs(self):
        player_x_norm = self.jugador.x / self.ancho_pantalla
        player_y_norm = self.jugador.y / self.alto_pantalla

        obs_list = []

        for enemigo in self.enemigos:
            ex_norm = enemigo.x / self.ancho_pantalla
            ey_norm = enemigo.y / self.alto_pantalla
            dx = self.jugador.x - enemigo.x
            dy = self.jugador.y - enemigo.y
            dist = max(math.hypot(dx, dy), 1.0)
            dir_x = dx / dist
            dir_y = dy / dist
            dist_norm = min(dist / 300.0, 1.0)
            obs_list.extend([ex_norm, ey_norm, dir_x, dir_y, dist_norm])

        prog = self.pasos / self.max_pasos
        obs_list.extend([player_x_norm, player_y_norm, prog])

        return np.array(obs_list, dtype=np.float32)

    def _get_info(self):
        distancias = [
            math.hypot(e.x - self.jugador.x, e.y - self.jugador.y)
            for e in self.enemigos
        ]
        return {
            "distancias": distancias,
            "pasos": self.pasos,
            "capturas": self.capturas,
            "efectividad_ia": self.efectividad_ia,
            "modo_ia": self.modo_ia
        }

    def reset(self, seed=None):

        super().reset(seed=seed)
        intentos = 0
        jugador_valido = False

        while intentos < 200 and not jugador_valido:
            jugador_x = random.randint(50, self.ancho_pantalla - 50)
            jugador_y = random.randint(50, self.alto_pantalla - 50)
            jugador_rect = pygame.Rect(int(jugador_x - 10), int(jugador_y - 10), 20, 20)

            enemigos_candidatos = []
            valido = True

            for _ in range(self.num_enemigos):
                ex = random.randint(50, self.ancho_pantalla - 50)
                ey = random.randint(50, self.alto_pantalla - 50)
                enemigo_rect_temp = pygame.Rect(int(ex - 12), int(ey - 12), 24, 24)


                if enemigo_rect_temp.colliderect(jugador_rect):
                    valido = False
                    break

                for (ox, oy) in enemigos_candidatos:
                    if math.hypot(ex - ox, ey - oy) < 80:
                        valido = False
                        break
                if not valido:
                    break

                enemigos_candidatos.append((ex, ey))

            if valido:
                for (ex, ey) in enemigos_candidatos:
                    d = math.hypot(ex - jugador_x, ey - jugador_y)
                    if d <= 150:
                        valido = False
                        break

            if valido:
                self.jugador = Jugador(jugador_x, jugador_y)
                self.enemigos = [Enemigo(ex, ey) for (ex, ey) in enemigos_candidatos]
                jugador_valido = True

            intentos += 1

        if not jugador_valido:
            raise RuntimeError("No se encontraron posiciones válidas para jugador y enemigos tras 200 intentos")

        self.obstaculos = []
        obstaculo_central = ObstaculoFuturista(
            self.ancho_pantalla // 2 - 40, self.alto_pantalla // 2 - 60, 80, 120
        )

        choque_central = False
        if obstaculo_central.rect.colliderect(pygame.Rect(int(self.jugador.x - 10), int(self.jugador.y - 10), 20, 20)):
            choque_central = True

        for enemigo in self.enemigos:
            enemigo_rect = pygame.Rect(int(enemigo.x - 12), int(enemigo.y - 12), 24, 24)
            if obstaculo_central.rect.colliderect(enemigo_rect):
                choque_central = True
                break

        if not choque_central:
            self.obstaculos.append(obstaculo_central)
        intentos_obs = 0
        num_obs = random.randint(2, 4)
        target_obs = num_obs + (1 if not choque_central else 0)

        while len(self.obstaculos) < target_obs and intentos_obs < 100:
            obs_x = random.randint(50, self.ancho_pantalla - 100)
            obs_y = random.randint(50, self.alto_pantalla - 80)
            obs_w = random.randint(30, 60)
            obs_h = random.randint(30, 60)
            nuevo_obs = ObstaculoFuturista(obs_x, obs_y, obs_w, obs_h)

            solapamiento = False

            for obs_exist in self.obstaculos:
                if nuevo_obs.rect.colliderect(obs_exist.rect):
                    solapamiento = True
                    break

            zona_segura_j = pygame.Rect(0, 0, 60, 60)
            zona_segura_j.center = (self.ancho_pantalla // 4, self.alto_pantalla // 2)
            zona_segura_e = pygame.Rect(0, 0, 60, 60)
            zona_segura_e.center = (3 * self.ancho_pantalla // 4, self.alto_pantalla // 2)

            if (nuevo_obs.rect.colliderect(zona_segura_j) or
                    nuevo_obs.rect.colliderect(zona_segura_e)):
                solapamiento = True

            jugador_rect = pygame.Rect(int(self.jugador.x - 10), int(self.jugador.y - 10), 20, 20)
            if nuevo_obs.rect.colliderect(jugador_rect):
                solapamiento = True

            if not solapamiento:
                for enemigo in self.enemigos:
                    enemigo_rect = pygame.Rect(int(enemigo.x - 12), int(enemigo.y - 12), 24, 24)
                    if nuevo_obs.rect.colliderect(enemigo_rect):
                        solapamiento = True
                        break

            if not solapamiento:
                dist_jugador = math.hypot(
                    (nuevo_obs.rect.centerx - self.jugador.x),
                    (nuevo_obs.rect.centery - self.jugador.y)
                )
                if dist_jugador < 30:
                    solapamiento = True

                for enemigo in self.enemigos:
                    dist_enemigo = math.hypot(
                        (nuevo_obs.rect.centerx - enemigo.x),
                        (nuevo_obs.rect.centery - enemigo.y)
                    )
                    if dist_enemigo < 30:
                        solapamiento = True
                        break

            if not solapamiento:
                self.obstaculos.append(nuevo_obs)

            intentos_obs += 1

        self.distancia_anterior = None
        self.pasos = 0
        self.juego_terminado = False
        self.victoria = False
        self.puntos = 0
        self.algoritmo_ia.historial_jugador.clear()
        for _ in range(3):
            self.algoritmo_ia.historial_jugador.append((self.jugador.x, self.jugador.y))

        observation = self._get_obs()
        info = self._get_info()
        if self.render_mode == "human":
            self._render_frame()
        return observation, info

    def step(self, action):
        if self.juego_terminado:
            return self._get_obs(), 0, True, False, self._get_info()

        self.pasos += 1

        if not self.modo_entrenamiento:
            self.jugador.actualizar_proyectiles(self.ancho_pantalla, self.alto_pantalla, self.obstaculos)

            for proyectil in self.jugador.proyectiles[:]:
                for enemigo in self.enemigos[:]:
                    if not enemigo.esta_vivo:
                        continue
                    if proyectil.colisiona_con(enemigo):
                        proyectil.activo = False
                        if proyectil in self.jugador.proyectiles:
                            self.jugador.proyectiles.remove(proyectil)

                        murio = enemigo.recibir_dano(20)
                        if murio:
                            enemigo.esta_vivo = False
                            self.puntos += 100
                        else:
                            self.puntos += 10
                        break

        acciones_enemigos = []
        enemigos_vivos = [e for e in self.enemigos if e.esta_vivo]

        if self.usar_ia_inteligente:
            for enemigo in enemigos_vivos:
                try:
                    accion_ia = calcular_accion_inteligente(
                        enemigo, self.jugador, self.obstaculos,
                        self.algoritmo_ia, self.modo_ia
                    )
                except Exception as e:
                    print(f"Error en IA inteligente: {e}")
                    accion_ia = action
                acciones_enemigos.append(accion_ia)
        else:
            acciones_enemigos = [action] * len(enemigos_vivos)
        movimientos_enemigo = [
            (0, -1), (1, -1), (1, 0), (1, 1),
            (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, 0)
        ]

        for idx, enemigo in enumerate(enemigos_vivos):
            if idx < len(acciones_enemigos):
                act = acciones_enemigos[idx]
                dx, dy = movimientos_enemigo[act]
                enemigo.mover(dx, dy, self.obstaculos, enemigos_vivos)


        if self.modo_entrenamiento:
            terminado = False
            recompensa = 0

            for enemigo in enemigos_vivos:
                distancia = math.hypot(enemigo.x - self.jugador.x, enemigo.y - self.jugador.y)
                if distancia < (enemigo.radio + self.jugador.radio):
                    terminado = True
                    self.capturas += 1
                    self.tiempo_captura_promedio.append(self.pasos)
                    recompensa += 300  # Gran recompensa por captura
                    break

            if not terminado:
                min_dist = min(math.hypot(e.x - self.jugador.x, e.y - self.jugador.y)
                               for e in enemigos_vivos) if enemigos_vivos else float('inf')

                if self.distancia_anterior is not None and enemigos_vivos:
                    dif_dist = self.distancia_anterior - min_dist
                    factor_dist = 1.0 + (200 - min(min_dist, 200)) / 200
                    recompensa += dif_dist * factor_dist * 3.0

                recompensa -= 0.01
                self.distancia_anterior = min_dist

            truncado = self.pasos >= self.max_pasos

        else:
            self.jugador.manejar_input(self.obstaculos)

            for enemigo in enemigos_vivos:
                distancia = math.hypot(enemigo.x - self.jugador.x, enemigo.y - self.jugador.y)
                if distancia < (enemigo.radio + self.jugador.radio):
                    murio_jugador = self.jugador.recibir_dano(enemigo.dano_contacto)
                    if murio_jugador:
                        if self.puntos >= 50:
                            self.puntos -= 10
                        self.juego_terminado = True
                        self.victoria = False
                        break
                    elif murio_jugador == False:
                        if self.puntos >= 50:
                            self.puntos -= 10

            if not enemigos_vivos and not self.juego_terminado:
                self.juego_terminado = True
                self.victoria = True
                self.puntos += 500
            terminado = self.juego_terminado
            recompensa = 0
            truncado = False

        observation = self._get_obs()
        info = self._get_info()

        if self.render_mode == "human":
            self._render_frame()

        if time.time() - self.tiempo_ultimo_powerup > self.INTERVALO_POWERUP and not self.modo_entrenamiento:
            for _ in range(5):
                x = random.randint(30, self.ancho_pantalla - 30)
                y = random.randint(30, self.alto_pantalla - 30)
                nuevo = PowerUpSalud(x, y)
                self.INTERVALO_POWERUP = random.randint(7, 12)

                if any(nuevo.rect().colliderect(obs.rect) for obs in self.obstaculos):
                    continue

                self.powerups_salud.append(nuevo)
                self.tiempo_ultimo_powerup = time.time()
                break

        self.powerups_salud = [p for p in self.powerups_salud if p.activo]

        for powerup in self.powerups_salud[:]:
            if self.jugador.vida_actual >= self.jugador.vida_maxima:
                break
            powerup.actualizar()

            distancia = math.hypot(powerup.x - self.jugador.x, powerup.y - self.jugador.y)
            if distancia < (self.jugador.radio + powerup.radio):
                self.jugador.vida_actual = min(self.jugador.vida_maxima, self.jugador.vida_actual + 15)
                self.powerups_salud.remove(powerup)

            if time.time() - self.tiempo_ultimo_mapa[0] > self.INTERVALO_MAPA and not hasattr(self,"actualizando_mapa") and not self.modo_entrenamiento:
                self.actualizando_mapa = True

                def set_mapa(nuevo_mapa):
                    if nuevo_mapa:
                        self.obstaculos = generador_mapa.filtrar_obstaculos_sin_colision(nuevo_mapa, [self.jugador] + self.enemigos)
                    if hasattr(self, "actualizando_mapa"):
                        delattr(self, "actualizando_mapa")
                    self.tiempo_ultimo_mapa[0] = time.time()

                generador_mapa.actualizar_mapa_async(self.ancho_pantalla, self.alto_pantalla, set_mapa)
            return observation, recompensa, terminado, truncado, info

    def _calcular_recompensa_mejorada(self, accion):
        distancia_actual = min(
            math.hypot(e.x - self.jugador.x, e.y - self.jugador.y) for e in self.enemigos if e.esta_vivo)
        recompensa = 0

        if distancia_actual < (
                self.enemigos[0].radio + self.jugador.radio):  # Asume que todos los enemigos tienen el mismo radio
            recompensa += 300

        if hasattr(self, 'distancia_anterior') and self.distancia_anterior is not None:
            diferencia_distancia = self.distancia_anterior - distancia_actual  # Recompensa por la reducción de distancia
            # Un factor de distancia que aumenta la recompensa cuando la distancia es menor,
            # lo que fomenta que el enemigo se acerque aún más una vez cerca.
            factor_distancia = 1.0 + (200 - min(distancia_actual, 200)) / 200
            recompensa += diferencia_distancia * factor_distancia * 3.0

        recompensa -= 0.01

        rect_enemigo = pygame.Rect(
            int(self.enemigos[0].x - self.enemigos[0].radio),  # Asume que solo se considera el primer enemigo
            int(self.enemigos[0].y - self.enemigos[0].radio),
            self.enemigos[0].radio * 2, self.enemigos[0].radio * 2
        )
        colision = False
        for obstaculo in self.obstaculos:
            if rect_enemigo.colliderect(obstaculo.rect):
                recompensa -= 5
                colision = True
                break
        if not colision:
            recompensa += 0.5

        if accion == 8:
            recompensa -= 1.0

        if distancia_actual < 50:
            recompensa += (50 - distancia_actual) * 0.15

        if hasattr(self, 'accion_anterior'):
            if accion != self.accion_anterior and accion != 8:
                recompensa -= 0.2
        self.accion_anterior = accion

        self.distancia_anterior = distancia_actual
        return recompensa

    def _render_frame(self):
        if self.pantalla is None:
            pygame.init()
            pygame.display.init()
            self.pantalla = pygame.display.set_mode((self.ancho_pantalla, self.alto_pantalla))
            pygame.display.set_caption("🚀 CYBER PURSUIT")

            if not self.modo_entrenamiento:
                pantalla_bienvenida(self.pantalla, self.ancho_pantalla, self.alto_pantalla)
            self.font = pygame.font.Font(None, 28)
            self.title_font = pygame.font.Font(None, 36)
        if self.clock is None:
            self.clock = pygame.time.Clock()

        for y in range(self.alto_pantalla):
            base_intensity = 10 + (y / self.alto_pantalla) * 20
            blue_component = int(base_intensity + 10 * math.sin(y * 0.01))
            purple_component = int(base_intensity * 0.7)
            color = (int(base_intensity * 0.3), purple_component, blue_component)
            pygame.draw.line(self.pantalla, color, (0, y), (self.ancho_pantalla, y))

        grid_intensity = int(40 + 20 * (math.sin(pygame.time.get_ticks() * 0.001) + 1) / 2)
        grid_color = (grid_intensity, grid_intensity, grid_intensity + 20)

        for x in range(0, self.ancho_pantalla, 50):
            pygame.draw.line(self.pantalla, grid_color, (x, 0), (x, self.alto_pantalla), 1)
        for y in range(0, self.alto_pantalla, 50):
            pygame.draw.line(self.pantalla, grid_color, (0, y), (self.ancho_pantalla, y), 1)

        for obstaculo in self.obstaculos:
            if hasattr(obstaculo, 'update'):
                obstaculo.update()
            obstaculo.dibujar(self.pantalla)

        if len(self.enemigos) > 1:
            for i, enemigo1 in enumerate(self.enemigos):
                if not enemigo1.esta_vivo:
                    continue
                for enemigo2 in self.enemigos[i + 1:]:
                    if not enemigo2.esta_vivo:
                        continue
                    dist = math.hypot(enemigo1.x - enemigo2.x, enemigo1.y - enemigo2.y)
                    if dist < 150:
                        alpha = int(50 * (1 - dist / 150))
                        VisualEffects.draw_particle_trail(
                            self.pantalla,
                            (enemigo1.x, enemigo1.y),
                            (enemigo2.x, enemigo2.y),
                            (255, 100, 100),
                            particles=6
                        )

        self.jugador.x = max(0, min(self.jugador.x, self.ancho_pantalla))
        self.jugador.y = max(0, min(self.jugador.y, self.alto_pantalla))
        self.jugador.dibujar(self.pantalla)

        for enemigo in self.enemigos:
            if not enemigo.esta_vivo:
                continue
            enemigo.x = max(0, min(enemigo.x, self.ancho_pantalla))
            enemigo.y = max(0, min(enemigo.y, self.alto_pantalla))
            enemigo.dibujar(self.pantalla)

        if self.enemigos:
            enemigos_ordenados = sorted(
                self.enemigos,
                key=lambda e: math.hypot(e.x - self.jugador.x, e.y - self.jugador.y)
            )

            closest_enemy = next((e for e in enemigos_ordenados if e.esta_vivo), None)

            if closest_enemy:
                vision_surface = pygame.Surface((160, 160), pygame.SRCALPHA)  # Superficie semitransparente
                pygame.draw.circle(vision_surface, (255, 0, 0, 20), (80, 80), 80)  # Círculo interior
                pygame.draw.circle(vision_surface, (255, 100, 100, 40), (80, 80), 80, 2)  # Borde del círculo
                self.pantalla.blit(vision_surface,
                                   (closest_enemy.x - 80, closest_enemy.y - 80))  # Dibujar en la posición del enemigo

        if not self.modo_entrenamiento:
            self._draw_futuristic_hud()

        if not self.modo_entrenamiento:
            self.jugador.dibujar_proyectiles(self.pantalla)

        for powerup in self.powerups_salud:
            powerup.dibujar(self.pantalla)

        pygame.display.flip()
        if not self.modo_entrenamiento and self.juego_terminado:
            pantalla_game_over(self.pantalla, self.ancho_pantalla,
                               self.alto_pantalla, self.victoria, self.puntos)

        self.clock.tick(self.velocidad_juego if not self.modo_entrenamiento else 0)

    def _draw_futuristic_hud(self):
        vida_porcentaje = self.jugador.vida_actual / self.jugador.vida_maxima if self.jugador.esta_vivo else 0
        vida_bar_width = 180
        vida_bar_height = 11
        padding = 15
        vida_x = padding
        vida_y = self.alto_pantalla - vida_bar_height - padding

        vida_bg = pygame.Rect(vida_x, vida_y, vida_bar_width, vida_bar_height)
        pygame.draw.rect(self.pantalla, (50, 50, 50), vida_bg)

        vida_fill_width = int(vida_bar_width * vida_porcentaje)
        color_vida = (0, 255, 0) if vida_porcentaje > 0.6 else (255, 255, 0) if vida_porcentaje > 0.3 else (255, 0, 0)
        pygame.draw.rect(self.pantalla, color_vida, (vida_x, vida_y, vida_fill_width, vida_bar_height))
        pygame.draw.rect(self.pantalla, (150, 150, 150), vida_bg, 2)

        puntos_text = f"PUNTOS: {self.puntos}"
        puntos_surface = pygame.font.Font(None, 28).render(puntos_text, True, (255, 255, 0))
        self.pantalla.blit(puntos_surface, (15, 15))

        enemigos_vivos = sum(1 for e in self.enemigos if e.esta_vivo)
        enemigos_text = f"ENEMIGOS: {enemigos_vivos}"
        enemigos_surface = pygame.font.Font(None, 28).render(enemigos_text, True, (255, 100, 100))
        self.pantalla.blit(enemigos_surface, (15, 45))

        if hasattr(self.jugador, 'boost_energy'):
            bar_width = 120
            bar_height = 12
            padding = 15
            x_pos = self.ancho_pantalla - bar_width - padding
            y_pos = self.alto_pantalla - bar_height - padding

            energy_rect = pygame.Rect(x_pos, y_pos, bar_width, bar_height)
            pygame.draw.rect(self.pantalla, (40, 40, 40), energy_rect)
            fill_width = int(bar_width * max(0, min(self.jugador.boost_energy, 100)) / 100)
            energy_fill = pygame.Rect(x_pos, y_pos, fill_width, bar_height)
            # Cambia el color de la barra de energía según el nivel de energía.
            energy_color = (0, 255, 255) if self.jugador.boost_energy > 50 else (255, 255, 0)
            pygame.draw.rect(self.pantalla, energy_color, energy_fill)
            pygame.draw.rect(self.pantalla, (100, 100, 100), energy_rect, 2)

        minimap_size = 140
        minimap_rect = pygame.Rect(self.ancho_pantalla - minimap_size - 15, 15, minimap_size, minimap_size)
        minimap_surface = pygame.Surface((minimap_size, minimap_size), pygame.SRCALPHA)
        player_x = max(0, min(self.jugador.x, self.ancho_pantalla))
        player_y = max(0, min(self.jugador.y, self.alto_pantalla))
        scale_x = minimap_size / self.ancho_pantalla
        scale_y = minimap_size / self.alto_pantalla

        player_minimap_x = int(player_x * scale_x)
        player_minimap_y = int(player_y * scale_y)

        if (player_minimap_x >= 0 and player_minimap_x <= minimap_size and
                player_minimap_y >= 0 and player_minimap_y <= minimap_size):
            bg_opacity = 80
        else:
            bg_opacity = 150

        pygame.draw.rect(minimap_surface, (0, 0, 0, bg_opacity), (0, 0, minimap_size, minimap_size))
        VisualEffects.draw_tech_border(minimap_surface, pygame.Rect(0, 0, minimap_size, minimap_size), (0, 255, 0), 1)

        if hasattr(self, 'obstaculos'):
            for obstaculo in self.obstaculos:
                # Asegura que las coordenadas del obstáculo estén dentro del rango del mapa.
                ox = max(0, min(obstaculo.x, self.ancho_pantalla))
                oy = max(0, min(obstaculo.y, self.alto_pantalla))
                ow = max(1, int(obstaculo.ancho * scale_x))
                oh = max(1, int(obstaculo.alto * scale_y))
                obs_x = int(ox * scale_x)
                obs_y = int(oy * scale_y)
                pygame.draw.rect(minimap_surface, (180, 180, 180), (obs_x, obs_y, ow, oh))

        pygame.draw.circle(minimap_surface, (0, 150, 255), (player_minimap_x, player_minimap_y), 4)

        for enemigo in self.enemigos:
            if not enemigo.esta_vivo:
                continue
            ex = max(0, min(enemigo.x, self.ancho_pantalla))
            ey = max(0, min(enemigo.y, self.alto_pantalla))
            enemy_x = int(ex * scale_x)
            enemy_y = int(ey * scale_y)
            pygame.draw.circle(minimap_surface, (255, 0, 0), (enemy_x, enemy_y), 3)

        for powerup in self.powerups_salud:
            if not powerup.activo:
                continue
            px = int(powerup.x * scale_x)
            py = int(powerup.y * scale_y)
            pygame.draw.circle(minimap_surface, (0, 255, 100), (px, py), 3)

        self.pantalla.blit(minimap_surface, minimap_rect.topleft)
        minimap_label = pygame.font.Font(None, 20).render("RADAR", True, (0, 255, 0))
        self.pantalla.blit(minimap_label, (self.ancho_pantalla - 65, minimap_rect.bottom + 5))