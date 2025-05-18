"""Utilidad para verificar dependencias e importaciones de llama_index"""
import sys
import os
import importlib

def check_package(package_name):
    try:
        module = importlib.import_module(package_name)
        if hasattr(module, "__version__"):
            version = module.__version__
        else:
            version = "Desconocida"
        print(f"✅ {package_name}: INSTALADO (versión: {version})")
        return True
    except ImportError:
        print(f"❌ {package_name}: NO INSTALADO")
        return False

def check_llama_index():
    """Verifica la instalación y funcionamiento de llama_index"""
    print("\n=== VERIFICANDO LLAMA_INDEX ===")
    
    if not check_package("llama_index"):
        print("   ⚠️ llama_index no está instalado. Instálalo con:")
        print("   pip install llama-index==0.9.4")
        return False
    
    # Verificar componentes cruciales
    components = [
        "llama_index.core",
        "llama_index.indices",
        "llama_index.storage",
        "llama_index.schema"
    ]
    
    for component in components:
        check_package(component)
    
    # Verificar importaciones específicas
    print("\n=== INTENTANDO IMPORTACIONES ESPECÍFICAS ===")
    
    tests = [
        ("from llama_index import Document", "Document"),
        ("from llama_index import VectorStoreIndex", "VectorStoreIndex"),
        ("from llama_index import StorageContext", "StorageContext"),
        ("from llama_index import load_index_from_storage", "load_index_from_storage"),
        ("from llama_index.chat_engine import ContextChatEngine", "ContextChatEngine"),
        ("from llama_index.llms.base import ChatMessage, MessageRole", "ChatMessage y MessageRole")
    ]
    
    success = True
    for code, name in tests:
        try:
            exec(code)
            print(f"✅ Importación exitosa: {name}")
        except Exception as e:
            print(f"❌ Error al importar {name}: {e}")
            success = False
    
    return success

def main():
    """Función principal de verificación"""
    print("=== VERIFICANDO ENTORNO DE PYTHON ===")
    print(f"Python: {sys.version}")
    print(f"Ejecutando desde: {os.getcwd()}")
    
    print("\n=== VERIFICANDO PAQUETES PRINCIPALES ===")
    packages = [
        "llama_index",
        "gradio", 
        "rich", 
        "requests", 
        "bs4"
    ]
    
    for pkg in packages:
        check_package(pkg)
    
    llama_index_ok = check_llama_index()
    
    print("\n=== RESULTADO ===")
    if llama_index_ok:
        print("✅ Todas las verificaciones de llama_index pasaron correctamente.")
        print("   Deberías poder ejecutar la aplicación sin problemas.")
    else:
        print("⚠️ Se encontraron problemas con llama_index.")
        print("   Recomendaciones:")
        print("   1. Reinstala llama_index: pip install llama-index==0.9.4 --force-reinstall")
        print("   2. Verifica que no haya conflictos de versiones")
        print("   3. Intenta crear un nuevo entorno virtual")

if __name__ == "__main__":
    main()