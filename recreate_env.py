"""
Script para recrear el entorno virtual desde cero
"""
import os
import sys
import subprocess
import platform

def run_command(command):
    """Ejecuta un comando y muestra el resultado"""
    print(f"Ejecutando: {command}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = process.communicate()
    
    if stdout:
        print(stdout)
    
    if stderr:
        print(f"ERROR: {stderr}")
    
    return process.returncode == 0

def main():
    """Función principal"""
    print("=== RECREANDO ENTORNO VIRTUAL ===")
    
    # Detectar sistema operativo
    is_windows = platform.system() == "Windows"
    
    # Paso 1: Desactivar entorno actual (informativo)
    print("\n[PASO 1] Desactivar el entorno virtual actual")
    print("NOTA: No podemos desactivar el entorno desde el script.")
    print("Si estás en un entorno virtual, cierra esta terminal y abre una nueva,")
    print("o ejecuta 'deactivate' manualmente antes de continuar.")
    
    input("Presiona Enter cuando estés listo para continuar...")
    


    
    
    # Paso 2: Eliminar entorno virtual existente
    print("\n[PASO 2] Eliminando entorno virtual existente...")
    if is_windows:
        if os.path.exists(".venv"):
            run_command("rmdir /s /q .venv")
    else:
        if os.path.exists(".venv"):
            run_command("rm -rf .venv")
    
    # Paso 3: Crear nuevo entorno virtual
    print("\n[PASO 3] Creando nuevo entorno virtual...")
    run_command("python -m venv .venv")
    
    # Paso 4: Activar el entorno e instalar dependencias
    print("\n[PASO 4] Instalando dependencias...")
    activate_cmd = ".venv\\Scripts\\activate" if is_windows else "source .venv/bin/activate"
    
    # En Windows, la activación y ejecución de comandos adicionales es complicada...
    # Es más fácil crear un script batch para Windows
    if is_windows:
        with open("install_deps.bat", "w") as f:
            f.write(f"@echo off\n")
            f.write(f"call {activate_cmd}\n")
            # ACTUALIZADO: Usar una versión de langchain compatible con llama-index 0.8.34
            f.write(f"pip install langchain>=0.0.293\n")
            f.write(f"pip install llama-index==0.8.34\n")
            f.write(f"pip install gradio==3.50.2 rich==13.6.0 requests==2.32.3 beautifulsoup4==4.12.2\n")
            f.write(f"pip install python-dotenv\n")
            f.write(f"echo Verificando instalacion...\n")
            f.write(f"python -c \"import llama_index; import langchain; print('llama-index: ' + llama_index.__version__ + ', langchain: ' + langchain.__version__)\"\n")
            f.write(f"echo Instalación completa!\n")
            f.write(f"pause\n")
        
        print("\n[INSTRUCCIONES]")
        print("1. Se ha creado un archivo 'install_deps.bat'")
        print("2. Ejecuta este archivo haciendo doble clic o desde la línea de comandos")
        print("3. Esto activará el entorno e instalará las dependencias")
    else:
        # En sistemas Unix, podemos poner todo en un shell script
        with open("install_deps.sh", "w") as f:
            f.write(f"#!/bin/bash\n")
            f.write(f"{activate_cmd}\n")
            # ACTUALIZADO: Usar una versión de langchain compatible con llama-index 0.8.34
            f.write(f"pip install langchain>=0.0.293\n")
            f.write(f"pip install llama-index==0.8.34\n")
            f.write(f"pip install gradio==3.50.2 rich==13.6.0 requests==2.32.3 beautifulsoup4==4.12.2\n")
            f.write(f"pip install python-dotenv\n")
            f.write(f"echo Verificando instalacion...\n")
            f.write(f"python -c \"import llama_index; import langchain; print('llama-index: ' + llama_index.__version__ + ', langchain: ' + langchain.__version__)\"\n")
        
        run_command("chmod +x install_deps.sh")
        
        print("\n[INSTRUCCIONES]")
        print("1. Se ha creado un archivo 'install_deps.sh'")
        print("2. Ejecuta este archivo con './install_deps.sh'")
    
    print("\n=== PROCESO COMPLETADO ===")
    print("Una vez instaladas las dependencias, podrás ejecutar tu aplicación normalmente.")

if __name__ == "__main__":
    main()

