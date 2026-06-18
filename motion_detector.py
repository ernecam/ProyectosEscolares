import cv2
import argparse
import numpy as np

# Argumento para recibir el video
args = argparse.ArgumentParser()
args.add_argument("-v", "--video", required=True, help="Path to the video")
ap = vars(args.parse_args())

cap = cv2.VideoCapture(ap["video"])

# Comprobación de video
if not cap.isOpened():
    print("No se pudo abrir el video.")
    exit()

# Parámetros que se configuraron
FPS_PROCESAMIENTO = 15     # Cuadros por segundo que se procesarán
THRESHOLD_VAL = 15         # Sensibilidad del cambio por píxel
VARIACION_MINIMA = 0.5     # Porcentaje mínimo de cambio para considerar movimiento

# Datos del video original para su mejor procesamiento
fps_original = cap.get(cv2.CAP_PROP_FPS)
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"FPS original: {fps_original:.2f}")
print(f"Procesando a {FPS_PROCESAMIENTO} fps...")

# Calcular salto de frames para que se procese el número que queremos
salto_frames = int(round(fps_original / FPS_PROCESAMIENTO))
if salto_frames < 1:
    salto_frames = 1

# Lectura del primer Frame
ret, frame_anterior = cap.read()
if not ret:
    print("No se pudo leer el primer frame.")
    exit()

# Preprocesamiento inicial para mejorar la imagen
frame_anterior = cv2.cvtColor(frame_anterior, cv2.COLOR_BGR2GRAY)
frame_anterior = cv2.equalizeHist(frame_anterior)
frame_anterior = cv2.GaussianBlur(frame_anterior, (9, 9), 0)

frame_index = 0

print("\nPresiona 'q' para salir.\n")

while True:
    # Saltar frames para controlar velocidad de análisis
    for _ in range(salto_frames - 1):
        cap.grab()

    ret, frame_actual = cap.read()
    if not ret:
        break

    frame_index += salto_frames

    # Convertir y mejorar imagen final
    frame_gray = cv2.cvtColor(frame_actual, cv2.COLOR_BGR2GRAY)
    frame_gray = cv2.equalizeHist(frame_gray)
    frame_gray = cv2.GaussianBlur(frame_gray, (9, 9), 0)

    # Resta entre imágenes
    diferencia = cv2.absdiff(frame_anterior, frame_gray)

    # Calcular variación para la detección de movimiento
    variacion = np.sum(diferencia > THRESHOLD_VAL) / diferencia.size * 100

    cv2.imshow("Video Original", frame_actual)

    # Si hay movimiento, hacer una pausa
    if variacion > VARIACION_MINIMA:
        tiempo_seg = frame_index / fps_original
        minutos = int(tiempo_seg // 60)
        segundos = int(tiempo_seg % 60)
        print(f"\n Movimiento detectado ({variacion:.2f}% cambio) en {minutos:02d}:{segundos:02d}")

        # Pausar el video
        print("Video pausado. Presiona ESPACIO para continuar...")
        while True:
            tecla = cv2.waitKey(0) & 0xFF
            if tecla == ord(' '):   # Espacio para continuar
                print("▶ Continuando video...\n")
                break
            elif tecla == ord('q'):  # 'q' para salir
                cap.release()
                cv2.destroyAllWindows()
                exit()

    # Actualizar frame anterior
    frame_anterior = frame_gray.copy()

    # Control de avance normal
    if cv2.waitKey(int(1000 / FPS_PROCESAMIENTO)) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
