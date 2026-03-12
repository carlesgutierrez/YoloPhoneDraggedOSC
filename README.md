# YOLOv8 Person & Phone Detector

Este proyecto es un detector de objetos en tiempo real que utiliza **YOLOv8** para identificar personas y teléfonos celulares. Si el programa detecta a una persona y un teléfono al mismo tiempo, activa una alerta visual parpadeante.

## 🚀 Cómo empezar

### Instalación Automática
He incluido un script que verifica tu hardware (GPU/CPU) y configura todo. **Si ya tenías el venv, ejecútalo de nuevo para instalar el soporte OSC:**

```powershell
python install.py
```

### Requisitos previos (Manual)
Si prefieres hacerlo a mano:
1. Crea un venv: `python -m venv venv`
2. Activa: `.\venv\Scripts\activate`
3. Instala dependencias: `pip install ultralytics opencv-python torch Pillow numpy python-osc`

### Uso
Lanza el script principal:
```powershell
.\venv\Scripts\activate; python .\detector.py
```

---

## 🛠️ Evolución del Proyecto y Créditos

Este proyecto ha sido una colaboración entre **Carles Gutiérrez** y **Gemini 3 Flash**. Hitos clave:

1.  **Detección Selectiva**: Alerta parpadeante al detectar a una persona (petición de teléfono).
2.  **Configuración JSON**: Control total de etiquetas, mensajes, colores, tipografías, resolución y parámetros OSC.
3.  **Estética Atari Retro**: Diseño CMY, pantalla completa y visuales limpios.
4.  **Optimización Multi-threading**: IA en un hilo separado para garantizar 60 FPS en la cámara.
5.  **Relación de Aspecto Real**: Fullscreen que respeta las proporciones de la webcam sin deformar la imagen.
6.  **Pillow High-Res Rendering**: Migración a **Pillow** para el renderizado de texto nítido.
7.  **Fuentes Locales (.ttf)**: Uso de tipografías del sistema (`arialbd.ttf`).
8.  **Monitor de Hardware**: Detección en tiempo real de GPU (GTX 1060) mediante CUDA.
9.  **Arranque Ultrarrápido**: Uso de `CAP_DSHOW` para evitar retrasos en Windows.
10. **Instalador Inteligente**: Script que automatiza la detección de hardware y librerías.
11. **Smart Phone Tracking**: Marcado con una cruz (X) del teléfono más grande detectado.
12. **Integración OSC (Wekinator)**: Envío de la posición (X, Y) normalizada del teléfono vía OSC (puerto 6448 por defecto).
13. **Modo Espejo (Mirror)**: Opción en `config.json` para invertir la cámara horizontalmente (activado por defecto).
14. **Persistencia y Leyenda**: Marcado de la última posición conocida y leyenda en pantalla con estados de conexión (Verde/Amarillo/Rojo).

---

## 🎮 Compatibilidad con Wekinator

Este programa actúa como un **cliente OSC de alta precisión** para [Wekinator](http://www.wekinator.org/). 
- Es equivalente al clásico ejemplo de "drag box" en Processing, pero utilizando visión artificial para capturar las coordenadas de un objeto físico (tu teléfono) en lugar del ratón.
- Envía dos valores flotantes normalizados `[0.0 - 1.0]` que representan el centro del teléfono, ideal para entrenar modelos de regresión o clasificación en tiempo real.

---
**Autor:** Carles Gutiérrez  
**IA Co-piloto:** Gemini 3 Flash  
*UTAD - Visión por Computador*
