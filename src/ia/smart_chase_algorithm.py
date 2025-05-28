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
      self._actualizar_historial_jugador(jugador) # Actualiza el historial de posiciones del jugador para la predicción.

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

        
      



          

    
