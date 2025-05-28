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
