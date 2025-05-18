"""
memoria.py - Sistema de gestión de memoria simplificado para Jarvis
"""
from functools import lru_cache
import os
import json
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import re

# Importaciones de llama_index simplificadas
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jarvis_memoria.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memoria")

# Configurar modelo de embeddings por defecto
def configurar_embedding_model():
    """Configura un modelo de embeddings local por defecto"""
    try:
        # Intentar usar un modelo local de HuggingFace
        embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
        # Establecer como modelo por defecto
        Settings.embed_model = embed_model
        return True
    except Exception as e:
        logger.error(f"Error al configurar el modelo de embeddings: {e}")
        try:
            # Intentar con un modelo alternativo
            from llama_index.embeddings.huggingface import HuggingFaceBgeEmbedding
            embed_model = HuggingFaceBgeEmbedding(model_name="BAAI/bge-small-en")
            Settings.embed_model = embed_model
            return True
        except Exception as e:
            logger.error(f"Error al configurar modelo alternativo: {e}")
            return False

class MemoryManager:
    """Gestor de memoria simplificado"""
    def __init__(self, memory_dir: str = "memory", index_dir: str = "embeddings"):
        self.memory_dir = memory_dir
        self.index_dir = index_dir
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Configurar modelo de embeddings
        configurar_embedding_model()
        
        # Intentar cargar índice o crear uno nuevo
        self.index = None
        try:
            self.index = self._load_or_create_index()
        except Exception as e:
            logger.error(f"Error al inicializar índice: {e}")
            self.index = VectorStoreIndex([])
        
        self._print_memory_stats()

    def _print_memory_stats(self):
        """Imprime estadísticas de la memoria"""
        memory_files = self._cargar_archivos_recuerdos()
        logger.info(f"Estadísticas de memoria:")
        logger.info(f"   - Archivos de recuerdos: {len(memory_files)}")
        if memory_files:
            logger.info(f"   - Último recuerdo: {memory_files[0]}")

    def guardar_recuerdo(self, contenido: str) -> bool:
        """Guarda un recuerdo en la memoria"""
        try:
            # Generar nombre único para el archivo
            nombre = datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
            path = os.path.join(self.memory_dir, nombre)
            
            # Guardar texto completo
            with open(path, "w", encoding="utf-8") as f:
                f.write(contenido)
                
            # Limpiar texto de thinking para indexación
            texto_limpio = contenido
            if "<think>" in texto_limpio and "</think>" in texto_limpio:
                parts = texto_limpio.split("</think>")
                texto_limpio = parts[-1].strip()
                
            # Insertar en índice si está disponible
            if self.index is not None:
                try:
                    doc = Document(text=texto_limpio, metadata={"source": path, "filename": nombre})
                    self.index.insert(doc)
                    # Guardar cambios
                    self.index.storage_context.persist(persist_dir=self.index_dir)
                except Exception as e:
                    logger.error(f"Error al indexar recuerdo: {e}")
            
            logger.info(f"Recuerdo guardado en {nombre}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar recuerdo: {e}")
            return False

    def _cargar_archivos_recuerdos(self) -> List[str]:
        """Carga la lista de archivos de recuerdos ordenados por fecha"""
        try:
            archivos = [
                f for f in os.listdir(self.memory_dir)
                if f.endswith(".txt") and not f.startswith("config") and not f.startswith("preferencia_")
            ]
            archivos.sort(key=lambda x: os.path.getmtime(os.path.join(self.memory_dir, x)), reverse=True)
            return archivos
        except Exception as e:
            logger.error(f"Error al cargar archivos de recuerdos: {e}")
            return []

    def leer_recuerdo(self, nombre: str) -> str:
        """Lee el contenido de un recuerdo específico"""
        try:
            ruta = os.path.join(self.memory_dir, nombre)
            with open(ruta, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error al leer el recuerdo {nombre}: {e}")
            return f"Error al leer el recuerdo: {e}"
        
    def _load_or_create_index(self):
        """Carga el índice existente o crea uno nuevo si no existe"""
        try:
            if not os.path.exists(self.index_dir) or not os.listdir(self.index_dir):
                return self._create_new_index()
            logger.info("Cargando recuerdos guardados...")
            try:
                from llama_index.core import load_index_from_storage
                return load_index_from_storage(StorageContext.from_defaults(persist_dir=self.index_dir))
            except Exception as e:
                logger.error(f"Error al cargar el índice: {e}")
                logger.info("Recreando índice desde los documentos originales...")
                return self._create_new_index(rebuild=True)
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return self._create_new_index(rebuild=True)

    def _create_new_index(self, rebuild: bool = False):
        """Crea un nuevo índice vectorial para búsqueda semántica"""
        if rebuild and os.path.exists(self.index_dir):
            logger.info("Eliminando índice corrupto...")
            shutil.rmtree(self.index_dir)
            os.makedirs(self.index_dir, exist_ok=True)

        logger.info("Iniciando memoria nueva...")
        documents = self._load_documents()
        logger.info(f"Cargando {len(documents)} documentos de memoria...")
        
        if documents:
            try:
                # Usar el modelo de embedding configurado explícitamente
                index = VectorStoreIndex.from_documents(
                    documents,
                    embed_model=Settings.embed_model
                )
                index.storage_context.persist(persist_dir=self.index_dir)
                return index
            except Exception as e:
                logger.error(f"Error al crear índice: {str(e)}")
                # Crear un índice vacío como fallback
                logger.warning("Creando índice vacío como alternativa")
                return VectorStoreIndex([])
        else:
            logger.warning("No se encontraron documentos de memoria")
            return VectorStoreIndex([])

    def _load_documents(self) -> List[Document]:
        """Carga todos los documentos de la memoria para indexación"""
        documentos = []
        for filename in os.listdir(self.memory_dir):
            if filename.endswith('.txt') and not filename.startswith("config"):
                filepath = os.path.join(self.memory_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        text = f.read()
                        # Eliminar partes de "thinking" que puedan confundir
                        if "<think>" in text and "</think>" in text:
                            parts = text.split("</think>")
                            text = parts[-1].strip()
                        doc = Document(text=text, metadata={"source": filepath, "filename": filename})
                        documentos.append(doc)
                except Exception as e:
                    logger.error(f"Error al leer {filepath}: {e}")
        return documentos

    def obtener_contexto_relevante(self, pregunta: str, top_k: int = 3) -> str:
        """Obtiene contexto relevante de la memoria para una pregunta"""
        if self.index is None:
            logger.warning("Índice no disponible para búsqueda de contexto")
            return ""
            
        try:
            # Usar retriever con mejor configuración
            retriever = self.index.as_retriever(similarity_top_k=top_k)
            resultados = retriever.retrieve(pregunta)
            
            if not resultados:
                return ""
                
            # Formatear recuerdos con mejor estructura
            contexto = []
            for nodo in resultados:
                # Extraer nombre de archivo y fecha
                filename = nodo.metadata.get("filename", "desconocido")
                date_part = filename.split("_")[0] if "_" in filename else ""
                
                # Intentar formatear fecha
                fecha = date_part
                if len(date_part) == 8:  # formato YYYYMMDD
                    try:
                        fecha = f"{date_part[6:8]}/{date_part[4:6]}/{date_part[0:4]}"
                    except:
                        pass
                        
                # Limpiar y formatear texto
                texto = nodo.text.strip()
                contexto.append(f"[Recuerdo del {fecha}]\n{texto}\n")
                
            return "\n".join(contexto)
        except Exception as e:
            logger.error(f"Error al recuperar recuerdos: {e}")
            return ""

    def cargar_configuracion(self) -> Dict[str, Any]:
        """Carga la configuración del sistema"""
        try:
            path = os.path.join(self.memory_dir, "configuracion.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}  # Configuración por defecto
        except Exception as e:
            logger.error(f"Error al cargar configuración: {e}")
            return {}
            
    def guardar_configuracion(self, configuracion: Dict[str, Any]) -> bool:
        """Guarda la configuración completa del sistema"""
        try:
            path = os.path.join(self.memory_dir, "configuracion.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(configuracion, f, indent=2)
            logger.info("Configuración guardada")
            return True
        except Exception as e:
            logger.error(f"Error al guardar configuración: {e}")
            return False

    def obtener_ultima_interaccion(self) -> str:
        """Obtiene la fecha de la última interacción guardada en la memoria"""
        try:
            # Obtener archivos de recuerdos ordenados por fecha (más recientes primero)
            archivos = self._cargar_archivos_recuerdos()
            
            # Si no hay recuerdos, retornar mensaje apropiado
            if not archivos:
                return "Sin interacciones previas"
            
            # Obtener la fecha del archivo más reciente
            archivo_reciente = archivos[0]
            
            # Extraer timestamp del nombre del archivo o del contenido
            if "_" in archivo_reciente:
                # Si el formato es "YYYYMMDD_HHMMSS.txt"
                partes = archivo_reciente.split("_")
                if len(partes) >= 2:
                    fecha_str = partes[0]
                    hora_str = partes[1].split(".")[0]  # Quitar extensión
                    
                    # Formatear bonito
                    try:
                        fecha = f"{fecha_str[:4]}-{fecha_str[4:6]}-{fecha_str[6:]}"
                        hora = f"{hora_str[:2]}:{hora_str[2:4]}:{hora_str[4:]}" if len(hora_str) >= 6 else hora_str
                        return f"{fecha} {hora}"
                    except:
                        return archivo_reciente
            
            # Alternativa: leer la fecha de modificación del archivo
            ruta_completa = os.path.join(self.memory_dir, archivo_reciente)
            timestamp = os.path.getmtime(ruta_completa)
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            
        except Exception as e:
            logger.error(f"Error al obtener última interacción: {e}")
            return "Error al determinar fecha"