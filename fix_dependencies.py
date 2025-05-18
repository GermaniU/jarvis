"""
Script para corregir problemas de dependencias entre llama-index y langchain
"""
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
    """Función principal"""
    print("=== CORRIGIENDO DEPENDENCIAS CONFLICTIVAS ===")
    
    print("\n[1/5] Desinstalando paquetes que causan conflictos...")
    packages_to_uninstall = [
        "llama-index",
        "llama-index-core", 
        "llama-index-embeddings-huggingface",
        "llama-index-llms-ollama",
        "langchain",
        "langchain-core",
        "langchain-community"
    ]
    
    for package in packages_to_uninstall:
        run_command(f"pip uninstall -y {package}")
    
    print("\n[2/5] Limpiando caché de pip...")
    run_command("pip cache purge")
    
    print("\n[3/5] Instalando versiones específicas compatibles...")
    # Estas versiones son compatibles entre sí
    run_command("pip install langchain==0.0.267")
    run_command("pip install langchain-core==0.0.10")
    run_command("pip install llama-index==0.8.34")
    
    print("\n[4/5] Instalando dependencias adicionales...")
    dependencies = [
        "gradio==3.50.2",
        "rich==13.6.0", 
        "requests==2.32.3",
        "beautifulsoup4==4.12.2"
    ]
    
    for dep in dependencies:
        run_command(f"pip install {dep}")
    
    print("\n[5/5] Verificando instalación...")
    verification_code = """
import langchain
import llama_index
from langchain_core.caches import BaseCache

print(f"LangChain versión: {langchain.__version__}")
print(f"llama-index versión: {llama_index.__version__}")
print("Importación de BaseCache exitosa")
print("✅ Todo parece funcionar correctamente")
    """
    
    temp_file = "verification_script.py"
    with open(temp_file, "w") as f:
        f.write(verification_code)
    
    result = run_command(f"python {temp_file}")
    
    if not result:
        print("\n[ATENCIÓN] La verificación falló. Intentando método alternativo...")
        
        # Intentar solución alternativa
        run_command("pip install langchain==0.0.207 langchain-core==0.0.1")
        run_command("python -c \"import langchain; print('LangChain versión:', langchain.__version__)\"")
    
    print("\n=== INSTALACIÓN FINALIZADA ===")
    print("Si sigues teniendo problemas, considera modificar tu código para usar")
    print("llm_wrapper.py en lugar de llama_index directamente.")

if __name__ == "__main__":
    main()
