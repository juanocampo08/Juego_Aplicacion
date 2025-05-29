import requests
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

    def obtener_mapa_aleatorio(self, ancho, alto, num_obstaculos=5, radio_jugador=10, radio_enemigo=12):

        if not self.api_key:
            print("Advertencia: No se ha proporcionado una clave API. No se generará el mapa.")
            return []

        prompt = (
            f"Generate exactly {num_obstaculos} rectangular obstacles for a {ancho}x{alto} pixel video game map. "
            f"MANDATORY REQUIREMENTS:\n"
            f"- ALWAYS include one central obstacle near the map center\n"
            f"- Create a challenging but playable level with STRATEGIC GAP SIZES:\n"
            f"  * Player radius: {radio_jugador}px, Enemy radius: {radio_enemigo}px\n"
            f"  * Create some narrow gaps ({radio_enemigo * 2 + 5}-{radio_jugador * 2 - 5}px) where ONLY enemies can fit through\n"
            f"  * Create wider passages ({radio_jugador * 2 + 10}px+) where both player and enemies can move\n"
            f"- Use tight spaces as enemy escape routes and tactical advantages\n"
            f"- Vary obstacle sizes: small (30-80px), medium (80-150px), large (150-300px)\n"
            f"- Position obstacles to create chokepoints and enemy-only shortcuts\n"
            f"- Keep all obstacles within bounds (0,0) to ({ancho},{alto})\n"
            f"- Prevent complete obstacle overlap but allow strategic narrow passages\n"
            f"- Leave spawn areas clear near corners\n\n"
            f"TACTICAL DESIGN GOAL: Create cat-and-mouse gameplay where smaller enemies can escape through gaps the larger player cannot follow.\n\n"
            f"OUTPUT FORMAT:\n"
            f"CRITICAL: Respond with ONLY a valid JSON array. No explanations, no markdown, no extra text.\n"
            f"Example format: [{{\"x\":100,\"y\":100,\"ancho\":50,\"alto\":150}}]"
        )

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.modelo_api,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()

            content = response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            print(f"[MAPA API FALLÓ] Usando fallback local: {e}")
            return [{"x": o.x, "y": o.y, "ancho": o.ancho, "alto": o.alto} for o in
                    self.generar_obstaculos_sin_colision(ancho, alto, [], num_obstaculos)]
        except KeyError as e:
            print(f"Error al parsear la respuesta JSON de la API (clave faltante): {e}")
            print(f"Contenido completo de la respuesta: {response.text}")
            return []
        except Exception as e:
            print(f"Error inesperado al obtener el mapa: {e}")
            return []

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            print("El contenido de la API no es JSON puro. Intentando extraer JSON con regex...")
            json_str = re.search(r"\[.*\]", content, re.DOTALL)
            if json_str:
                try:
                    return json.loads(json_str.group(0))
                except json.JSONDecodeError as e:
                    print(f"Error al parsear JSON extraído con regex: {e}")
            print("No se pudo extraer un JSON válido de la respuesta de la API.")
            return []

    def generar_obstaculos_sin_colision(self, ancho, alto, entidades, num_obstaculos=4, max_intentos=100):

        obstaculos = []
        intentos = 0
        while len(obstaculos) < num_obstaculos and intentos < max_intentos:
            w = random.randint(30, 100)
            h = random.randint(30, 100)
            x = random.randint(0, ancho - w)
            y = random.randint(0, alto - h)
            nuevo_rect = pygame.Rect(x, y, w, h)

            colision_con_entidades = False
            for entidad in entidades:
                entidad_rect = pygame.Rect(
                    int(entidad.x - entidad.radio), int(entidad.y - entidad.radio),
                    entidad.radio * 2, entidad.radio * 2
                )
                if nuevo_rect.colliderect(entidad_rect):
                    colision_con_entidades = True
                    break

            if colision_con_entidades:
                intentos += 1
                continue

            colision_con_obstaculos = False
            for obs in obstaculos:
                if nuevo_rect.colliderect(obs.rect):
                    colision_con_obstaculos = True
                    break

            if colision_con_obstaculos:
                intentos += 1
                continue

            obstaculos.append(ObstaculoFuturista(x, y, w, h))
            intentos += 1
        return obstaculos

    def filtrar_obstaculos_sin_colision(self, mapa_json, entidades):

        obstaculos_filtrados = []
        for o in mapa_json:
            rect = pygame.Rect(o["x"], o["y"], o["ancho"], o["alto"])

            colisiona = False
            for e in entidades:
                entidad_rect = pygame.Rect(
                    int(e.x - e.radio), int(e.y - e.radio),
                    e.radio * 2, e.radio * 2
                )
                if rect.colliderect(entidad_rect):
                    colisiona = True
                    break

            if not colisiona:
                obstaculos_filtrados.append(ObstaculoFuturista(o["x"], o["y"], o["ancho"], o["alto"]))
        return obstaculos_filtrados

    def actualizar_mapa_async(self, ancho, alto, callback):

        def worker():

            nuevo_mapa = self.obtener_mapa_aleatorio(ancho, alto)
            callback(nuevo_mapa)

        threading.Thread(target=worker, daemon=True).start()