import cv2
import time
import json
import os
import threading
import torch
import numpy as np
import socket
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont
from pythonosc import udp_client

class YOLODetector:
    def __init__(self, model_name: str = "yolov8n.pt"):
        print(f"[1/3] Cargando modelo YOLO ({model_name})...")
        self.model = YOLO(model_name)
        self.frame = None
        self.results = None
        self.running = True
        self.new_frame_event = threading.Event()
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()
        self.last_inference_time = 0.01
        
        # Detectar dispositivo
        self.device_info = "CPU"
        if torch.cuda.is_available():
            self.device_info = f"GPU: {torch.cuda.get_device_name(0)}"
            print(f"[*] CUDA detectado! Usando {self.device_info}")
        else:
            print("[!] CUDA no disponible, usando CPU.")

    def _detection_loop(self):
        while self.running:
            self.new_frame_event.wait()
            if self.frame is not None:
                start = time.time()
                self.results = self.model(self.frame, verbose=False)[0]
                self.last_inference_time = time.time() - start
            self.new_frame_event.clear()

    def update_frame(self, frame):
        if not self.new_frame_event.is_set():
            self.frame = frame.copy()
            self.new_frame_event.set()

    def stop(self):
        self.running = False
        self.new_frame_event.set()

def load_config():
    config_path = "config.json"
    default_config = {
        "trigger_tags": ["person", "cell phone"],
        "alert_message": "¡MUESTRA EL TELÉFONO!",
        "alert_color": [255, 20, 147],
        "font_scale": 120,
        "font_path": "C:\\Windows\\Fonts\\arialbd.ttf",
        "show_confidence": True,
        "camera_width": 1280,
        "camera_height": 720,
        "osc_ip": "127.0.0.1",
        "osc_port": 6448,
        "osc_tag": "/wek/inputs"
    }
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except Exception as e:
            print(f"Error al leer config.json: {e}")
    return default_config

def draw_text_pill(image, text, position, font_size, color, font_path, center=False):
    """ Dibuja texto de alta calidad usando Pillow sobre un frame de OpenCV """
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    draw = ImageDraw.Draw(pil_img)
    
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
        
    pos = position
    if center:
        # Centrar texto
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pos = ((image.shape[1] - w) // 2, (image.shape[0] - h) // 2)
        
    draw.text(pos, text, font=font, fill=color)
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def is_connected():
    """ Verifica si hay conexión básica a red/internet """
    try:
        # Intenta conectar a un host común para ver si hay red
        socket.create_connection(("1.1.1.1", 53), timeout=1)
        return True
    except OSError:
        return False

def main():
    print("\n=== Iniciando YOLO Atari Edition (OSC Legend & Persistence) ===")
    config = load_config()
    
    # Configuración de alerta y visual
    alert_message = str(config.get("alert_message", "¡MUESTRA EL TELÉFONO!"))
    color_raw = config.get("alert_color", [255, 20, 147])
    if not isinstance(color_raw, list) or len(color_raw) < 3: color_raw = [255, 20, 147]
    alert_color_pill = (int(color_raw[0]), int(color_raw[1]), int(color_raw[2]))
    alert_color_cv2 = (int(color_raw[2]), int(color_raw[1]), int(color_raw[0]))
    
    alert_font_size = int(config.get("font_scale", 120))
    font_path = str(config.get("font_path", "C:\\Windows\\Fonts\\arialbd.ttf"))
    if not os.path.exists(font_path): font_path = "arial.ttf"
    
    show_conf = bool(config.get("show_confidence", True))
    cam_w = int(config.get("camera_width", 1280))
    cam_h = int(config.get("camera_height", 720))

    # Configuración OSC
    osc_ip = str(config.get("osc_ip", "127.0.0.1"))
    osc_port = int(config.get("osc_port", 6448))
    osc_tag = str(config.get("osc_tag", "/wek/inputs"))
    osc_client = udp_client.SimpleUDPClient(osc_ip, osc_port)
    print(f"[*] OSC configurado en {osc_ip}:{osc_port} con tag {osc_tag}")

    detector = YOLODetector("yolov8n.pt")
    
    # IDs para person (0) y cell phone (67 en COCO)
    PERSON_ID = 0
    PHONE_ID = 67 

    print("[2/3] Inicializando cámara...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_h)

    if not cap.isOpened():
        print("[!] Error fatal: No se pudo acceder a la cámara.")
        return

    fullscreen = True
    print("[3/3] Configurando ventana Fullscreen...")
    window_name = "YOLO Atari High-Res"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    blink_state = True
    last_blink_time = time.time()
    last_frame_time = time.time()
    
    CYAN_CV2, RED_CV2 = (255, 255, 0), (0, 0, 255)
    GREEN_CV2, YELLOW_CV2 = (0, 255, 0), (0, 255, 255)
    WHITE_PILL = (255, 255, 255)
    
    # Persistencia del teléfono
    last_phone_box = None
    osc_status = "YELLOW"
    last_sent_coords = [0.0, 0.0]

    print("\n[V] ¡Sistema listo! Presiona 'q' para salir o ESC para toggle fullscreen.")
    while True:
        ret, frame = cap.read()
        if not ret: break

        detector.update_frame(frame)
        results = detector.results
        person_detected = False
        phones = []
        current_phone_seen = False

        if results is not None:
            boxes = results.boxes.data.tolist()
            for box in boxes:
                cls = int(box[5])
                if cls == PERSON_ID:
                    person_detected = True
                elif cls == PHONE_ID:
                    phones.append(box)

            if time.time() - last_blink_time > 0.4:
                blink_state = not blink_state
                last_blink_time = time.time()

            # Estilo Atari para personas
            for box in boxes:
                if int(box[5]) == PERSON_ID:
                    x1, y1, x2, y2 = map(int, box[:4])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), CYAN_CV2, 2)
                    frame = draw_text_pill(frame, "PERSON", (x1, y1-25), 20, WHITE_PILL, font_path)

            # Lógica de Teléfono
            if len(phones) > 0:
                best_phone = max(phones, key=lambda b: (b[2]-b[0])*(b[3]-b[1]))
                last_phone_box = list(best_phone[:6])
                current_phone_seen = True
                
                x1, y1, x2, y2, conf = map(float, last_phone_box[:5])
                cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), alert_color_cv2, 3)
                cv2.line(frame, (int(x1), int(y2)), (int(x2), int(y1)), alert_color_cv2, 3)
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), alert_color_cv2, 2)
                
                conf_text = f" {int(conf*100)}%" if show_conf else ""
                frame = draw_text_pill(frame, f"PHONE{conf_text}", (int(x1), int(y1)-25), 20, WHITE_PILL, font_path)
                
                last_sent_coords = [float((x1+x2)/2/frame.shape[1]), float((y1+y2)/2/frame.shape[0])]
                
                if not is_connected():
                    osc_status = "RED"
                else:
                    try:
                        osc_client.send_message(osc_tag, last_sent_coords)
                        osc_status = "GREEN"
                    except:
                        osc_status = "RED"
            else:
                osc_status = "YELLOW"
                if last_phone_box:
                    x1, y1, x2, y2 = map(int, last_phone_box[:4])
                    cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), CYAN_CV2, 2)
                    cv2.line(frame, (int(x1), int(y2)), (int(x2), int(y1)), CYAN_CV2, 2)
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), CYAN_CV2, 1)
                    frame = draw_text_pill(frame, "LAST POS", (x1, y1-25), 18, WHITE_PILL, font_path)

        if person_detected and not current_phone_seen and blink_state:
            frame = draw_text_pill(frame, alert_message, (0, 0), alert_font_size, alert_color_pill, font_path, center=True)

        # Leyenda de Controles (Arriba Derecha)
        ctrl_text = "[q]: SALIR | [ESC]: FULLSCREEN"
        frame = draw_text_pill(frame, ctrl_text, (frame.shape[1] - 320, 20), 16, WHITE_PILL, font_path)

        # Leyenda OSC (Abajo Derecha)
        st_color = GREEN_CV2 if osc_status == "GREEN" else (YELLOW_CV2 if osc_status == "YELLOW" else RED_CV2)
        ly = frame.shape[0] - 40
        lx = frame.shape[1] - 250
        cv2.circle(frame, (lx, ly + 10), 8, st_color, -1)
        osc_info = f"OSC: [{last_sent_coords[0]:.2f}, {last_sent_coords[1]:.2f}]"
        frame = draw_text_pill(frame, osc_info, (lx + 20, ly), 16, WHITE_PILL, font_path)

        now = time.time()
        fps = 1.0 / (now - last_frame_time) if now > last_frame_time else 0
        last_frame_time = now
        inf_fps = 1.0 / detector.last_inference_time if detector.last_inference_time > 0 else 0
        
        frame = draw_text_pill(frame, f"DEVICE: {detector.device_info}", (20, 20), 16, WHITE_PILL, font_path)
        frame = draw_text_pill(frame, f"CAM:{fps:.1f} | YOLO:{inf_fps:.1f}", (20, frame.shape[0]-40), 16, WHITE_PILL, font_path)

        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == 27: # ESC
            fullscreen = not fullscreen
            if fullscreen:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                cv2.resizeWindow(window_name, cam_w, cam_h)

    detector.stop()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
