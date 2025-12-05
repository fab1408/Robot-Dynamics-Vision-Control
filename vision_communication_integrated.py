import cv2
import numpy as np
import socket
import struct
from time import sleep
import os
from datetime import datetime

# ========================================
# CONFIGURATION
# ========================================
ROBOT_IP = "192.168.125.1"
ROBOT_PORT = 9119

# ========================================
# CREATE OUTPUT FOLDER
# ========================================
# Create folder with timestamp
output_folder = "results"
os.makedirs(output_folder, exist_ok=True)
print(f"Output folder created: {output_folder}\n")

# ========================================
# LOAD AND SAVE ORIGINAL IMAGE
# ========================================
ruta = r"C:\Users\USER\Downloads\vision_project_robotics\vision_project\estanteria.jpg"
img = cv2.imread(ruta)

if img is None:
    print(f"ERROR: Cannot load image from {ruta}")
    exit()

cv2.imwrite(os.path.join(output_folder, "01_imagen_original.jpg"), img)

# ========================================
# SHELVING CONFIGURATION PARAMETERS
# ========================================
B = 48              # Shelving width (cm)
H = 37              # Shelving height (cm)
N = 800             # Width in pixels
M = 600             # Height in pixels

rel_h = N/B         # Horizontal ratio (pixels/cm)
rel_v = M/H         # Vertical ratio (pixels/cm)

b = 8*rel_h         # Test width in pixels
a = 1*rel_v         # Test height in pixels

# ========================================
# IMAGE ROTATION AND COLOR CONVERSION
# ========================================
rw = 800
rh = 600
center = (rw / 2, rh / 2)
Mr = cv2.getRotationMatrix2D(center, 180, 1)
imagen = cv2.warpAffine(img, Mr, (800, 600))
cv2.imwrite(os.path.join(output_folder, "02_imagen_rotada.jpg"), imagen)

imagen_hsv = cv2.cvtColor(imagen, cv2.COLOR_BGR2HSV)
cv2.imwrite(os.path.join(output_folder, "03_imagen_hsv.jpg"), imagen_hsv)
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
# CORNER DETECTION USING ORANGE MARKERS
# ========================================
masc_nar = cv2.inRange(imagen_hsv, naranja_bajos, naranja_altos)

kernel = np.ones((1, 1), np.uint8)
masc_nar = cv2.morphologyEx(masc_nar, cv2.MORPH_OPEN, kernel)
masc_nar = cv2.morphologyEx(masc_nar, cv2.MORPH_CLOSE, kernel)
cv2.imwrite(os.path.join(output_folder, "04_mascara_naranja.jpg"), masc_nar)

contours, hierarchy = cv2.findContours(masc_nar, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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

if len(corners) != 4:
    print(f"ERROR: Expected 4 corners but found {len(corners)}")
    print("Adjust orange color thresholds or check lighting")
    exit()

corners_sorted = sorted(corners, key=lambda x: x[1])
top_corners = sorted(corners_sorted[:2], key=lambda x: x[0])
bottom_corners = sorted(corners_sorted[2:], key=lambda x: x[0])

esq4 = top_corners[0]      # Top-Left
esq1 = top_corners[1]      # Top-Right
esq2 = bottom_corners[1]   # Bottom-Right
esq3 = bottom_corners[0]   # Bottom-Left

img_with_corners = imagen_bgr.copy()
cv2.circle(img_with_corners, tuple(esq4), 15, (255, 0, 0), -1)
cv2.circle(img_with_corners, tuple(esq1), 15, (0, 255, 0), -1)
cv2.circle(img_with_corners, tuple(esq2), 15, (0, 0, 255), -1)
cv2.circle(img_with_corners, tuple(esq3), 15, (255, 255, 0), -1)

cv2.putText(img_with_corners, "TL", (esq4[0]-30, esq4[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
cv2.putText(img_with_corners, "TR", (esq1[0]+15, esq1[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
cv2.putText(img_with_corners, "BR", (esq2[0]+15, esq2[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
cv2.putText(img_with_corners, "BL", (esq3[0]-30, esq3[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

cv2.imwrite(os.path.join(output_folder, "05_esquinas_detectadas.jpg"), img_with_corners)

# ========================================
# PERSPECTIVE CORRECTION
# ========================================
N = 800
M = 600

pts1 = np.float32([esq4, esq1, esq2, esq3])
pts2 = np.float32([[0, 0], [N, 0], [N, M], [0, M]])

transformada = cv2.getPerspectiveTransform(pts1, pts2)
imagen_nueva_hsv = cv2.warpPerspective(imagen_hsv, transformada, (N, M))
imagen_nueva_bgr = cv2.warpPerspective(imagen_bgr, transformada, (N, M))

cv2.imwrite(os.path.join(output_folder, "06_perspectiva_corregida.jpg"), imagen_nueva_bgr)

# ========================================
# COLOR DETECTION ON CORRECTED IMAGE
# ========================================
masc_rojo = cv2.inRange(imagen_nueva_hsv, rojo_bajos, rojo_altos)
masc_azul = cv2.inRange(imagen_nueva_hsv, azul_bajos, azul_altos)

cv2.imwrite(os.path.join(output_folder, "07_mascara_azul.jpg"), masc_azul)
cv2.imwrite(os.path.join(output_folder, "08_mascara_roja.jpg"), masc_rojo)

# ========================================
# GRID SCANNING AND PART DETECTION
# ========================================
perspective_image = imagen_nueva_bgr.copy()

x, y = 0, 0
dx, dy = 265, 200
w, h = 265, 200
pct_corte = 0.2

board = np.zeros(9)
k = 0

for i in range(0, 3):
    for j in range(0, 3):
        cell_x = x + (j * dx)
        cell_y = y + (i * dy)
        
        cv2.rectangle(perspective_image, 
                     (cell_x, cell_y), 
                     (cell_x + w, cell_y + h), 
                     (0, 255, 0), 2)
        
        center_x = cell_x + w // 2
        center_y = cell_y + h // 2
        
        roi_azul = masc_azul[cell_y:cell_y + h, cell_x:cell_x + w]
        roi_rojo = masc_rojo[cell_y:cell_y + h, cell_x:cell_x + w]
        
        count_azul = cv2.countNonZero(roi_azul)
        count_rojo = cv2.countNonZero(roi_rojo)
        
        if count_azul > pct_corte or count_rojo > pct_corte:
            if count_azul > count_rojo:
                board[k] = 1
                cv2.putText(perspective_image, 'AZUL', 
                           (center_x +10, center_y-50), 
                           cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 0, 0), 2)
            else:
                board[k] = 2
                cv2.putText(perspective_image, 'ROJA', 
                           (center_x +10, center_y-50), 
                           cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 255), 2)
        else:
            board[k] = 0
            cv2.putText(perspective_image, 'VACIO', 
                       (center_x - 50, center_y), 
                       cv2.FONT_HERSHEY_DUPLEX, 1.0, (128, 128, 128), 2)
        
        k = k + 1
        
        cv2.putText(perspective_image, f"{k-1}", 
                   (cell_x + 10, cell_y + 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

print(f"Detection results: {board}")
cv2.imwrite(os.path.join(output_folder, "09_deteccion_final.jpg"), perspective_image)
longitud_board = len(board)

# ========================================
# DATA ARRAY CONSTRUCTION
# ========================================
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
        
        data_array.append([fila, columna, int(color)])
        
        if color == 1:
            num_azules += 1
        elif color == 2:
            num_rojos += 1
    
    indice_disco = indice_disco + 1

available_indices = [num_azules, num_rojos]
print(f"Available parts: {available_indices[0]} Blue, {available_indices[1]} Red")

# ========================================
# SAVE DETECTION REPORT
# ========================================
report_path = os.path.join(output_folder, "00_detection_report.txt")
with open(report_path, 'w') as f:
    f.write("="*50 + "\n")
    f.write("DETECTION REPORT\n")
    f.write("="*50 + "\n\n")
    f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Image source: {ruta}\n\n")
    f.write(f"Corners detected: {len(corners)}\n")
    f.write(f"  - Top-Left: {esq4}\n")
    f.write(f"  - Top-Right: {esq1}\n")
    f.write(f"  - Bottom-Right: {esq2}\n")
    f.write(f"  - Bottom-Left: {esq3}\n\n")
    f.write(f"Detection results:\n")
    f.write(f"  - Blue parts: {num_azules}\n")
    f.write(f"  - Red parts: {num_rojos}\n")
    f.write(f"  - Total parts: {num_azules + num_rojos}\n\n")
    f.write(f"Board state: {board}\n\n")
    f.write("Part positions (row, col, color):\n")
    for idx, pieza in enumerate(data_array):
        color_name = "Blue" if pieza[2] == 1 else "Red"
        f.write(f"  Part {idx+1}: Row={pieza[0]}, Col={pieza[1]}, Color={color_name}\n")

print(f"Detection report saved: {report_path}")

# ========================================
# COMMUNICATION FUNCTION
# ========================================
def SendMove(data_vector):
    """
    Send movement command to robot
    data_vector: [row, column, height]
    """
    print(f'Sending move: Row={data_vector[0]}, Col={data_vector[1]}, Height={data_vector[2]}')
    
    try:
        # Create socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(60)  # 1 min timeout
        
        # Connect to robot server
        print(f"Connecting to robot at {ROBOT_IP}:{ROBOT_PORT}...")
        s.connect((ROBOT_IP, ROBOT_PORT))
        print("Connected!")
        
        # Pack the three values as 32-bit integers
        message = struct.pack('iii', data_vector[0], data_vector[1], data_vector[2])
        s.sendall(message)
        print(f"Data sent: {len(message)} bytes")
        
        # Wait for server response
        response = s.recv(1024)
        print(f'Response received: {response.decode()}')
        
        # Close socket
        s.close()
        print("Connection closed\n")
        return True
        
    except socket.timeout:
        print("ERROR: Connection timeout")
        return False
    except ConnectionRefusedError:
        print("ERROR: Connection refused. Is the robot program running?")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

# ========================================
# USER INTERACTION AND EXECUTION
# ========================================
print("\n" + "="*50)
print("ROBOT PART PICKING SYSTEM")
print("="*50)

print("\nAvailable part types:")
print("1 - Blue parts")
print("2 - Red parts")

decision = int(input("\nEnter the part type you want to pick (1 or 2): "))
quantity = int(input("Enter the number of parts to pick: "))

# Filter data_array to only include parts matching user's color choice
piezas_filtradas = []
for pieza in data_array:
    if pieza[2] == decision:
        piezas_filtradas.append(pieza)

# Limit quantity to available parts
actual_quantity = min(quantity, len(piezas_filtradas))

print(f"\n{len(piezas_filtradas)} parts of type {decision} available")
print(f"Will pick {actual_quantity} parts")

if actual_quantity == 0:
    print("No parts available to pick!")
    exit()

# Prepare positions to pick
posiciones_a_recoger = piezas_filtradas[:actual_quantity]

print("STARTING COMMUNICATION WITH ROBOT")

# Save execution log
execution_log_path = os.path.join(output_folder, "10_execution_log.txt")
with open(execution_log_path, 'w') as f:
    f.write("EXECUTION LOG\n")
    f.write(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Color selected: {'Blue' if decision == 1 else 'Red'}\n")
    f.write(f"Quantity requested: {quantity}\n")
    f.write(f"Quantity to pick: {actual_quantity}\n\n")
    f.write("Parts to pick:\n")
    for idx, pieza in enumerate(posiciones_a_recoger):
        f.write(f"  Part {idx+1}: Row={pieza[0]}, Col={pieza[1]}\n")
    f.write("\n")

# Send coordinates to robot one by one
success_count = 0
for idx, pieza in enumerate(posiciones_a_recoger):
    print(f"\n--- Part {idx+1}/{actual_quantity} ---")
    print(f"Position: Row={pieza[0]}, Col={pieza[1]}, Color={'Blue' if pieza[2]==1 else 'Red'}")
    
    # Add height=1 as third parameter (since we ignore height)
    data_to_send = [pieza[0], pieza[1], 1]
    
    success = SendMove(data_to_send)
    
    # Log result
    with open(execution_log_path, 'a') as f:
        f.write(f"Part {idx+1}: {'SUCCESS' if success else 'FAILED'} at {datetime.now().strftime('%H:%M:%S')}\n")
    
    if success:
        success_count += 1
    else:
        print(f"Failed to send part {idx+1}. Stopping...")
        break
    
    # Wait between sends
    if idx < actual_quantity - 1:
        print("Waiting 3 seconds before next part...")
        sleep(3)

# Final summary
with open(execution_log_path, 'a') as f:
    f.write(f"\n{'='*50}\n")
    f.write(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Successful picks: {success_count}/{actual_quantity}\n")
    f.write(f"{'='*50}\n")

print("\n" + "="*50)
print("PROCESS COMPLETED")
print(f"Successful picks: {success_count}/{actual_quantity}")
print(f"All results saved in: {output_folder}")
print("="*50)