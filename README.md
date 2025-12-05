# Robot Dynamics & Vision Control: Automated Pick & Place System

![Language](https://img.shields.io/badge/Python-3.14-blue)
![Platform](https://img.shields.io/badge/Robot-ABB%20IRB%20120-orange)

## 📖 Overview

This project implements an automated **Pick & Place system** integrating Computer Vision and Industrial Robotics. It was designed to identify, locate, and manipulate 3D-printed disks located within a shelving unit based on color classification.

Originally conceived as an academic group project, this repository represents the **functional, refined version** developed personally by the authors to achieve a robust, working industrial prototype.

The system uses a **Python-based vision client** to process static images of the workspace and communicates coordinates via TCP/IP to an **ABB IRB 120 industrial robot** (RAPID server).

## 👥 Authors & Credits

This project is a collaborative effort between:

* **Fabrizio Michele Chiaramonte**  
    * *Role:* **Lead Vision & Software Engineer**
    * *Responsibility:* Developed the Python architecture, image processing algorithms (OpenCV), TCP/IP socket communication, and calibration tools.
    
* **Alberto González García** 
    * *Role:* **Lead Robotics Engineer**
    * *Responsibility:* Developed the RAPID program, motion planning, robot calibration, coordinate logic, and RobotStudio integration.

## ⚙️ Hardware Setup

* **Robot:** ABB IRB 120 (6-axis industrial robot).
* **End-Effector:** Custom 3D-printed "forklift-style" gripper designed to lift objects from below.
* **Objects:** 3D-printed circular disks (Red/Blue) with a bottom slot for the gripper.
* **Environment:** Acrylic shelving unit configured in a 3x3 grid.
* **Connection:** Ethernet link between the Vision PC and the Robot Controller.

## 🚀 Software Architecture

The system operates on a **Client-Server architecture**:

1.  **Vision System (Python Client):**
    * Loads the workspace image (`estanteria.jpg`).
    * **Perspective Correction:** Detects 4 orange markers to warp the image and remove distortion.
    * **Grid Analysis:** Splits the shelving unit into a 3x3 logical grid.
    * **Color Detection:** Uses HSV filtering to identify if a cell contains a Red or Blue part.
    * **User Interface:** Asks the user which color to pick and how many.
    * **Transmission:** Sends `[Row, Column, Height]` data packets to the robot.

2.  **Robot Controller (RAPID Server):**
    * Runs a socket server on Port `9119`.
    * **Calibration:** Performs an initial `row_sweep` to validate positions.
    * **Execution:** Receives coordinates, maps them to physical offsets (mm), and executes a precise approach-lift-retract motion sequence.

## 🛠️ Tech Stack & Requirements

### Python Environment
* **Python:** 3.14
* **OpenCV:** `opencv-python==4.11.0.86`
* **NumPy:** `numpy==2.3.4`

### Robot Environment
* **Language:** RAPID
* **Software:** ABB RobotStudio (for code upload and simulation)

## 📂 Key Files Description

* `vision_communication_integrated.py`: **MAIN SCRIPT.** Handles the full pipeline: image loading, processing, user input, and robot communication.
* `module.mod`: **ROBOT SCRIPT.** The RAPID code running on the ABB controller. Handles the server logic and physical movements.
* `vision.py`: Standalone version of the vision logic (no communication) for testing detection algorithms.
* **Calibration Tools:**
    * `grid_test.py`: GUI tool to visualize and adjust the 3x3 grid overlay parameters (`dx`, `dy`, offsets).
    * `adaptive_color.py`: Tool to sample colors from the image and generate optimal HSV ranges for different lighting conditions.

## 🔧 Installation & Usage

### 1. Robot Setup
1.  Load `module.mod` into the ABB IRB 120 controller using a USB drive or RobotStudio.
2.  Connect the PC to the Robot via Ethernet.
3.  Start the program on the FlexPendant. The robot will perform a calibration move and display: *"Esperando conexion..."* (Waiting for connection).

### 2. PC Setup
1.  Ensure the static image `estanteria.jpg` is in the project folder (captured before operation).
2.  Install dependencies:
    ```bash
    pip install opencv-python numpy
    ```
3.  Run the main script:
    ```bash
    python vision_communication_integrated.py
    ```

### 3. Operation
1.  The Python script will process the image and generate a report.
2.  Follow the terminal prompt:
    > Enter the part type you want to pick (1 or 2):
3.  The system will filter available parts and send coordinates one by one to the robot.

## 🔮 Future Improvements
* **Real-time Capture:** Integration with Raspberry Pi Camera for live video feed analysis.
* **Z-Axis Logic:** Implementation of "Height" logic to handle stacked objects (currently implemented in protocol but unused in motion planning).

---
*Project developed in Universidad Loyola de Andalucia Octubre - Diciembre 2025.*
