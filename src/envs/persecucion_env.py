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

