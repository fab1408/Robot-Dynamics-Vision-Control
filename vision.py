import sqlite3
import cv2
import numpy as np
import random
import threading
import socket
from time import sleep
import struct
import sys
import os
#from picamera.array import PiRGBArray
#from picamera import PiCamera

# ========================================
# CREATE OUTPUT FOLDER
# ========================================
output_folder = "resultados"
os.makedirs(output_folder, exist_ok=True)
print(f"Output folder: {output_folder}\n")

# ========================================
# INITIAL IMAGE CAPTURE 
# ========================================
# Code for capturing image with Raspberry Pi Camera
## camera=PiCamera()
## rw = 800
## rh = 600
## camera.resolution=(rw,rh)
## camera.start_preview()
## sleep(3)
## camera.capture('memoria.jpg')
## camera.stop_preview()

# ========================================
# LOAD AND SAVE ORIGINAL IMAGE
# ========================================
ruta = r"C:\Users\USER\Downloads\vision_project_robotics\vision_project\estanteria.jpg"
img = cv2.imread(ruta)
cv2.imwrite(os.path.join(output_folder, "Imagen original.jpg"), img)

# ========================================
# SHELVING CONFIGURATION PARAMETERS
# ========================================
# Real shelving dimensions in centimeters
B = 48              # Shelving width (cm)
H = 37              # Shelving height (cm)

# Target image dimensions in pixels
N = 800             # Width in pixels
M = 600             # Height in pixels

# Conversion ratios: pixels per centimeter
rel_h = N/B         # Horizontal ratio (pixels/cm)
rel_v = M/H         # Vertical ratio (pixels/cm)

# Shelving geometry translated to pixels
b = 8*rel_h         # Test width in pixels
a = 1*rel_v         # Test height in pixels
v0 = 3*rel_v        # Vertical coordinate of position (0,0)
h0 = 8.1*rel_h      # Horizontal coordinate of position (0,0)
hp = 14.8*rel_h     # Horizontal spacing between parts
vpn = 2*rel_v       # Vertical spacing between parts in same row
vp = 11.4*rel_v     # Height of each row

# Shelving structure configuration
num_est = 3         # Number of rows
num_col = 3         # Number of columns
num_p_col = 1.5     # Piling height factor

# Detection variables
lim = a*b*0.3*255   # Threshold for validating part presence
n = 0               # Counter variable
num_fila = int(num_p_col*num_est)       # Total number of rows
mpiezas = np.zeros((num_fila,num_col))  # Matrix storing part locations

# ========================================
# IMAGE ROTATION AND COLOR CONVERSION
# ========================================
rw = 800
rh = 600
center = (rw / 2, rh / 2)
Mr = cv2.getRotationMatrix2D(center, 180, 1)
imagen = cv2.warpAffine(img, Mr, (800, 600))
cv2.imwrite(os.path.join(output_folder, 'cap_rot.jpg'), imagen)

# Convert to HSV for color detection
imagen_hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
cv2.imwrite(os.path.join(output_folder, "Prueba1.jpg"), imagen_hsv)

# Keep a BGR version for display
imagen_bgr = imagen.copy()

# ========================================
# COLOR RANGES FOR MASK DETECTION 
# ========================================

# BLUE (HSV)
azul_bajos = np.array([98, 159, 162], dtype=np.uint8)
azul_altos = np.array([103, 209, 226], dtype=np.uint8)

# RED (HSV)
rojo_bajos = np.array([173, 190, 170], dtype=np.uint8)
rojo_altos = np.array([177, 245, 211], dtype=np.uint8)

# ORANGE (HSV)
naranja_bajos = np.array([3, 154, 230], dtype=np.uint8)
naranja_altos = np.array([5, 207, 244], dtype=np.uint8)

# ========================================
# CORNER DETECTION USING ORANGE MARKERS2
# ========================================
# Create orange mask
masc_nar = cv2.inRange(imagen_hsv, naranja_bajos, naranja_altos)

# Apply morphological operations to reduce noise
kernel = np.ones((1, 1), np.uint8)
masc_nar = cv2.morphologyEx(masc_nar, cv2.MORPH_OPEN, kernel)
masc_nar = cv2.morphologyEx(masc_nar, cv2.MORPH_CLOSE, kernel)
cv2.imwrite(os.path.join(output_folder, 'masc_nar.jpg'), masc_nar)

# Find ALL contours
contours, hierarchy = cv2.findContours(masc_nar, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Filter and get centers of all orange circles
corners = []
for contour in contours:
    area = cv2.contourArea(contour)
    if area > 100:
        M = cv2.moments(contour)
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            corners.append([cx, cy])

print(f"Valid corners found: {len(corners)}")

# Check if we found exactly 4 corners
if len(corners) != 4:
    print(f"ERROR: Expected 4 corners but found {len(corners)}")
    print("Adjust orange color thresholds or check lighting")
    exit()

# Sort corners
corners_sorted = sorted(corners, key=lambda x: x[1])
top_corners = sorted(corners_sorted[:2], key=lambda x: x[0])
bottom_corners = sorted(corners_sorted[2:], key=lambda x: x[0])

esq4 = top_corners[0]      # Top-Left
esq1 = top_corners[1]      # Top-Right
esq2 = bottom_corners[1]   # Bottom-Right
esq3 = bottom_corners[0]   # Bottom-Left

# Draw corners on BGR image for visualization
img_with_corners = imagen_bgr.copy()
cv2.circle(img_with_corners, tuple(esq4), 15, (255, 0, 0), -1)
cv2.circle(img_with_corners, tuple(esq1), 15, (0, 255, 0), -1)
cv2.circle(img_with_corners, tuple(esq2), 15, (0, 0, 255), -1)
cv2.circle(img_with_corners, tuple(esq3), 15, (255, 255, 0), -1)

cv2.putText(img_with_corners, "TL", (esq4[0]-30, esq4[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
cv2.putText(img_with_corners, "TR", (esq1[0]+15, esq1[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
cv2.putText(img_with_corners, "BR", (esq2[0]+15, esq2[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
cv2.putText(img_with_corners, "BL", (esq3[0]-30, esq3[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

cv2.imwrite(os.path.join(output_folder, 'corners_detected.jpg'), img_with_corners)

# ========================================
# PERSPECTIVE CORRECTION
# ========================================
N = 800  # Target width
M = 600  # Target height

pts1 = np.float32([esq4, esq1, esq2, esq3])
pts2 = np.float32([[0, 0], [N, 0], [N, M], [0, M]])

# Apply perspective transformation to HSV image
transformada = cv2.getPerspectiveTransform(pts1, pts2)
imagen_nueva_hsv = cv2.warpPerspective(imagen_hsv, transformada, (N, M))

# Also transform BGR for display
imagen_nueva_bgr = cv2.warpPerspective(imagen_bgr, transformada, (N, M))

cv2.imwrite(os.path.join(output_folder, 'perspectiva.jpg'), imagen_nueva_bgr)

# ========================================
# COLOR DETECTION ON CORRECTED IMAGE
# ========================================
masc_rojo = cv2.inRange(imagen_nueva_hsv, rojo_bajos, rojo_altos)
masc_azul = cv2.inRange(imagen_nueva_hsv, azul_bajos, azul_altos)

# Save masks for debugging
cv2.imwrite(os.path.join(output_folder, 'masc_azul.jpg'), masc_azul)
cv2.imwrite(os.path.join(output_folder, 'masc_rojo.jpg'), masc_rojo)

# ========================================
# GRID SCANNING AND PART DETECTION
# ========================================
perspective_image = imagen_nueva_bgr.copy()

# Grid positioning parameters
x, y = 0, 0
dx, dy = 265, 200
w, h = 265, 200
pct_corte = 0.2

board = np.zeros(9)
k = 0

# Scan 3x3 grid
for i in range(0, 3):
    for j in range(0, 3):
        cell_x = x + (j * dx)
        cell_y = y + (i * dy)
        
        # Draw detection rectangle
        cv2.rectangle(perspective_image, 
                     (cell_x, cell_y), 
                     (cell_x + w, cell_y + h), 
                     (0, 255, 0), 2)
        
        # Calculate center
        center_x = cell_x + w // 2
        center_y = cell_y + h // 2
        
        # Extract ROI for BOTH colors
        roi_azul = masc_azul[cell_y:cell_y + h, cell_x:cell_x + w]
        roi_rojo = masc_rojo[cell_y:cell_y + h, cell_x:cell_x + w]
        
        # Count pixels of each color
        count_azul = cv2.countNonZero(roi_azul)
        count_rojo = cv2.countNonZero(roi_rojo)
        
        # Determine which color has MORE pixels
        if count_azul > pct_corte or count_rojo > pct_corte:
            if count_azul > count_rojo:
                # Blue has more pixels
                board[k] = 1
                cv2.putText(perspective_image, 'AZUL', 
                           (center_x +10, center_y-50), 
                           cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 0, 0), 2)
            else:
                # Red has more pixels
                board[k] = 2
                cv2.putText(perspective_image, 'ROJA', 
                           (center_x +10, center_y-50), 
                           cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 255), 2)
        else:
            # No significant color detected
            board[k] = 0
            cv2.putText(perspective_image, 'VACIO', 
                       (center_x - 50, center_y), 
                       cv2.FONT_HERSHEY_DUPLEX, 1.0, (128, 128, 128), 2)
        
        k = k + 1
        
        # Draw cell number
        cv2.putText(perspective_image, f"{k-1}", 
                   (cell_x + 10, cell_y + 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

print(f"Detection results: {board}")
cv2.imwrite(os.path.join(output_folder, 'final3x3.jpg'), perspective_image)
longitud_board = len(board)


# ========================================
# USER INTERACTION: PART SELECTION
# ========================================
print("Available part types:")
print("1 - Blue parts")
print("2 - Red parts")

decision = int(input("Enter the part type you want to pick (1 or 2): "))
quantity = int(input("Enter the number of parts to pick: "))

# ========================================
# DATA ARRAY CONSTRUCTION
# ========================================
# Build structured data from board array
indice_disco = 0
num_azules = 0
num_rojos = 0
available_indices = [0, 0]
data_array = []

for k in range(longitud_board):
    color = board[k]
    if color != 0:
        fila = k // 3       # Calculate row index
        columna = k % 3     # Calculate column index
        
        # Append [row, column, color] to data array
        data_array.append([fila, columna, int(color)])
        
        if color == 1:
            num_azules += 1  # Count blue parts
        elif color == 2:
            num_rojos += 1   # Count red parts
    
    indice_disco = indice_disco + 1

# Store available part counts [blue_count, red_count]
available_indices = [num_azules, num_rojos]
print(f"Available parts: {available_indices[0]} Blue, {available_indices[1]} Red")

# ========================================
# FILTER PARTS BY USER SELECTION
# ========================================
# Filter data_array to only include parts matching user's color choice
piezas_filtradas = []
for pieza in data_array:
    if pieza[2] == decision:  # pieza[2] contains the color (1 or 2)
        piezas_filtradas.append(pieza)

# Limit quantity to available parts
actual_quantity = min(quantity, len(piezas_filtradas))

# Select positions to pick (up to actual_quantity)
posiciones_a_recoger = piezas_filtradas[:actual_quantity]
print(f"{len(posiciones_a_recoger)} parts will be prepared for pickup.")

# ========================================
# OUTPUT PARTS TO PICK
# ========================================
print("\nParts to pick (coordinates):")
for pieza in posiciones_a_recoger:
    print(pieza)