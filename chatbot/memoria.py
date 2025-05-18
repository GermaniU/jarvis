"""
memoria.py - Sistema de gestión de memoria simplificado para Jarvis
"""
import os
import json
import shutil
import logging
from datetime import datetime
from typing import Dict, List, Any
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings

from chatbot.config import DEFAULT_EMBEDDING_MODEL

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

def configurar_embedding_model():
    """Configura el modelo de embeddings desde config.py"""
    try:
        if DEFAULT_EMBEDDING_MODEL == "local":
            from llama_index.embeddings.ollama import OllamaEmbedding
            embed_model = OllamaEmbedding(model_name="nomic-embed-text")  # Cambia por deepseek-embed si prefieres
            Settings.embed_model = embed_model
            logger.info("Embeddings de Ollama configurados correctamente")
            return True
        else:
            raise ValueError(f"Modelo de embeddings desconocido: {DEFAULT_EMBEDDING_MODEL}")
    except Exception as e:
        logger.error(f"Error al configurar embeddings: {e}")
        return False

class MemoryManager:
    """Gestor de memoria simplificado"""
    def __init__(self, memory_dir: str = "memory", index_dir: str = "embeddings"):
        self.memory_dir = memory_dir
        self.index_dir = index_dir
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.index_dir, exist_ok=True)

        # Crear o cargar índice desde disco
        self.index = self._load_or_create_index()
        if self.index:
            logger.info("Índice de memoria inicializado correctamente")
        else:
            logger.warning("No se pudo inicializar el índice de memoria. Se trabajará sin embeddings.")

        self._print_memory_stats()

    def _print_memory_stats(self):
        memory_files = self._cargar_archivos_recuerdos()
        logger.info("Estadísticas de memoria:")
        logger.info(f"   - Archivos de recuerdos: {len(memory_files)}")
        if memory_files:
            logger.info(f"   - Último recuerdo: {memory_files[0]}")

    def guardar_recuerdo(self, contenido: str) -> bool:
        try:
            nombre = datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt"
            path = os.path.join(self.memory_dir, nombre)

            with open(path, "w", encoding="utf-8") as f:
                f.write(contenido)

            texto_limpio = contenido
            if "<think>" in texto_limpio and "</think>" in texto_limpio:
                parts = texto_limpio.split("</think>")
                texto_limpio = parts[-1].strip()

            if self.index:
                try:
                    doc = Document(text=texto_limpio, metadata={"source": path, "filename": nombre})
                    self.index.insert(doc)
                    self.index.storage_context.persist(persist_dir=self.index_dir)
                except Exception as e:
                    logger.error(f"Error al indexar recuerdo: {e}")

            logger.info(f"Recuerdo guardado en {nombre}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar recuerdo: {e}")
            return False

    def _cargar_archivos_recuerdos(self) -> List[str]:
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
        try:
            ruta = os.path.join(self.memory_dir, nombre)
            with open(ruta, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error al leer el recuerdo {nombre}: {e}")
            return f"Error al leer el recuerdo: {e}"

    def _load_or_create_index(self):
        try:
            if not os.path.exists(self.index_dir) or not os.listdir(self.index_dir):
                return self._create_new_index()
            logger.info("Cargando índice desde almacenamiento persistente...")
            from llama_index.core import load_index_from_storage
            return load_index_from_storage(StorageContext.from_defaults(persist_dir=self.index_dir))
        except Exception as e:
            logger.error(f"Error al cargar índice existente: {e}")
            logger.info("Creando nuevo índice desde documentos de memoria...")
            return self._create_new_index(rebuild=True)

    def _create_new_index(self, rebuild: bool = False):
        if rebuild and os.path.exists(self.index_dir):
            logger.info("Eliminando índice anterior...")
            shutil.rmtree(self.index_dir)
            os.makedirs(self.index_dir, exist_ok=True)

        documentos = self._load_documents()
        logger.info(f"Cargando {len(documentos)} documentos de memoria...")

        try:
            index = VectorStoreIndex.from_documents(
                documentos,
                embed_model=Settings.embed_model
            )
            index.storage_context.persist(persist_dir=self.index_dir)
            return index
        except Exception as e:
            logger.error(f"Error al crear índice: {e}")
            logger.warning("Creando índice vacío como alternativa")
            return VectorStoreIndex([])

    def _load_documents(self) -> List[Document]:
        documentos = []
        for filename in os.listdir(self.memory_dir):
            if filename.endswith('.txt') and not filename.startswith("config"):
                filepath = os.path.join(self.memory_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        text = f.read()
                        if "<think>" in text and "</think>" in text:
                            parts = text.split("</think>")
                            text = parts[-1].strip()
                        doc = Document(text=text, metadata={"source": filepath, "filename": filename})
                        documentos.append(doc)
                except Exception as e:
                    logger.error(f"Error al leer {filepath}: {e}")
        return documentos

    def obtener_contexto_relevante(self, pregunta: str, top_k: int = 3) -> str:
        if not self.index:
            logger.warning("Índice no disponible para búsqueda de contexto")
            return ""

        try:
            retriever = self.index.as_retriever(similarity_top_k=top_k)
            resultados = retriever.retrieve(pregunta)

            if not resultados:
                return ""

            contexto = []
            for nodo in resultados:
                filename = nodo.metadata.get("filename", "desconocido")
                date_part = filename.split("_")[0] if "_" in filename else ""
                fecha = date_part
                if len(date_part) == 8:
                    try:
                        fecha = f"{date_part[6:8]}/{date_part[4:6]}/{date_part[0:4]}"
                    except:
                        pass
                texto = nodo.text.strip()
                contexto.append(f"[Recuerdo del {fecha}]\n{texto}\n")

            return "\n".join(contexto)
        except Exception as e:
            logger.error(f"Error al recuperar recuerdos: {e}")
            return ""

    def cargar_configuracion(self) -> Dict[str, Any]:
        try:
            path = os.path.join(self.memory_dir, "configuracion.json")
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error al cargar configuración: {e}")
            return {}

    def guardar_configuracion(self, configuracion: Dict[str, Any]) -> bool:
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
        try:
            archivos = self._cargar_archivos_recuerdos()
            if not archivos:
                return "Sin interacciones previas"

            archivo_reciente = archivos[0]
            if "_" in archivo_reciente:
                partes = archivo_reciente.split("_")
                if len(partes) >= 2:
                    fecha_str = partes[0]
                    hora_str = partes[1].split(".")[0]
                    try:
                        fecha = f"{fecha_str[:4]}-{fecha_str[4:6]}-{fecha_str[6:]}"
                        hora = f"{hora_str[:2]}:{hora_str[2:4]}:{hora_str[4:]}" if len(hora_str) >= 6 else hora_str
                        return f"{fecha} {hora}"
                    except:
                        return archivo_reciente

            ruta_completa = os.path.join(self.memory_dir, archivo_reciente)
            timestamp = os.path.getmtime(ruta_completa)
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Error al obtener última interacción: {e}")
            return "Error al determinar fecha"
