"""
memoria_hibrida.py - Sistema de memoria híbrida para Jarvis

Combina enfoques de memoria a corto plazo (reciente) y largo plazo (indexada)
con múltiples estrategias de ponderación y mayor robustez.

Características principales:
- Memoria híbrida: Combina resultados de memoria reciente y memoria vectorial
- Ponderación múltiple: Usa semántica, palabras clave, recencia y relevancia
- Refuerzo de temas importantes: Marca información crítica para priorización
- Mayor robustez: Implementa sistemas de respaldo cuando falla la búsqueda semántica
"""
import os
import json
import shutil
import logging
import datetime
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta

# Para procesamiento de texto y palabras clave
from collections import Counter
import string
import math

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jarvis_memoria_hibrida.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memoria_hibrida")

try:
    # Intentar importar componentes para embeddings
    from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings
    from llama_index.core.retrievers import VectorIndexRetriever
    from llama_index.core.node_parser import SentenceSplitter
    from chatbot.config import DEFAULT_EMBEDDING_MODEL
    
    llama_index_disponible = True
except ImportError as e:
    logger.warning(f"No se pudo importar LlamaIndex: {e}")
    llama_index_disponible = False

# Constantes para configuración
PESO_MEMORIA_RECIENTE = 0.4
PESO_MEMORIA_SEMANTICA = 0.6
MAX_RECUERDOS_RECIENTES = 10
PRIORIDAD_TEMA_IMPORTANTE = 1.5  # Multiplicador de relevancia para temas importantes
UMBRAL_RELEVANCIA = 0.2  # Umbral mínimo de relevancia

def configurar_embedding_model():
    """Configura el modelo de embeddings desde config.py"""
    if not llama_index_disponible:
        logger.warning("LlamaIndex no está disponible. No se pueden configurar embeddings.")
        return False
        
    try:
        if DEFAULT_EMBEDDING_MODEL == "local":
            from llama_index.embeddings.ollama import OllamaEmbedding
            embed_model = OllamaEmbedding(model_name="nomic-embed-text")
            Settings.embed_model = embed_model
            logger.info("Embeddings de Ollama configurados correctamente")
            return True
        else:
            raise ValueError(f"Modelo de embeddings desconocido: {DEFAULT_EMBEDDING_MODEL}")
    except Exception as e:
        logger.error(f"Error al configurar embeddings: {e}")
        return False

def extraer_palabras_clave(texto: str, max_keywords: int = 10) -> List[str]:
    """
    Extrae palabras clave de un texto mediante TF-IDF simplificado
    
    Args:
        texto: Texto del que extraer palabras clave
        max_keywords: Número máximo de palabras clave a devolver
        
    Returns:
        List[str]: Lista de palabras clave ordenadas por relevancia
    """
    # Eliminar puntuación y convertir a minúsculas
    texto = texto.lower()
    for p in string.punctuation:
        texto = texto.replace(p, ' ')
    
    # Lista de palabras vacías en español
    stop_words = {
        'a', 'al', 'algo', 'algunas', 'algunos', 'ante', 'antes', 'como', 'con', 'contra',
        'cual', 'cuando', 'de', 'del', 'desde', 'donde', 'durante', 'e', 'el', 'ella',
        'ellas', 'ellos', 'en', 'entre', 'era', 'erais', 'eran', 'eras', 'eres', 'es',
        'esa', 'esas', 'ese', 'eso', 'esos', 'esta', 'estaba', 'estabais', 'estaban',
        'estabas', 'estad', 'estada', 'estadas', 'estado', 'estados', 'estamos', 'estando',
        'estar', 'estaremos', 'estará', 'estarán', 'estarás', 'estaré', 'estaréis',
        'estaría', 'estaríais', 'estaríamos', 'estarían', 'estarías', 'estas', 'este',
        'estemos', 'esto', 'estos', 'estoy', 'estuve', 'estuviera', 'estuvierais',
        'estuvieran', 'estuvieras', 'estuvieron', 'estuviese', 'estuvieseis', 'estuviesen',
        'estuvieses', 'estuvimos', 'estuviste', 'estuvisteis', 'estuviéramos',
        'estuviésemos', 'estuvo', 'fue', 'fuera', 'fuerais', 'fueran', 'fueras', 'fueron',
        'fuese', 'fueseis', 'fuesen', 'fueses', 'fui', 'fuimos', 'fuiste', 'fuisteis',
        'fuéramos', 'fuésemos', 'ha', 'habéis', 'haber', 'habida', 'habidas', 'habido',
        'habidos', 'habiendo', 'habremos', 'habrá', 'habrán', 'habrás', 'habré', 'habréis',
        'habría', 'habríais', 'habríamos', 'habrían', 'habrías', 'habéis', 'había',
        'habíais', 'habíamos', 'habían', 'habías', 'han', 'has', 'hasta', 'hay', 'haya',
        'hayamos', 'hayan', 'hayas', 'hayáis', 'he', 'hemos', 'hube', 'hubiera',
        'hubierais', 'hubieran', 'hubieras', 'hubieron', 'hubiese', 'hubieseis',
        'hubiesen', 'hubieses', 'hubimos', 'hubiste', 'hubisteis', 'hubiéramos',
        'hubiésemos', 'hubo', 'la', 'las', 'le', 'les', 'lo', 'los', 'me', 'mi', 'mis',
        'mucho', 'muchos', 'muy', 'más', 'mí', 'mía', 'mías', 'mío', 'míos', 'nada',
        'ni', 'no', 'nos', 'nosotras', 'nosotros', 'nuestra', 'nuestras', 'nuestro',
        'nuestros', 'o', 'os', 'otra', 'otras', 'otro', 'otros', 'para', 'pero', 'poco',
        'por', 'porque', 'que', 'quien', 'quienes', 'qué', 'se', 'sea', 'seamos',
        'sean', 'seas', 'seremos', 'será', 'serán', 'serás', 'seré', 'seréis', 'sería',
        'seríais', 'seríamos', 'serían', 'serías', 'seáis', 'si', 'sido', 'siendo',
        'sin', 'sobre', 'sois', 'somos', 'son', 'soy', 'su', 'sus', 'suya', 'suyas',
        'suyo', 'suyos', 'sí', 'también', 'tanto', 'te', 'tendremos', 'tendrá', 'tendrán',
        'tendrás', 'tendré', 'tendréis', 'tendría', 'tendríais', 'tendríamos', 'tendrían',
        'tendrías', 'tened', 'tenemos', 'tenga', 'tengamos', 'tengan', 'tengas', 'tengo',
        'tengáis', 'tenida', 'tenidas', 'tenido', 'tenidos', 'teniendo', 'tenéis', 'tenía',
        'teníais', 'teníamos', 'tenían', 'tenías', 'ti', 'tiene', 'tienen', 'tienes',
        'todo', 'todos', 'tu', 'tus', 'tuve', 'tuviera', 'tuvierais', 'tuvieran',
        'tuvieras', 'tuvieron', 'tuviese', 'tuvieseis', 'tuviesen', 'tuvieses', 'tuvimos',
        'tuviste', 'tuvisteis', 'tuviéramos', 'tuviésemos', 'tuvo', 'tuya', 'tuyas',
        'tuyo', 'tuyos', 'tú', 'un', 'una', 'uno', 'unos', 'vosotras', 'vosotros',
        'vuestra', 'vuestras', 'vuestro', 'vuestros', 'y', 'ya', 'yo', 'él', 'éramos'
    }
    
    # Tokenizar y contar frecuencias
    palabras = [palabra for palabra in texto.split() if len(palabra) > 2 and palabra not in stop_words]
    
    if not palabras:
        return []
    
    # Contar frecuencia de palabras
    contador = Counter(palabras)
    total_palabras = len(palabras)
    
    # Calcular TF (Term Frequency) para cada palabra
    tf = {palabra: frecuencia / total_palabras for palabra, frecuencia in contador.items()}
    
    # Ordenar por frecuencia (TF simplificado)
    palabras_clave = sorted(tf.items(), key=lambda x: x[1], reverse=True)
    
    # Devolver solo las palabras, limitadas por max_keywords
    return [palabra for palabra, _ in palabras_clave[:max_keywords]]

def calcular_relevancia_por_keywords(texto_recuerdo: str, consulta: str) -> float:
    """
    Calcula relevancia basada en palabras clave compartidas
    
    Args:
        texto_recuerdo: Texto del recuerdo
        consulta: Consulta del usuario
        
    Returns:
        float: Puntuación de relevancia (0.0 a 1.0)
    """
    # Extraer palabras clave de ambos textos
    keywords_recuerdo = set(extraer_palabras_clave(texto_recuerdo, max_keywords=15))
    keywords_consulta = set(extraer_palabras_clave(consulta, max_keywords=10))
    
    if not keywords_consulta or not keywords_recuerdo:
        return 0.0
    
    # Calcular intersección
    palabras_comunes = keywords_recuerdo.intersection(keywords_consulta)
    
    # Calcular puntuación basada en la proporción de palabras comunes
    if len(keywords_consulta) > 0:
        return len(palabras_comunes) / len(keywords_consulta)
    return 0.0

def calcular_factor_recencia(fecha_recuerdo: datetime, max_dias: int = 30) -> float:
    """
    Calcula factor de recencia para un recuerdo
    
    Args:
        fecha_recuerdo: Fecha del recuerdo
        max_dias: Máximo número de días para considerar (valor mínimo de factor)
        
    Returns:
        float: Factor de recencia (0.0 a 1.0)
    """
    # Calcular días desde el recuerdo
    dias_transcurridos = (datetime.now() - fecha_recuerdo).days
    
    # Limitar a max_dias
    dias_ajustados = min(dias_transcurridos, max_dias)
    
    # Invertir para que recencia más alta (días más cercanos) den valores más altos
    # 1.0 para hoy, decreciendo gradualmente
    return 1.0 - (dias_ajustados / max_dias)

class MemoriaHibrida:
    """
    Gestor de memoria híbrida que combina:
    - Memoria a corto plazo (reciente)
    - Memoria a largo plazo (indexada por embeddings)
    - Ponderación múltiple de relevancia
    """
    def __init__(self, memory_dir: str = "memory", index_dir: str = "embeddings"):
        self.memory_dir = memory_dir
        self.index_dir = index_dir
        self.temas_importantes = set()  # Conjunto de palabras clave consideradas importantes
        
        # Crear directorios si no existen
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Archivo para temas importantes
        self.temas_importantes_path = os.path.join(self.memory_dir, "temas_importantes.json")
        self._cargar_temas_importantes()
        
        # Inicializar índice vectorial si está disponible LlamaIndex
        self.index = None
        if llama_index_disponible:
            self.index = self._load_or_create_index()
            if self.index:
                logger.info("Índice vectorial inicializado correctamente")
            else:
                logger.warning("No se pudo inicializar el índice vectorial. Se trabajará con alternativas.")
        else:
            logger.warning("LlamaIndex no disponible. Se utilizará solo memoria basada en recencia y palabras clave.")
        
        # Imprimir estadísticas iniciales
        self._print_memory_stats()
    
    def _print_memory_stats(self):
        """Imprime estadísticas sobre el estado de la memoria"""
        try:
            memoria_archivos = self._cargar_archivos_recuerdos()
            temas = list(self.temas_importantes)[:5]
            
            logger.info("Estadísticas de memoria híbrida:")
            logger.info(f"   - Archivos de recuerdos: {len(memoria_archivos)}")
            logger.info(f"   - Temas importantes: {len(self.temas_importantes)}")
            
            if temas:
                logger.info(f"   - Ejemplos de temas importantes: {', '.join(temas)}")
                
            if memoria_archivos:
                logger.info(f"   - Último recuerdo: {memoria_archivos[0]}")
                
            if self.index:
                try:
                    num_nodes = len(self.index.docstore.docs)
                    logger.info(f"   - Nodos en índice vectorial: {num_nodes}")
                except:
                    pass
        except Exception as e:
            logger.error(f"Error al imprimir estadísticas: {e}")
    
    def _cargar_temas_importantes(self):
        """Carga la lista de temas importantes desde un archivo JSON"""
        try:
            if os.path.exists(self.temas_importantes_path):
                with open(self.temas_importantes_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.temas_importantes = set(data.get('temas', []))
                    logger.info(f"Cargados {len(self.temas_importantes)} temas importantes")
            else:
                self.temas_importantes = set()
        except Exception as e:
            logger.error(f"Error al cargar temas importantes: {e}")
            self.temas_importantes = set()
    
    def _guardar_temas_importantes(self):
        """Guarda la lista de temas importantes en un archivo JSON"""
        try:
            with open(self.temas_importantes_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'temas': list(self.temas_importantes),
                    'ultima_actualizacion': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"Guardados {len(self.temas_importantes)} temas importantes")
            return True
        except Exception as e:
            logger.error(f"Error al guardar temas importantes: {e}")
            return False
    
    def agregar_tema_importante(self, tema: str) -> bool:
        """
        Agrega un tema a la lista de temas importantes
        
        Args:
            tema: Palabra clave o frase a marcar como importante
            
        Returns:
            bool: True si se agregó correctamente
        """
        try:
            # Normalizar y limpiar
            tema = tema.lower().strip()
            if not tema:
                return False
                
            # Agregar a conjunto
            self.temas_importantes.add(tema)
            
            # Guardar cambios
            return self._guardar_temas_importantes()
        except Exception as e:
            logger.error(f"Error al agregar tema importante: {e}")
            return False
    
    def eliminar_tema_importante(self, tema: str) -> bool:
        """
        Elimina un tema de la lista de temas importantes
        
        Args:
            tema: Tema a eliminar
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            tema = tema.lower().strip()
            if tema in self.temas_importantes:
                self.temas_importantes.remove(tema)
                return self._guardar_temas_importantes()
            return True  # No estaba, así que técnicamente se cumplió la operación
        except Exception as e:
            logger.error(f"Error al eliminar tema importante: {e}")
            return False
    
    def guardar_recuerdo(self, contenido: str, es_importante: bool = False) -> bool:
        """
        Guarda un nuevo recuerdo en el sistema
        
        Args:
            contenido: Texto del recuerdo
            es_importante: Si debe marcarse como importante
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            # Generar nombre único basado en timestamp
            nombre = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Añadir marca si es importante
            if es_importante:
                nombre += "_important"
                
            # Completar con extensión
            nombre += ".txt"
            path = os.path.join(self.memory_dir, nombre)
            
            # Guardar contenido en archivo
            with open(path, "w", encoding="utf-8") as f:
                f.write(contenido)
            
            # Limpiar texto para indexación (eliminar etiquetas thinking)
            texto_limpio = contenido
            if "<think>" in texto_limpio and "</think>" in texto_limpio:
                parts = texto_limpio.split("</think>")
                texto_limpio = parts[-1].strip()
            
            # Extraer palabras clave automáticamente
            palabras_clave = extraer_palabras_clave(texto_limpio)
            
            # Verificar si contiene temas importantes
            contiene_importante = False
            if self.temas_importantes:
                texto_lower = texto_limpio.lower()
                for tema in self.temas_importantes:
                    if tema.lower() in texto_lower:
                        contiene_importante = True
                        break
            
            # Marcar como importante si contiene temas importantes o se especificó
            if contiene_importante and not es_importante:
                # Renombrar archivo para incluir marca
                nuevo_nombre = nombre.replace(".txt", "_important.txt")
                nuevo_path = os.path.join(self.memory_dir, nuevo_nombre)
                os.rename(path, nuevo_path)
                path = nuevo_path
                es_importante = True
            
            # Indexar en memoria vectorial si está disponible
            if self.index:
                try:
                    # Crear documento con metadatos
                    metadatos = {
                        "source": path,
                        "filename": os.path.basename(path),
                        "timestamp": datetime.now().isoformat(),
                        "importante": es_importante,
                        "keywords": ",".join(palabras_clave)
                    }
                    
                    doc = Document(text=texto_limpio, metadata=metadatos)
                    self.index.insert(doc)
                    self.index.storage_context.persist(persist_dir=self.index_dir)
                except Exception as e:
                    logger.error(f"Error al indexar recuerdo: {e}")
            
            logger.info(f"Recuerdo guardado en {nombre} (importante: {es_importante})")
            return True
        except Exception as e:
            logger.error(f"Error al guardar recuerdo: {e}")
            return False
    
    def marcar_recuerdo_importante(self, nombre_archivo: str) -> bool:
        """
        Marca un recuerdo existente como importante
        
        Args:
            nombre_archivo: Nombre del archivo a marcar
            
        Returns:
            bool: True si se modificó correctamente
        """
        try:
            ruta_original = os.path.join(self.memory_dir, nombre_archivo)
            
            # Verificar si ya está marcado
            if "_important" in nombre_archivo:
                return True  # Ya está marcado
                
            # Crear nuevo nombre con marca
            base, ext = os.path.splitext(nombre_archivo)
            nuevo_nombre = f"{base}_important{ext}"
            nueva_ruta = os.path.join(self.memory_dir, nuevo_nombre)
            
            # Renombrar archivo
            os.rename(ruta_original, nueva_ruta)
            
            # Actualizar índice si es posible
            if self.index:
                try:
                    # Leer contenido para reindexar
                    with open(nueva_ruta, "r", encoding="utf-8") as f:
                        contenido = f.read()
                    
                    # Eliminar referencia anterior si existe
                    # Nota: Esto es simplificado, en una implementación real
                    # deberíamos buscar por metadatos
                    
                    # Reindexar con nueva marca
                    texto_limpio = contenido
                    if "<think>" in texto_limpio and "</think>" in texto_limpio:
                        parts = texto_limpio.split("</think>")
                        texto_limpio = parts[-1].strip()
                    
                    doc = Document(
                        text=texto_limpio, 
                        metadata={
                            "source": nueva_ruta,
                            "filename": nuevo_nombre,
                            "importante": True,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    
                    self.index.insert(doc)
                    self.index.storage_context.persist(persist_dir=self.index_dir)
                except Exception as e:
                    logger.error(f"Error al actualizar índice: {e}")
            
            logger.info(f"Recuerdo '{nombre_archivo}' marcado como importante")
            return True
        except Exception as e:
            logger.error(f"Error al marcar recuerdo importante: {e}")
            return False
    
    def _cargar_archivos_recuerdos(self) -> List[str]:
        """
        Obtiene lista de archivos de recuerdos ordenados por fecha
        
        Returns:
            List[str]: Lista de nombres de archivo
        """
        try:
            # Obtener todos los archivos txt excepto configuraciones
            archivos = [
                f for f in os.listdir(self.memory_dir)
                if f.endswith(".txt") and not f.startswith("config") and not f.startswith("preferencia_")
            ]
            
            # Ordenar por fecha de modificación (más recientes primero)
            archivos.sort(key=lambda x: os.path.getmtime(os.path.join(self.memory_dir, x)), reverse=True)
            return archivos
        except Exception as e:
            logger.error(f"Error al cargar archivos de recuerdos: {e}")
            return []
    
    def _extract_datetime_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Extrae fecha y hora de un nombre de archivo con formato YYYYMMDD_HHMMSS
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Optional[datetime]: Objeto datetime o None si no se pudo extraer
        """
        try:
            # Patrón para extraer fecha y hora
            match = re.match(r'(\d{8})_(\d{6})', filename)
            if match:
                date_str, time_str = match.groups()
                year = int(date_str[:4])
                month = int(date_str[4:6])
                day = int(date_str[6:8])
                
                hour = int(time_str[:2])
                minute = int(time_str[2:4])
                second = int(time_str[4:6])
                
                return datetime(year, month, day, hour, minute, second)
            return None
        except Exception:
            return None
    
    def leer_recuerdo(self, nombre: str) -> str:
        """
        Lee el contenido de un recuerdo específico
        
        Args:
            nombre: Nombre del archivo
            
        Returns:
            str: Contenido del recuerdo
        """
        try:
            ruta = os.path.join(self.memory_dir, nombre)
            with open(ruta, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error al leer el recuerdo {nombre}: {e}")
            return f"Error al leer el recuerdo: {e}"
    
    def _load_or_create_index(self):
        """
        Carga o crea el índice vectorial
        
        Returns:
            VectorStoreIndex o None si hay error
        """
        if not llama_index_disponible:
            return None
            
        try:
            # Verificar si existe índice
            if not os.path.exists(self.index_dir) or not os.listdir(self.index_dir):
                return self._create_new_index()
                
            logger.info("Cargando índice desde almacenamiento persistente...")
            from llama_index.core import load_index_from_storage
            return load_index_from_storage(StorageContext.from_defaults(persist_dir=self.index_dir))
        except Exception as e:
            logger.error(f"Error al cargar índice existente: {e}")
            logger.info("Intentando crear nuevo índice...")
            return self._create_new_index(rebuild=True)
    
    def _create_new_index(self, rebuild: bool = False):
        """
        Crea un nuevo índice desde documentos de memoria
        
        Args:
            rebuild: Si se debe reconstruir el índice existente
            
        Returns:
            VectorStoreIndex o None si hay error
        """
        if not llama_index_disponible:
            return None
            
        # Limpiar directorio si se solicita reconstrucción
        if rebuild and os.path.exists(self.index_dir):
            logger.info("Eliminando índice anterior...")
            shutil.rmtree(self.index_dir)
            os.makedirs(self.index_dir, exist_ok=True)
        
        # Cargar documentos
        documentos = self._load_documents()
        logger.info(f"Cargando {len(documentos)} documentos para crear índice...")
        
        try:
            # Crear índice con los documentos
            index = VectorStoreIndex.from_documents(
                documentos,
                embed_model=Settings.embed_model
            )
            index.storage_context.persist(persist_dir=self.index_dir)
            return index
        except Exception as e:
            logger.error(f"Error al crear índice: {e}")
            logger.warning("Creando índice vacío como alternativa")
            try:
                # Crear índice vacío como fallback
                return VectorStoreIndex([])
            except:
                return None
    
    def _load_documents(self) -> List[Document]:
        """
        Carga todos los documentos de memoria para indexación
        
        Returns:
            List[Document]: Lista de documentos de LlamaIndex
        """
        if not llama_index_disponible:
            return []
            
        documentos = []
        for filename in os.listdir(self.memory_dir):
            if filename.endswith('.txt') and not filename.startswith("config"):
                filepath = os.path.join(self.memory_dir, filename)
                try:
                    # Extraer fecha del nombre
                    fecha = self._extract_datetime_from_filename(filename)
                    timestamp = fecha.isoformat() if fecha else datetime.fromtimestamp(
                        os.path.getmtime(filepath)).isoformat()
                    
                    # Determinar si es importante
                    es_importante = "_important" in filename
                    
                    # Leer contenido
                    with open(filepath, "r", encoding="utf-8") as f:
                        text = f.read()
                        
                    # Limpiar formato thinking si existe
                    if "<think>" in text and "</think>" in text:
                        parts = text.split("</think>")
                        text = parts[-1].strip()
                    
                    # Extraer palabras clave
                    palabras_clave = extraer_palabras_clave(text)
                    
                    # Crear documento con metadatos
                    # Crear documento con metadatos
                    doc = Document(
                        text=text, 
                        metadata={
                            "source": filepath,
                            "filename": filename,
                            "timestamp": timestamp,
                            "importante": es_importante,
                            "keywords": ",".join(palabras_clave)
                        }
                    )
                    documentos.append(doc)
                except Exception as e:
                    logger.error(f"Error al leer {filepath}: {e}")
        return documentos
    
    def obtener_recuerdos_recientes(self, limite: int = MAX_RECUERDOS_RECIENTES) -> List[Dict[str, Any]]:
        """
        Obtiene los recuerdos más recientes
        
        Args:
            limite: Número máximo de recuerdos a obtener
            
        Returns:
            List[Dict[str, Any]]: Lista de recuerdos con metadatos
        """
        try:
            # Obtener archivos ordenados por fecha (más recientes primero)
            archivos = self._cargar_archivos_recuerdos()
            archivos = archivos[:limite]  # Limitar cantidad
            
            recuerdos = []
            for archivo in archivos:
                try:
                    ruta = os.path.join(self.memory_dir, archivo)
                    
                    # Determinar si es importante
                    es_importante = "_important" in archivo
                    
                    # Extraer fecha del nombre
                    fecha_obj = self._extract_datetime_from_filename(archivo)
                    if not fecha_obj:
                        fecha_obj = datetime.fromtimestamp(os.path.getmtime(ruta))
                    
                    fecha_str = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Leer contenido
                    with open(ruta, "r", encoding="utf-8") as f:
                        texto = f.read()
                    
                    # Limpiar formato thinking si existe
                    if "<think>" in texto and "</think>" in texto:
                        parts = texto.split("</think>")
                        texto = parts[-1].strip()
                    
                    recuerdos.append({
                        "archivo": archivo,
                        "fecha": fecha_str,
                        "fecha_obj": fecha_obj,
                        "contenido": texto,
                        "importante": es_importante
                    })
                except Exception as e:
                    logger.error(f"Error al procesar recuerdo {archivo}: {e}")
            
            return recuerdos
        except Exception as e:
            logger.error(f"Error al obtener recuerdos recientes: {e}")
            return []
    
    def obtener_contexto_vectorial(self, pregunta: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Obtiene recuerdos usando búsqueda semántica vectorial
        
        Args:
            pregunta: Consulta para buscar contexto relevante
            top_k: Número máximo de resultados
            
        Returns:
            List[Dict[str, Any]]: Lista de recuerdos relevantes con metadatos
        """
        if not self.index:
            logger.warning("Índice vectorial no disponible para búsqueda")
            return []
        
        try:
            # Crear retriever con configuración personalizada
            retriever = self.index.as_retriever(similarity_top_k=top_k)
            
            # Realizar búsqueda
            nodos_resultado = retriever.retrieve(pregunta)
            
            if not nodos_resultado:
                return []
            
            # Convertir nodos a formato unificado
            resultados = []
            for nodo in nodos_resultado:
                # Extraer metadatos
                metadata = nodo.metadata or {}
                filename = metadata.get("filename", "desconocido")
                importante = metadata.get("importante", False)
                
                # Intentar extraer fecha del nombre o usar metadatos
                fecha_obj = None
                if "timestamp" in metadata:
                    try:
                        fecha_obj = datetime.fromisoformat(metadata["timestamp"])
                    except (ValueError, TypeError):
                        pass
                
                if not fecha_obj:
                    fecha_obj = self._extract_datetime_from_filename(filename)
                
                if not fecha_obj and "source" in metadata:
                    try:
                        fecha_obj = datetime.fromtimestamp(os.path.getmtime(metadata["source"]))
                    except (OSError, ValueError):
                        fecha_obj = datetime.now()
                
                fecha_str = fecha_obj.strftime("%Y-%m-%d %H:%M:%S") if fecha_obj else "Fecha desconocida"
                
                # Añadir a resultados
                resultados.append({
                    "archivo": filename,
                    "fecha": fecha_str,
                    "fecha_obj": fecha_obj,
                    "contenido": nodo.text,
                    "score": nodo.score if hasattr(nodo, 'score') else 0.0,
                    "importante": importante
                })
            
            return resultados
        except Exception as e:
            logger.error(f"Error al recuperar contexto vectorial: {e}")
            return []
    
    def obtener_contexto_por_keywords(self, pregunta: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Obtiene recuerdos relevantes basados en palabras clave compartidas
        
        Args:
            pregunta: Consulta para buscar contexto
            top_k: Máximo número de resultados
            
        Returns:
            List[Dict[str, Any]]: Lista de recuerdos con puntuación de relevancia
        """
        try:
            # Obtener todos los recuerdos (limitando para no procesar demasiados)
            archivos = self._cargar_archivos_recuerdos()[:50]  # Limitar búsqueda a los 50 más recientes
            
            # Extraer palabras clave de la consulta
            keywords_consulta = extraer_palabras_clave(pregunta)
            if not keywords_consulta:
                return []
            
            # Lista para almacenar (recuerdo, puntuación)
            puntuaciones = []
            
            for archivo in archivos:
                try:
                    ruta = os.path.join(self.memory_dir, archivo)
                    
                    # Leer contenido
                    with open(ruta, "r", encoding="utf-8") as f:
                        texto = f.read()
                    
                    # Limpiar formato thinking si existe
                    if "<think>" in texto and "</think>" in texto:
                        parts = texto.split("</think>")
                        texto = parts[-1].strip()
                    
                    # Calcular relevancia
                    relevancia = calcular_relevancia_por_keywords(texto, pregunta)
                    
                    # Si supera umbral, añadir a resultados
                    if relevancia > UMBRAL_RELEVANCIA:
                        # Determinar si es importante
                        es_importante = "_important" in archivo
                        
                        # Aplicar bonus de relevancia si es importante
                        if es_importante:
                            relevancia *= PRIORIDAD_TEMA_IMPORTANTE
                        
                        # Extraer fecha
                        fecha_obj = self._extract_datetime_from_filename(archivo)
                        if not fecha_obj:
                            fecha_obj = datetime.fromtimestamp(os.path.getmtime(ruta))
                        
                        fecha_str = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Añadir a puntuaciones
                        puntuaciones.append({
                            "archivo": archivo,
                            "fecha": fecha_str,
                            "fecha_obj": fecha_obj,
                            "contenido": texto,
                            "score": relevancia,
                            "importante": es_importante
                        })
                except Exception as e:
                    logger.error(f"Error al procesar archivo {archivo} para keywords: {e}")
            
            # Ordenar por relevancia (mayor primero)
            puntuaciones.sort(key=lambda x: x["score"], reverse=True)
            
            # Devolver top_k
            return puntuaciones[:top_k]
        except Exception as e:
            logger.error(f"Error al obtener contexto por keywords: {e}")
            return []
    
    def obtener_contexto_combinado(self, pregunta: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Obtiene contexto relevante combinando múltiples estrategias
        
        Args:
            pregunta: Consulta del usuario
            top_k: Número máximo de resultados
            
        Returns:
            List[Dict[str, Any]]: Lista combinada de recuerdos relevantes
        """
        try:
            resultados_combinados = {}
            
            # 1. Obtener recuerdos recientes
            recientes = self.obtener_recuerdos_recientes(limite=MAX_RECUERDOS_RECIENTES)
            
            # 2. Obtener recuerdos por vector embedding
            vectores = self.obtener_contexto_vectorial(pregunta, top_k=top_k)
            
            # 3. Obtener recuerdos por palabras clave
            keywords = self.obtener_contexto_por_keywords(pregunta, top_k=top_k)
            
            # Primero añadir resultados vectoriales con su puntuación
            for rec in vectores:
                archivo = rec["archivo"]
                puntuacion = rec["score"] if "score" in rec else 0.0
                
                # Aplicar peso de estrategia vectorial
                puntuacion_ponderada = puntuacion * PESO_MEMORIA_SEMANTICA
                
                # Aplicar bonus si es importante
                if rec.get("importante", False):
                    puntuacion_ponderada *= PRIORIDAD_TEMA_IMPORTANTE
                
                resultados_combinados[archivo] = {
                    **rec,
                    "score_final": puntuacion_ponderada,
                    "fuente": "vector"
                }
            
            # Añadir resultados por keywords, combinando con existentes si corresponde
            for rec in keywords:
                archivo = rec["archivo"]
                puntuacion = rec["score"] if "score" in rec else 0.0
                
                # Si ya existe, combinar puntuaciones
                if archivo in resultados_combinados:
                    # Promediar con peso actual
                    actual = resultados_combinados[archivo]
                    puntuacion_actual = actual["score_final"]
                    
                    # Aplicar peso de keywords
                    puntuacion_keywords = puntuacion * (1 - PESO_MEMORIA_SEMANTICA)
                    
                    # Actualizar puntuación final
                    resultados_combinados[archivo]["score_final"] = puntuacion_actual + puntuacion_keywords
                    resultados_combinados[archivo]["fuente"] += "+keywords"
                else:
                    # Aplicar peso de keywords
                    puntuacion_ponderada = puntuacion * (1 - PESO_MEMORIA_SEMANTICA)
                    
                    # Aplicar bonus si es importante
                    if rec.get("importante", False):
                        puntuacion_ponderada *= PRIORIDAD_TEMA_IMPORTANTE
                    
                    # Añadir nuevo
                    resultados_combinados[archivo] = {
                        **rec,
                        "score_final": puntuacion_ponderada,
                        "fuente": "keywords"
                    }
            
            # Añadir factor de recencia para recuerdos recientes
            for rec in recientes:
                archivo = rec["archivo"]
                
                # Calcular factor de recencia
                factor_recencia = 0.0
                if "fecha_obj" in rec and rec["fecha_obj"]:
                    factor_recencia = calcular_factor_recencia(rec["fecha_obj"])
                
                # Aplicar peso de recencia
                puntuacion_recencia = factor_recencia * PESO_MEMORIA_RECIENTE
                
                # Aplicar bonus si es importante
                if rec.get("importante", False):
                    puntuacion_recencia *= PRIORIDAD_TEMA_IMPORTANTE
                
                # Si ya existe, sumar componente de recencia
                if archivo in resultados_combinados:
                    resultados_combinados[archivo]["score_final"] += puntuacion_recencia
                    resultados_combinados[archivo]["fuente"] += "+recencia"
                else:
                    # Añadir nuevo solo por recencia
                    resultados_combinados[archivo] = {
                        **rec,
                        "score_final": puntuacion_recencia,
                        "fuente": "recencia"
                    }
            
            # Convertir diccionario a lista
            resultados_lista = list(resultados_combinados.values())
            
            # Ordenar por puntuación final (mayor primero)
            resultados_lista.sort(key=lambda x: x["score_final"], reverse=True)
            
            # Limitar a top_k
            return resultados_lista[:top_k]
        except Exception as e:
            logger.error(f"Error al obtener contexto combinado: {e}")
            
            # Fallback: devolver al menos recuerdos recientes si algo falla
            try:
                return self.obtener_recuerdos_recientes(limite=top_k)
            except:
                return []
    
    def obtener_contexto_relevante(self, pregunta: str, top_k: int = 5) -> str:
        """
        Obtiene contexto relevante a la pregunta y lo formatea como texto
        
        Args:
            pregunta: Consulta del usuario
            top_k: Número máximo de recuerdos a incluir
            
        Returns:
            str: Texto formateado con recuerdos relevantes
        """
        try:
            # Obtener contexto relevante usando todas las estrategias
            resultados = self.obtener_contexto_combinado(pregunta, top_k=top_k)
            
            if not resultados:
                return ""
            
            # Formatear resultados como texto
            contexto = []
            for rec in resultados:
                # Extraer fecha
                fecha = rec.get("fecha", "Fecha desconocida")
                
                # Añadir marca si es importante
                marca = " (⭐)" if rec.get("importante", False) else ""
                
                # Formatear recuerdo
                texto = rec["contenido"].strip()
                contexto.append(f"[Recuerdo del {fecha}{marca}]\n{texto}\n")
            
            return "\n".join(contexto)
        except Exception as e:
            logger.error(f"Error al recuperar contexto relevante: {e}")
            return ""
    
    def cargar_configuracion(self) -> Dict[str, Any]:
        """
        Carga la configuración del sistema
        
        Returns:
            Dict[str, Any]: Configuración cargada o diccionario vacío
        """
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
        """
        Guarda la configuración del sistema
        
        Args:
            configuracion: Diccionario con la configuración
            
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            path = os.path.join(self.memory_dir, "configuracion.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(configuracion, f, indent=2, ensure_ascii=False)
            logger.info("Configuración guardada")
            return True
        except Exception as e:
            logger.error(f"Error al guardar configuración: {e}")
            return False
    
    def obtener_ultima_interaccion(self) -> str:
        """
        Obtiene la fecha de la última interacción
        
        Returns:
            str: Fecha y hora de la última interacción o mensaje predeterminado
        """
        try:
            archivos = self._cargar_archivos_recuerdos()
            if not archivos:
                return "Sin interacciones previas"
            
            archivo_reciente = archivos[0]
            
            # Intentar extraer del nombre del archivo
            fecha_obj = self._extract_datetime_from_filename(archivo_reciente)
            if fecha_obj:
                return fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
            
            # Si no se pudo extraer, usar fecha del sistema de archivos
            ruta_completa = os.path.join(self.memory_dir, archivo_reciente)
            timestamp = os.path.getmtime(ruta_completa)
            return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Error al obtener última interacción: {e}")
            return "Error al determinar fecha"
    
    def obtener_estadisticas_memoria(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas detalladas del sistema de memoria
        
        Returns:
            Dict[str, Any]: Diccionario con estadísticas
        """
        try:
            # Obtener archivos de recuerdos
            archivos = self._cargar_archivos_recuerdos()
            
            # Contar recuerdos importantes
            recuerdos_importantes = sum(1 for a in archivos if "_important" in a)
            
            # Calcular tamaño total
            tamano_total = 0
            for archivo in archivos:
                try:
                    ruta = os.path.join(self.memory_dir, archivo)
                    tamano_total += os.path.getsize(ruta)
                except:
                    pass
            
            # Calcular distribución temporal
            ahora = datetime.now()
            hoy = 0
            semana = 0
            mes = 0
            
            for archivo in archivos:
                try:
                    # Extraer fecha del nombre
                    fecha_obj = self._extract_datetime_from_filename(archivo)
                    if not fecha_obj:
                        ruta = os.path.join(self.memory_dir, archivo)
                        fecha_obj = datetime.fromtimestamp(os.path.getmtime(ruta))
                    
                    # Contar por rangos de tiempo
                    delta = ahora - fecha_obj
                    
                    if delta.days == 0:  # Hoy
                        hoy += 1
                        semana += 1
                        mes += 1
                    elif delta.days < 7:  # Esta semana
                        semana += 1
                        mes += 1
                    elif delta.days < 30:  # Este mes
                        mes += 1
                except:
                    pass
            
            # Recopilar estadísticas
            stats = {
                "total_recuerdos": len(archivos),
                "recuerdos_importantes": recuerdos_importantes,
                "tamano_total_kb": round(tamano_total / 1024, 2),
                "ultima_interaccion": self.obtener_ultima_interaccion(),
                "distribucion_temporal": {
                    "hoy": hoy,
                    "semana": semana,
                    "mes": mes
                },
                "temas_importantes": len(self.temas_importantes),
                "ejemplos_temas": list(self.temas_importantes)[:5]
            }
            
            # Añadir información de vectores si está disponible
            if self.index:
                try:
                    num_nodes = len(self.index.docstore.docs)
                    stats["nodos_indexados"] = num_nodes
                    stats["tipo_indice"] = "VectorStoreIndex"
                except:
                    pass
            
            return stats
        except Exception as e:
            logger.error(f"Error al obtener estadísticas: {e}")
            return {
                "total_recuerdos": len(self._cargar_archivos_recuerdos()),
                "ultima_interaccion": self.obtener_ultima_interaccion(),
                "error": str(e)
            }
    
    def reindexar_memoria(self) -> bool:
        """
        Fuerza una reindexación completa de todos los recuerdos
        
        Returns:
            bool: True si se reindexó correctamente
        """
        try:
            if not llama_index_disponible:
                logger.warning("No se puede reindexar: LlamaIndex no disponible")
                return False
            
            logger.info("Iniciando reindexación de memoria...")
            
            # Crear nuevo índice con reconstrucción
            self.index = self._create_new_index(rebuild=True)
            
            if self.index:
                logger.info("Reindexación completada correctamente")
                return True
            else:
                logger.error("Error al reindexar: no se pudo crear índice")
                return False
        except Exception as e:
            logger.error(f"Error durante reindexación: {e}")
            return False

class MemoryAdapter:
    """
    Adaptador para proporcionar una interfaz común entre diferentes sistemas de memoria
    
    Esta clase permite usar las características avanzadas de MemoriaHibrida cuando está disponible,
    pero mantiene compatibilidad con los sistemas existentes.
    """
    
    def __init__(self, memory_dir: str = "memory"):
        """
        Inicializa el adaptador para memoria
        
        Args:
            memory_dir: Directorio para almacenar memoria
        """
        self.memory_dir = memory_dir
        self.memory_manager = None
        
        # Intentar inicializar en este orden de preferencia
        self._inicializar_memoria()
    
    def _inicializar_memoria(self) -> bool:
        """
        Intenta inicializar los diferentes sistemas de memoria en orden de preferencia
        
        Returns:
            bool: True si algún sistema se inicializó correctamente
        """
        # 1. Intenta con MemoriaHibrida
        try:
            from chatbot.memoria_hibrida import MemoriaHibrida, configurar_embedding_model
            configurar_embedding_model()
            self.memory_manager = MemoriaHibrida(memory_dir=self.memory_dir)
            logger.info("MemoriaHibrida inicializada correctamente")
            self.tipo = "hibrida"
            return True
        except ImportError:
            logger.warning("MemoriaHibrida no disponible, intentando alternativa...")
        except Exception as e:
            logger.error(f"Error al inicializar MemoriaHibrida: {e}")
        
        # 2. Intenta con MemoryManager (vectorial)
        try:
            from chatbot.memoria import MemoryManager, configurar_embedding_model
            configurar_embedding_model()
            self.memory_manager = MemoryManager(memory_dir=self.memory_dir)
            logger.info("MemoryManager (vectorial) inicializado correctamente")
            self.tipo = "vectorial"
            return True
        except ImportError:
            logger.warning("MemoryManager no disponible, intentando alternativa...")
        except Exception as e:
            logger.error(f"Error al inicializar MemoryManager: {e}")
        
        # 3. Última opción: MemoryManagerSimple
        try:
            from chatbot.memoria_simple import MemoryManagerSimple
            self.memory_manager = MemoryManagerSimple(memory_dir=self.memory_dir)
            logger.info("MemoryManagerSimple inicializado como alternativa")
            self.tipo = "simple"
            return True
        except ImportError:
            logger.error("Ningún sistema de memoria disponible")
            self.tipo = "ninguno"
        except Exception as e:
            logger.error(f"Error al inicializar MemoryManagerSimple: {e}")
            self.tipo = "ninguno"
        
        return False
    
    def __getattr__(self, name):
        """
        Delegación de métodos al gestor de memoria actual
        
        Args:
            name: Nombre del método o atributo
            
        Returns:
            El método o atributo del gestor de memoria
            
        Raises:
            AttributeError: Si el método no existe
        """
        if self.memory_manager is None:
            raise AttributeError(f"No hay sistema de memoria inicializado. Método '{name}' no disponible.")
        
        if hasattr(self.memory_manager, name):
            return getattr(self.memory_manager, name)
        else:
            raise AttributeError(f"El método '{name}' no está disponible en el sistema de memoria actual.")
    
    def tiene_capacidad(self, feature: str) -> bool:
        """
        Verifica si el sistema actual tiene una capacidad específica
        
        Args:
            feature: Nombre de la característica a verificar
            
        Returns:
            bool: True si la característica está disponible
        """
        if self.memory_manager is None:
            return False
        
        # Mapeo de características a métodos/atributos que las indican
        feature_map = {
            "vectorial": lambda x: hasattr(x, 'index') and x.index is not None,
            "keywords": lambda x: hasattr(x, 'obtener_contexto_por_keywords'),
            "hibrida": lambda x: hasattr(x, 'obtener_contexto_combinado'),
            "temas_importantes": lambda x: hasattr(x, 'temas_importantes')
        }
        
        if feature in feature_map:
            return feature_map[feature](self.memory_manager)
        
        # Verificar si existe el método/atributo directamente
        return hasattr(self.memory_manager, feature)
    
    def obtener_ultimos_recuerdos(self, n: int = 3) -> List[Dict[str, Any]]:
        """
        Obtiene los N recuerdos más recientes delegando al gestor de memoria subyacente
        
        Args:
            n: Número de recuerdos a obtener
            
        Returns:
            List[Dict[str, Any]]: Lista de los últimos recuerdos
        """
        # Delegación correcta al gestor de memoria
        if hasattr(self.memory_manager, 'obtener_recuerdos_recientes'):
            # Usar método específico si existe (MemoriaHibrida)
            return self.memory_manager.obtener_recuerdos_recientes(limite=n)
            
        elif hasattr(self.memory_manager, '_cargar_archivos_recuerdos'):
            # Implementación alternativa si el gestor tiene los métodos necesarios
            try:
                archivos = self.memory_manager._cargar_archivos_recuerdos()[:n]
                resultados = []
                
                for archivo in archivos:
                    try:
                        contenido = self.memory_manager.leer_recuerdo(archivo)
                        
                        # Intentar extraer fecha con el método del gestor si existe
                        fecha = None
                        if hasattr(self.memory_manager, '_extract_datetime_from_filename'):
                            fecha_obj = self.memory_manager._extract_datetime_from_filename(archivo)
                            if fecha_obj:
                                fecha = fecha_obj.strftime("%Y-%m-%d %H:%M:%S")
                        elif hasattr(self.memory_manager, '_extraer_fecha_de_archivo'):
                            fecha = self.memory_manager._extraer_fecha_de_archivo(archivo)
                        
                        if not fecha:
                            # Extraer fecha del nombre (formato YYYYMMDD_HHMMSS)
                            match = re.match(r'(\d{8})_(\d{6})', archivo)
                            if match:
                                fecha = f"{match.group(1)[:4]}-{match.group(1)[4:6]}-{match.group(1)[6:8]}"
                            else:
                                fecha = "Fecha desconocida"
                        
                        # Determinar si es importante
                        es_importante = "_important" in archivo
                        
                        resultados.append({
                            "id": archivo,
                            "contenido": contenido,
                            "fecha": fecha,
                            "score_final": 0.9,  # Alta relevancia por ser reciente
                            "importante": es_importante
                        })
                    except Exception as e:
                        logger.error(f"Error al leer recuerdo reciente {archivo}: {e}")
                
                return resultados
            except Exception as e:
                logger.error(f"Error al obtener recuerdos recientes: {e}")
                return []
        else:
            # Alternativa simple si no hay métodos específicos
            logger.warning("El gestor de memoria actual no soporta obtener_ultimos_recuerdos")
            return []