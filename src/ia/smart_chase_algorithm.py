import heapq
import pygame
import random
from collections import deque
import math


class AlgoritmoPersecucionInteligente:
  def __init__(self, ancho_mapa, alto_mapa, cell_size=15):
        self.ancho_mapa = ancho_mapa
        self.alto_mapa = alto_mapa
        self.cell_size = cell_size
        self.cols = ancho_mapa // cell_size
        self.rows = alto_mapa // cell_size
        
        self.historial_jugador = deque(maxlen=10) # Historial de posiciones del jugador para la predicción de movimiento.
        self.poblacion_rutas = []
    
    def calcular_mejor_accion(self, enemigo, jugador, obstaculos, modo="hibrido"):
      
      if modo == "hibrido":
            return self._algoritmo_hibrido(enemigo, jugador, obstaculos)
        elif modo == "predictivo":
            return self._a_star_predictivo(enemigo, jugador, obstaculos)
        elif modo == "campo_potencial":
            return self._campo_potencial(enemigo, jugador, obstaculos)
        elif modo == "genetico":
            return self._algoritmo_genetico(enemigo, jugador, obstaculos)
        else:
            return self._a_star_predictivo(enemigo, jugador, obstaculos)

    def _algoritmo_hibrido(self, enemigo, jugador, obstaculos):
      self._actualizar_historial_jugador(jugador)
      dx = jugador.x - enemigo.x
      dy = jugador.y - enemigo.y
      distancia = math.hypot(dx, dy)
      UMBRAL_LEJOS_GEN = 300   
      UMBRAL_LEJOS = 200       
      UMBRAL_CERCA = 80

      if distancia > UMBRAL_LEJOS_GEN:
            return self._algoritmo_genetico(enemigo, jugador, obstaculos, generaciones=3)
        elif distancia > UMBRAL_LEJOS:
            return self._a_star_predictivo(enemigo, jugador, obstaculos)
        else:
            if not self._hay_obstaculo_directo(enemigo, jugador, obstaculos):
                return self._campo_potencial(enemigo, jugador, obstaculos)
            else:
                return self._a_star_predictivo(enemigo, jugador, obstaculos)

    def _hay_obstaculo_directo(self, enemigo, jugador, obstaculos):
      steps = int(max(abs(enemigo.x - jugador.x), abs(enemigo.y - jugador.y)) // self.cell_size)
        if steps == 0:
            return False

        for i in range(1, steps + 1):
            t = i / float(steps)
            # Calcular el punto intermedio en la línea.
            x_inter = enemigo.x + (jugador.x - enemigo.x) * t
            y_inter = enemigo.y + (jugador.y - enemigo.y) * t
            punto = pygame.Rect(int(x_inter), int(y_inter), 2, 2)
            for obs in obstaculos:
                if punto.colliderect(obs.rect):
                    return True
        return False

    def _predecir_posicion_jugador(self):
      if len(self.historial_jugador) < 3:
            return self.historial_jugador[-1] if self.historial_jugador else (0, 0)
        
        velocidades = []
        for i in range(1, len(self.historial_jugador)):
            prev_pos = self.historial_jugador[i-1]
            curr_pos = self.historial_jugador[i]
            vx = curr_pos[0] - prev_pos[0]
            vy = curr_pos[1] - prev_pos[1]
            velocidades.append((vx, vy))
          
        sum_weights = sum(range(1, len(velocidades)+1))
        vx_pred = sum(vx * (i+1) for i, (vx, vy) in enumerate(velocidades)) / sum_weights
        vy_pred = sum(vy * (i+1) for i, (vx, vy) in enumerate(velocidades)) / sum_weights
        
        pos_actual = self.historial_jugador[-1]
        predicciones = []

        for t in range(1, 6):  
            pred_x = pos_actual[0] + vx_pred * t
            pred_y = pos_actual[1] + vy_pred * t
            pred_x = max(0, min(pred_x, self.ancho_mapa))
            pred_y = max(0, min(pred_y, self.alto_mapa))
            predicciones.append((pred_x, pred_y)) 

        return predicciones[2] if len(predicciones) > 2 else predicciones[0]

    def _a_star_predictivo(self, enemigo, jugador, obstaculos):
      pos_predicha = self._predecir_posicion_jugador()
      
      grid = self._crear_grid_mejorado(obstaculos)
        
      start = self._pos_a_grid(enemigo.x, enemigo.y)
      
      goal_pred = self._pos_a_grid(pos_predicha[0], pos_predicha[1])
      goal_actual = self._pos_a_grid(jugador.x, jugador.y)
      
      path = self._a_star_con_heuristica_mejorada(grid, start, goal_pred)
      
      if not path or len(path) < 2:
            path = self._a_star_con_heuristica_mejorada(grid, start, goal_actual)
      return self._path_a_accion(path, start)

    def _campo_potencial(self, enemigo, jugador, obstaculos):
      fx_atractiva = (jugador.x - enemigo.x)
      fy_atractiva = (jugador.y - enemigo.y)
      
      dist_jugador = max(math.sqrt(fx_atractiva**2 + fy_atractiva**2), 1)
      fx_atractiva = fx_atractiva / dist_jugador * 10
      fy_atractiva = fy_atractiva / dist_jugador * 10
      
      fx_repulsiva = 0
      fy_repulsiva = 0
      
      radio_evitacion = 25 
      for obstaculo in obstaculos:
          dist_x = enemigo.x - (obstaculo.x + obstaculo.ancho/2)
          dist_y = enemigo.y - (obstaculo.y + obstaculo.alto/2)
          distancia = math.sqrt(dist_x**2 + dist_y**2)
            
          if distancia < 25:
            factor_repulsion = 500 / max(distancia**2, 1)
            fx_repulsiva += (dist_x / max(distancia, 1)) * factor_repulsion
            fy_repulsiva += (dist_y / max(distancia, 1)) * factor_repulsion
            
      fx_total = fx_atractiva + fx_repulsiva
      fy_total = fy_atractiva + fy_repulsiva
      return self._fuerza_a_accion(fx_total, fy_total)

    def _algoritmo_genetico(self, enemigo, jugador, obstaculos, generaciones=5):
      if not self.poblacion_rutas:
            self._inicializar_poblacion_genetica(enemigo, jugador)
        
      for _ in range(generaciones):
            self._evaluar_poblacion(enemigo, jugador, obstaculos)
            self._seleccion_y_reproduccion()
            self._mutacion()
        
      mejor_ruta = max(self.poblacion_rutas, key=lambda r: r['fitness'])
      
      if mejor_ruta['path'] and len(mejor_ruta['path']) > 1:
            return self._path_a_accion(mejor_ruta['path'], self._pos_a_grid(enemigo.x, enemigo.y))
      return 8

    def _inicializar_poblacion_genetica(self, enemigo, jugador, tamaño_poblacion=20):
      self.poblacion_rutas = []
      start = self._pos_a_grid(enemigo.x, enemigo.y)
      goal = self._pos_a_grid(jugador.x, jugador.y)
      
      for _ in range(tamaño_poblacion):
            # Se genera una ruta aleatoria con un sesgo hacia el objetivo para empezar.
            ruta = self._generar_ruta_aleatoria(start, goal)
            self.poblacion_rutas.append({
                'path': ruta,
                'fitness': 0 # El fitness se calculará posteriormente.
            })

    def _generar_ruta_aleatoria(self, start, goal, max_pasos=15):
      ruta = [start]
        pos_actual = start
        
        for _ in range(max_pasos):
            if pos_actual == goal:
                break
              
            if random.random() < 0.7:
                dx = 1 if goal[1] > pos_actual[1] else (-1 if goal[1] < pos_actual[1] else 0)
                dy = 1 if goal[0] > pos_actual[0] else (-1 if goal[0] < pos_actual[0] else 0)
            else:
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
            
            nueva_pos = (pos_actual[0] + dy, pos_actual[1] + dx)
            
            if (0 <= nueva_pos[0] < self.rows and 
                0 <= nueva_pos[1] < self.cols):
                ruta.append(nueva_pos)
                pos_actual = nueva_pos
        
        return ruta

    def _evaluar_poblacion(self, enemigo, jugador, obstaculos):
      grid = self._crear_grid_mejorado(obstaculos)
        
        for individuo in self.poblacion_rutas:
            ruta = individuo['path']
            fitness = 0
            
            if not ruta:
                individuo['fitness'] = -1000
                continue
            
            fitness -= len(ruta) * 2
            
            if ruta:
                pos_final = ruta[-1]
                pos_final_real = self._grid_a_pos(pos_final[0], pos_final[1])
                dist_final = math.sqrt((pos_final_real[0] - jugador.x)**2 + 
                                     (pos_final_real[1] - jugador.y)**2)
                fitness += max(0, 200 - dist_final)
            
            for pos in ruta:
                if (0 <= pos[0] < self.rows and 0 <= pos[1] < self.cols and
                    grid[pos[0]][pos[1]] == 1):
                    fitness -= 50
            
            if len(ruta) > 2:
                cambios_direccion = 0
                for i in range(2, len(ruta)):
                    dir1 = (ruta[i-1][0] - ruta[i-2][0], ruta[i-1][1] - ruta[i-2][1])
                    dir2 = (ruta[i][0] - ruta[i-1][0], ruta[i][1] - ruta[i-1][1])
                    if dir1 != dir2:
                        cambios_direccion += 1
                fitness -= cambios_direccion * 5 
            individuo['fitness'] = fitness

    def _seleccion_y_reproduccion(self):
      nueva_poblacion = []
        
        self.poblacion_rutas.sort(key=lambda x: x['fitness'], reverse=True)
        nueva_poblacion.extend(self.poblacion_rutas[:5])
        
        while len(nueva_poblacion) < len(self.poblacion_rutas):
            padre1 = self._seleccion_torneo()
            padre2 = self._seleccion_torneo()
            hijo = self._cruce(padre1, padre2)
            nueva_poblacion.append(hijo)
        
        self.poblacion_rutas = nueva_poblacion

    def _seleccion_torneo(self, tamaño_torneo=3):
      candidatos = random.sample(self.poblacion_rutas, 
                                 min(tamaño_torneo, len(self.poblacion_rutas)))
        return max(candidatos, key=lambda x: x['fitness'])

    def _cruce(self, padre1, padre2):
      
      if not padre1['path'] or not padre2['path']:
            return {'path': [], 'fitness': 0}
        
        punto_cruce = random.randint(1, min(len(padre1['path']), len(padre2['path'])) - 1)
        
        nueva_ruta = padre1['path'][:punto_cruce] + padre2['path'][punto_cruce:]
        
        return {'path': nueva_ruta, 'fitness': 0}

    def _mutacion(self, tasa_mutacion=0.1):
      for individuo in self.poblacion_rutas:
            if random.random() < tasa_mutacion and individuo['path']:
                idx = random.randint(0, len(individuo['path']) - 1)
                pos_actual = individuo['path'][idx]
                
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                nueva_pos = (pos_actual[0] + dy, pos_actual[1] + dx)
                
                if (0 <= nueva_pos[0] < self.rows and 
                    0 <= nueva_pos[1] < self.cols):
                    individuo['path'][idx] = nueva_pos

    def _crear_grid_mejorado(self, obstaculos, margen_inflacion=15):
      grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        
        for obstaculo in obstaculos:
            rect_inflado = pygame.Rect(
                obstaculo.x - margen_inflacion,
                obstaculo.y - margen_inflacion,
                obstaculo.ancho + 2 * margen_inflacion,
                obstaculo.alto + 2 * margen_inflacion
            )
            
            for i in range(self.rows):
                for j in range(self.cols):
                    x, y = self._grid_a_pos(i, j)
                    if rect_inflado.collidepoint(x, y):
                        grid[i][j] = 1
        
        return grid

    def _a_star_con_heuristica_mejorada(self, grid, start, goal):
      heap = []
        heapq.heappush(heap, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}
        
        while heap:
            _, current = heapq.heappop(heap)
            
            if current == goal:
                break 
            
            for di in [-1, 0, 1]:
                for dj in [-1, 0, 1]:
                    if di == 0 and dj == 0:
                        continue
                    
                    ni, nj = current[0] + di, current[1] + dj
                    
                    if (0 <= ni < self.rows and 0 <= nj < self.cols and 
                        grid[ni][nj] == 0):
                        
                        move_cost = 1.414 if di != 0 and dj != 0 else 1.0
                        
                        if current in came_from and came_from[current]:
                            prev = came_from[current]
                            prev_dir = (current[0] - prev[0], current[1] - prev[1])
                            curr_dir = (di, dj)
                            if prev_dir != curr_dir:
                                move_cost += 0.1
                        
                        new_cost = cost_so_far[current] + move_cost
                        neighbor = (ni, nj)
                        
                        if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                            cost_so_far[neighbor] = new_cost
                            
                            h_manhattan = abs(goal[0] - ni) + abs(goal[1] - nj)
                            h_euclidiana = math.sqrt((goal[0] - ni)**2 + (goal[1] - nj)**2)
                            heuristica = 0.7 * h_euclidiana + 0.3 * h_manhattan
                            
                            priority = new_cost + heuristica
                            heapq.heappush(heap, (priority, neighbor))
                            came_from[neighbor] = current 
        
        if goal not in came_from:
            return [] 
        
        path = []
        node = goal
        while node is not None:
            path.append(node)
            node = came_from.get(node)
        path.reverse() 
        
        return path

    def _actualizar_historial_jugador(self, jugador):
      self.historial_jugador.append((jugador.x, jugador.y))

    def _pos_a_grid(self, x, y):
      return int(y // self.cell_size), int(x // self.cell_size)

    def _grid_a_pos(self, i, j):
      return j * self.cell_size + self.cell_size // 2, i * self.cell_size + self.cell_size // 2

    def _fuerza_a_accion(self, fx, fy):
      magnitud = math.sqrt(fx**2 + fy**2)
        if magnitud < 0.1:
            return 8  
        
        fx_norm = fx / magnitud
        fy_norm = fy / magnitud
        
        if fx_norm > 0.5:
            dx = 1
        elif fx_norm < -0.5:
            dx = -1
        else:
            dx = 0
            
        if fy_norm > 0.5:
            dy = 1
        elif fy_norm < -0.5:
            dy = -1
        else:
            dy = 0
        
        movimientos = [
            (0, -1), (1, -1), (1, 0), (1, 1),    
            (0, 1), (-1, 1), (-1, 0), (-1, -1),  
            (0, 0)                               
        ]
        
        try:
            return movimientos.index((dx, dy))
        except ValueError:
            return 8

    def _path_a_accion(self, path, start):
      if not path or len(path) < 2:
            return 8 
        
        next_pos = path[1]
        
        di = next_pos[0] - start[0]
        dj = next_pos[1] - start[1]
        
        di = max(-1, min(1, di))
        dj = max(-1, min(1, dj))
        
        movimientos = [
            (0, -1), (1, -1), (1, 0), (1, 1),
            (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, 0)
        ]
        
        try:
            return movimientos.index((dj, di))
        except ValueError:
            return 8

    

    

    

    
      

        
      



          

    
