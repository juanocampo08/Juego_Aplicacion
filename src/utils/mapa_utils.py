import  requests
import pygame
import json
import re
import random
import sys
import threading

sys.path.append("src")

from src.model.entorno import ObstaculoFuturista

API_KEY = "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"

class GeneradorDeMapas:
    def __init__(self, api_key=API_KEY, modelo_api="deepseek/deepseek-prover-v2:free"):
        self.api_key = api_key
        self.modelo_api = modelo_api
