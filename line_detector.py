import cv2
import numpy as np
import argparse

# Argumentos que recibe el programa
args = argparse.ArgumentParser()
args.add_argument("-v", "--video", required=True, help="Path to the video")
args.add_argument("-k", "--ksize", required=True, type=int, help="Size of kernel")
ap = vars(args.parse_args())

# Configuración de valores 
canny_th1 = 150
canny_th2 = 230

L_offset, A_offset, B_offset = -125, 0, 0
low, high = 10, 180

size = ap["ksize"]

# Funciones aplicadas

def apply_gamma(image, gamma):
    invGamma = 1.0 / gamma
    table = np.array([(i / 255.0) ** invGamma * 255 for i in np.arange(256)]).astype("uint8")
    return cv2.LUT(image, table)

def adaptive_gamma_roi(frame, roi):
    x1, y1, x2, y2 = roi
    gray_roi = cv2.cvtColor(frame[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)

    # Estadísticas de la ROI
    mean_intensity = np.mean(gray_roi)
    min_val, max_val = np.min(gray_roi), np.max(gray_roi)
    dynamic_range = max_val - min_val

    # Selección de media
    if mean_intensity < 80:
        base_percentile = 25   
    elif mean_intensity > 150:
        base_percentile = 100   
    else:
        base_percentile = 60   

    # Primer ajuste según contraste
    if dynamic_range < 20:
        # poco contraste → mover hacia el centro
        dynamic_percentile = (base_percentile + 50) / 2
    elif dynamic_range > 100:
        # mucho contraste → empujar hacia extremos
        if base_percentile < 50:
            dynamic_percentile = max(20, base_percentile - 10)
        else:
            dynamic_percentile = min(80, base_percentile + 10)
    else:
        dynamic_percentile = base_percentile

    # Intensidad de referencia
    perc_intensity = np.percentile(gray_roi, dynamic_percentile)

    # Relación luz - gamma
    gamma_val = 2.0 - (perc_intensity / 45.0)
    gamma_val = np.clip(gamma_val, 0.08, 10.0)

    corrected = apply_gamma(frame, gamma_val)
    return corrected, gamma_val, dynamic_percentile, dynamic_range


def calc_contrast_dynamic(gray, mask, low, high):
    if mask is not None:
        gray = cv2.bitwise_and(gray, gray, mask=mask)
    if not np.any(gray):
        return 0, 0
    if low is not None and high is not None:
        gray = np.clip(gray, low, high)
    vals = gray[np.nonzero(gray)]
    if len(vals) == 0:
        return 0, 0
    min_val, max_val = np.min(vals), np.max(vals)
    contraste = max_val - min_val
    rango_dinamico = max_val / min_val if min_val > 0 else 0
    return contraste, rango_dinamico

# Procesamiento del video
cap = cv2.VideoCapture(ap["video"])
if not cap.isOpened():
    print("Error al abrir el video")
    exit()

roi = (70, 200, 600, 350)  # Región de interés (x1, y1, x2, y2)

# Definir el codec y crear el VideoWriter
fourcc = cv2.VideoWriter_fourcc(*'mp4v')   
fps = cap.get(cv2.CAP_PROP_FPS)            
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# guardar video en formato mp4
out = cv2.VideoWriter("output_otsu.mp4v", fourcc, fps, (width, height))

#out = cv2.VideoWriter("output_combined.mp4", fourcc, fps, (width*2, height))




while True:
    ret, frame = cap.read()
    if not ret:
        # cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # ciclado del video
        break # Salida
        continue

    # Paso 1: Gamma adaptativo solo en ROI
    gamma_corrected, gamma_val,_,_ = adaptive_gamma_roi(frame, roi)

    # Paso 2: Ecualización de histograma solo en L
    lab = cv2.cvtColor(gamma_corrected, cv2.COLOR_BGR2Lab)
    l, a, b = cv2.split(lab)
    l = cv2.equalizeHist(l) 
    lab_eq = cv2.merge([l, a, b])
    lab_bgr = cv2.cvtColor(lab_eq, cv2.COLOR_Lab2BGR)

    # Paso 3: aplicar offsets en L A B
    l = cv2.add(l, L_offset)
    a = cv2.add(a, A_offset)
    b = cv2.add(b, B_offset)
    lab_adjusted = cv2.merge([l, a, b])
    lab_bgr = cv2.cvtColor(lab_adjusted, cv2.COLOR_Lab2BGR)

    # Paso 4: aplicar filtro bilateral
    imgb = cv2.bilateralFilter(lab_bgr, size, 21, 21)

    # Paso 5: auto-contraste
    gray = cv2.cvtColor(lab_bgr, cv2.COLOR_BGR2GRAY)
    gray_clipped = np.clip(gray, low, high)
    gray_adj = cv2.normalize(gray_clipped, None, 50, 200, cv2.NORM_MINMAX)

    # Paso 6: contraste y rango dinámico en ROI
    mask = np.zeros_like(gray, dtype=np.uint8)
    cv2.rectangle(mask, (roi[0], roi[1]), (roi[2], roi[3]), 255, -1)
    contraste, rango_dinamico = calc_contrast_dynamic(gray_adj, mask, low, high)

    # Paso 7: detección de bordes Canny
    edges = cv2.Canny(gray_adj, canny_th1, canny_th2)

    # Paso 8: Umbralización de Otsu
    _, otsu = cv2.threshold(gray_adj, 150, 240, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Aplicar máscara negra fuera de ROI
    otsu_masked = cv2.bitwise_and(otsu, otsu, mask=mask)

    # Convierte a BGR para concatenar con frame
    otsu_bgr = cv2.cvtColor(otsu_masked, cv2.COLOR_GRAY2BGR)

    # Ventana combinada para video final
    combined = cv2.hconcat([frame, otsu_bgr])
    cv2.imshow("Original + Otsu", combined)

    # Resultados de filtros
    cv2.rectangle(frame, (roi[0], roi[1]), (roi[2], roi[3]), (0, 255, 0), 2)
    cv2.imshow("Original", frame)
    cv2.imshow("Gamma adaptativo", gamma_corrected)
    cv2.imshow("Lab ecualizado", lab_bgr)
    cv2.imshow("Filtrado", imgb)
    cv2.imshow("Contraste", gray_adj)
    cv2.imshow("Canny", edges)
    cv2.imshow("Otsu", otsu)

    # Guarda el video
    otsu_bgr = cv2.cvtColor(otsu_masked, cv2.COLOR_GRAY2BGR)
    out.write(otsu_bgr)

    #out.write(combined)
    
    if cv2.waitKey(15) & 0xFF == ord('q'):
        break

cap.release()

out.release()

cv2.destroyAllWindows()
