"""
indexador.py - Módulo para construir y gestionar índices vectoriales
"""
import os
import json
import glob
import logging
from typing import List, Dict, Any, Optional

# Importar directamente (no desde llm_imports)
try:
    # from llama_index.core import (
    #     Document, 
    #     VectorStoreIndex, 
    #     SimpleDirectoryReader,
    #     Settings
    # )
    # from llama_index.core.node_parser import SentenceSplitter
    llama_index_available = True
except ImportError:
    llama_index_available = False

from .config import MEMORY_DIR, EMBEDDINGS_DIR, DATA_DIR, get_logger

# Obtener logger
logger = get_logger("indexador")

def construir_indice(directorios=None, incluir_recuerdos=True):
    """Construye un índice vectorial para búsqueda semántica"""
    if not llama_index_available:
        logger.error("LlamaIndex no está disponible")
        return None
        
    if directorios is None:
        directorios = [DATA_DIR]
        
    try:
        documentos = []
        
        # Cargar documentos de los directorios
        for directorio in directorios:
            if os.path.exists(directorio):
                logger.info(f"Cargando documentos desde: {directorio}")
                reader = SimpleDirectoryReader(directorio)
                docs = reader.load_data()
                documentos.extend(docs)
                logger.info(f"Cargados {len(docs)} documentos desde {directorio}")
        
        # Cargar recuerdos si está habilitado
        if incluir_recuerdos and os.path.exists(MEMORY_DIR):
            logger.info("Cargando recuerdos...")
            recuerdos = cargar_recuerdos()
            documentos.extend(recuerdos)
            logger.info(f"Cargados {len(recuerdos)} recuerdos")
        
        # Construir índice
        logger.info(f"Construyendo índice con {len(documentos)} documentos...")
        
        # Verificar si hay documentos
        if not documentos:
            logger.warning("No hay documentos para indexar")
            indice = VectorStoreIndex([])
        else:
            indice = VectorStoreIndex.from_documents(documentos)
            
        # Guardar índice
        indice.storage_context.persist(persist_dir=EMBEDDINGS_DIR)
        logger.info(f"Índice guardado en: {EMBEDDINGS_DIR}")
        
        return indice
        
    except Exception as e:
        logger.error(f"Error al construir índice: {e}")
        return None

def cargar_recuerdos():
    """Carga recuerdos como documentos"""
    recuerdos = []
    
    if not os.path.exists(MEMORY_DIR):
        return recuerdos
        
    try:
        # Cargar archivos de texto como recuerdos
        for archivo in os.listdir(MEMORY_DIR):
            if archivo.endswith(".txt") and not archivo.startswith("config"):
                ruta = os.path.join(MEMORY_DIR, archivo)
                
                try:
                    with open(ruta, "r", encoding="utf-8") as f:
                        contenido = f.read()
                        
                    # Limpiar thinking si existe
                    if "<think>" in contenido and "</think>" in contenido:
                        contenido = contenido.split("</think>")[-1].strip()
                        
                    # Crear documento
                    doc = Document(
                        text=contenido,
                        metadata={"source": ruta, "filename": archivo}
                    )
                    recuerdos.append(doc)
                except Exception as e:
                    logger.error(f"Error al procesar recuerdo {archivo}: {e}")
    except Exception as e:
        logger.error(f"Error al cargar recuerdos: {e}")
        
    return recuerdos