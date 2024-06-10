import os

import cv2
import numpy as np

output_folder = "output"
os.makedirs(output_folder, exist_ok=True)
output_filename = os.path.join(output_folder, "processed_image.jpg")

# Carrega a imagem
image = cv2.imread("even_more_currency.jpg")

# Converte para escala de cinza
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# Aplica um filtro de suavização mais forte
blurred = cv2.GaussianBlur(gray, (11, 11), 0)

# Aplica a detecção de bordas de Canny com parâmetros ajustados
edges = cv2.Canny(blurred, 100, 200)

# Aplica dilatação e erosão para fechar buracos e remover ruídos
dilated = cv2.dilate(edges, None, iterations=2)
eroded = cv2.erode(dilated, None, iterations=2)

# Encontra os contornos na imagem processada
contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Itera sobre os contornos encontrados
for contour in contours:
    # Ignora contornos pequenos para evitar detecções falsas
    if cv2.contourArea(contour) < 500:  # Aumenta a área mínima para 500 pixels
        continue

    # Calcula o momento do contorno
    M = cv2.moments(contour)
    if M["m00"] != 0:
        # Calcula o centroide
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])

        # Desenha o centroide na imagem
        cv2.circle(image, (cX, cY), 5, (255, 0, 0), -1)
        cv2.putText(
            image,
            "centroid",
            (cX - 25, cY - 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 0),
            2,
        )

        # Calcula o retângulo delimitador do contorno
        x, y, w, h = cv2.boundingRect(contour)
        # Desenha o retângulo na imagem
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

cv2.imwrite(output_filename, image)

# Open the image using the default image viewer
if os.name == "nt":  # For Windows
    os.startfile(output_filename)
elif os.uname()[0] == "Darwin":  # For macOS
    os.system(f'open "{output_filename}"')
else:  # For Linux and other Unix-like OS
    os.system(f'xdg-open "{output_filename}"')
