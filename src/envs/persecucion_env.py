import pygame
import random
import math
import time
import numpy as np
import gymnasium as gym
from gymnasium import spaces

import sys

from utils.mapa_utils import GeneradorDeMapas
from ia.smart_chase_algorithm import AlgoritmoPersecucionInteligente, calcular_accion_inteligente
from model.agentes import Jugador, Enemigo
from model.entorno import ObstaculoFuturista, PowerUpSalud
from utils.visual_effects import VisualEffects
from utils.pantallas import pantalla_bienvenida, pantalla_game_over



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
        self.modo_ia = modo_ia  # Configura el modo de IA para los enemigos
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
