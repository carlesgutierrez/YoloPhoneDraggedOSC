import os
import subprocess
import sys
import platform

def run_command(command):
    print(f"\n[EXEC] {command}")
    try:
        # Usamos shell=True solo en Windows para mayor compatibilidad con cmd/powershell
        is_windows = platform.system() == "Windows"
        subprocess.check_call(command, shell=is_windows)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Error al ejecutar: {e}")
        return False

def main():
    print("="*60)
    print("   INSTALADOR DE YOLO DETECTOR (ATARI EDITION + OSC)")
    print("="*60)
    print("Este script configurará el entorno virtual e instalará las librerías.")
    
    confirm = input("\n¿Deseas continuar con la instalación? (s/n): ").lower()
    if confirm != 's':
        print("Instalación cancelada.")
        return

    is_windows = platform.system() == "Windows"
    pip_path = ".\\venv\\Scripts\\pip" if is_windows else "./venv/bin/pip"
    python_venv = ".\\venv\\Scripts\\python" if is_windows else "./venv/bin/python"

    # 1. Crear entorno virtual
    if not os.path.exists("venv"):
        print("\n[*] Creando entorno virtual...")
        if not run_command(f"{sys.executable} -m venv venv"):
            return
    else:
        print("\n[OK] El entorno virtual ya existe.")

    # 2. Actualizar pip
    print("\n[*] Actualizando pip...")
    run_command(f"{pip_path} install --upgrade pip")

    # 3. Verificar GPU NVIDIA
    print("\n[*] Verificando hardware NVIDIA...")
    has_nvidia = False
    try:
        subprocess.check_output("nvidia-smi", shell=True)
        has_nvidia = True
        print("[OK] GPU NVIDIA detectada.")
    except:
        print("[!] No se detectó GPU NVIDIA (o no están los drivers).")

    # 4. Configurar comando de PyTorch
    if has_nvidia:
        resp = input("\n¿Instalar versión con soporte CUDA (GPU)? (s/n): ").lower()
        if resp == 's':
            # Instalamos Torch por separado usando su índice específico
            print("\n[*] Instalando PyTorch con soporte CUDA...")
            torch_cmd = f"{pip_path} install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121"
        else:
            torch_cmd = f"{pip_path} install torch torchvision torchaudio"
    else:
        torch_cmd = f"{pip_path} install torch torchvision torchaudio"

    if not run_command(torch_cmd):
        print("\n[!] Falló la instalación de PyTorch. Intenta de nuevo.")
        return

    # 5. Instalar el resto de dependencias (desde PyPI normal)
    print("\n[*] Instalando dependencias adicionales (YOLO, OpenCV, OSC, Pillow)...")
    deps_cmd = f"{pip_path} install ultralytics opencv-python Pillow numpy python-osc"
    
    if run_command(deps_cmd):
        print("\n" + "="*60)
        print("   ¡INSTALACIÓN COMPLETADA CON ÉXITO!")
        print("="*60)
        print("\nPara lanzar el programa:")
        if is_windows:
            print("  .\\venv\\Scripts\\activate; python .\\detector.py")
        else:
            print("  source venv/bin/activate; python detector.py")
        print("\n¡Disfruta de tu YOLO Atari Edition!")
    else:
        print("\n[!] Error al instalar las dependencias finales.")

if __name__ == "__main__":
    main()
