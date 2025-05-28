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
      



          

    
