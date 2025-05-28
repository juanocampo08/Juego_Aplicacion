import sys

sys.path.append("src")

from utils.modos_juego import jugar_con_modelo_mejorado, entrenar_modelo_mejorado

def main(modo = "jugar", modo_ia = "hibrido", modelo_path = "src/ml_model/best_model", velocidad_juego = 240, timesteps = 300000):
    MODO = modo
    MODO_IA = modo_ia
    MODELO_PATH = modelo_path
    VELOCIDAD_JUEGO = velocidad_juego
    TIMESTEPS = timesteps

    print("Juego de Persecución con IA Súper Avanzada")
    print("=" * 60)

    try:
        if MODO == "entrenar":
            entrenar_modelo_mejorado(
                modelo_path = MODELO_PATH,
                timesteps = TIMESTEPS,
                modo_ia = MODO_IA,
                velocidad_juego = VELOCIDAD_JUEGO
            )
        elif MODO == "jugar":
            jugar_con_modelo_mejorado(
                modelo_path = MODELO_PATH,
                modo_ia = MODO_IA
            )
        else:
            print("Error: Modo no válido. Usa 'entrenar' o 'jugar'")
            return

    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario")
        return

    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        return
    return

if __name__ == "__main__":
    """
        Configuración disponible:
        - MODO: "entrenar" para entrenar el modelo, "jugar" para ejecutar el juego
        - MODO_IA: Tipo de inteligencia artificial del enemigo
        - MODELO_PATH: Ruta donde se guardará el modelo entrenado
        - VELOCIDAD_JUEGO: FPS del juego (mayor velocidad = entrenamiento más rápido)
        - TIMESTEPS: Número de pasos de entrenamiento (solo para modo entrenar)
    """
    main(modo="jugar", modo_ia="hibrido", modelo_path="src/ml_model/best_model", velocidad_juego=240, timesteps=300000)