"""
Script para reinstalar llama-index con versiones específicas
para evitar problemas de importación circular
"""
import os
import sys
import subprocess
import time

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
    """Función principal de reinstalación"""
    print("=== REINSTALACIÓN DE DEPENDENCIAS ===")
    
    # 1. Desinstalar versiones actuales de llama-index
    print("\n[1/5] Desinstalando versiones actuales de llama-index...")
    packages_to_uninstall = [
        "llama-index",
        "llama-index-core",
        "llama-index-embeddings-huggingface",
        "llama-index-llms-ollama",
        "llama-index-readers-file",
        "llama-index-vector-stores-chroma"
    ]
    
    for package in packages_to_uninstall:
        run_command(f"pip uninstall -y {package}")
    
    # 2. Limpiar caché de pip
    print("\n[2/5] Limpiando caché de pip...")
    run_command("pip cache purge")
    
    # 3. Instalar versión anterior estable
    print("\n[3/5] Instalando llama-index versión 0.8.34 (versión estable)...")
    success = run_command("pip install llama-index==0.8.34")
    
    if not success:
        print("ERROR: No se pudo instalar llama-index 0.8.34")
        return
    
    # 4. Instalar dependencias adicionales
    print("\n[4/5] Instalando dependencias adicionales...")
    dependencies = [
        "gradio==3.50.2",
        "rich==13.6.0",
        "requests==2.32.3",
        "beautifulsoup4==4.12.2",
        "python-dotenv==1.0.0"
    ]
    
    for dep in dependencies:
        run_command(f"pip install {dep}")
    
    # 5. Verificar la instalación
    print("\n[5/5] Verificando la instalación...")
    
    try:
        import llama_index
        print(f"✓ llama-index instalado correctamente - Versión: {llama_index.__version__}")
        
        # Verificar acceso a componentes clave
        from llama_index import VectorStoreIndex, Document, ServiceContext
        print("✓ Componentes básicos disponibles")
        
        print("\nInstalación completada correctamente.")
        
    except ImportError as e:
        print(f"ERROR: No se pudo importar llama-index: {e}")
        print("\nLa instalación no fue exitosa. Intente manualmente:")
        print("1. Desactivar el entorno virtual: deactivate")
        print("2. Eliminar el entorno virtual: rm -rf .venv")
        print("3. Crear un nuevo entorno: python -m venv .venv")
        print("4. Activarlo: .venv\\Scripts\\activate")
        print("5. Instalar dependencias: pip install llama-index==0.8.34 gradio==3.50.2 rich requests bs4")

if __name__ == "__main__":
    main()