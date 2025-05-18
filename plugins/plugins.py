"""
plugins.py - Sistema de plugins para Jarvis
"""
import os
import importlib
import logging
import inspect
from typing import Dict, List, Any, Callable, Optional, Type

logger = logging.getLogger("plugins")

class Plugin:
    """Clase base para todos los plugins de Jarvis"""
    
    # Metadatos que deben ser definidos por cada plugin
    name = "plugin_base"  # Nombre único del plugin
    description = "Plugin base para Jarvis"  # Descripción corta
    version = "0.1.0"  # Versión del plugin
    author = "Desconocido"  # Autor del plugin
    
    # Nivel de prioridad (afecta el orden de carga)
    priority = 50  # Prioridad normal (0-100), valores más altos = mayor prioridad
    
    # Dependencias con otros plugins
    dependencies = []  # Lista de nombres de plugins que deben cargarse antes
    
    def __init__(self, jarvis_instance=None):
        """
        Inicializa el plugin
        
        Args:
            jarvis_instance: Referencia a la instancia principal de Jarvis
        """
        self.jarvis = jarvis_instance
        self.enabled = True
        self.initialized = False
        logger.debug(f"Plugin {self.name} v{self.version} creado")
    
    def initialize(self) -> bool:
        """
        Método llamado durante la fase de inicialización del plugin
        Debe ser sobrescrito por plugins concretos
        
        Returns:
            bool: True si la inicialización fue exitosa, False en caso contrario
        """
        self.initialized = True
        return True
    
    def shutdown(self) -> None:
        """
        Método llamado al finalizar para limpiar recursos
        """
        pass
    
    def get_commands(self) -> Dict[str, Callable]:
        """
        Devuelve un diccionario con los comandos que proporciona este plugin
        
        Returns:
            Dict[str, Callable]: Diccionario con nombre de comando y función a ejecutar
        """
        return {}
    
    def get_hooks(self) -> Dict[str, Callable]:
        """
        Devuelve un diccionario con los hooks (puntos de extensión) que proporciona este plugin
        
        Returns:
            Dict[str, Callable]: Diccionario con nombre de hook y función a ejecutar
        """
        return {}
    
    def can_process_message(self, message: str) -> bool:
        """
        Determina si este plugin puede procesar un mensaje dado
        
        Args:
            message: Mensaje a procesar
            
        Returns:
            bool: True si el plugin puede procesar este mensaje
        """
        return False
    
    def process_message(self, message: str) -> Optional[str]:
        """
        Procesa un mensaje y devuelve una respuesta si es aplicable
        
        Args:
            message: Mensaje a procesar
            
        Returns:
            Optional[str]: Respuesta del plugin o None si no aplica
        """
        return None
    
    def __str__(self) -> str:
        """Representación en texto del plugin"""
        return f"{self.name} v{self.version} por {self.author}"

class PluginManager:
    """Gestiona el ciclo de vida y organización de plugins"""
    
    def __init__(self, plugins_dir: str = "plugins", jarvis_instance=None):
        """
        Inicializa el gestor de plugins
        
        Args:
            plugins_dir: Directorio donde buscar plugins
            jarvis_instance: Referencia a la instancia principal de Jarvis
        """
        self.plugins_dir = plugins_dir
        self.jarvis = jarvis_instance
        self.plugins: Dict[str, Plugin] = {}
        self.commands: Dict[str, Callable] = {}
        self.hooks: Dict[str, List[Callable]] = {}
        self.initialized = False
        
        # Crear directorio si no existe
        os.makedirs(plugins_dir, exist_ok=True)
        
        logger.info(f"PluginManager inicializado. Directorio de plugins: {plugins_dir}")
    
    def discover_plugins(self) -> List[Type[Plugin]]:
        """
        Descubre todos los plugins disponibles en el directorio de plugins
        
        Returns:
            List[Type[Plugin]]: Lista de clases de plugins encontradas
        """
        plugin_classes = []
        
        # Asegurar que el directorio de plugins esté en el path
        plugin_path = os.path.abspath(self.plugins_dir)
        if plugin_path not in os.sys.path:
            os.sys.path.append(plugin_path)
        
        # Buscar archivos Python
        plugin_files = [f[:-3] for f in os.listdir(plugin_path) 
                       if f.endswith(".py") and not f.startswith("__")]
        
        for plugin_file in plugin_files:
            try:
                # Importar el módulo
                module = importlib.import_module(plugin_file)
                
                # Buscar clases de Plugin
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    # Verificar si es una clase, subclase de Plugin y no es la clase base
                    if (inspect.isclass(attr) and 
                        issubclass(attr, Plugin) and 
                        attr is not Plugin):
                        plugin_classes.append(attr)
                        logger.debug(f"Plugin encontrado: {attr.name}")
            except Exception as e:
                logger.error(f"Error al cargar plugin {plugin_file}: {e}")
        
        return plugin_classes
    
    def load_plugins(self) -> int:
        """
        Carga todos los plugins disponibles
        
        Returns:
            int: Número de plugins cargados
        """
        # Descubrir plugins
        plugin_classes = self.discover_plugins()
        
        # Ordenar por prioridad y dependencias
        plugin_classes = self._sort_by_priority(plugin_classes)
        
        # Crear instancias
        for plugin_class in plugin_classes:
            try:
                plugin_instance = plugin_class(self.jarvis)
                self.plugins[plugin_class.name] = plugin_instance
                logger.info(f"Plugin cargado: {plugin_instance}")
            except Exception as e:
                logger.error(f"Error al crear instancia de {plugin_class.name}: {e}")
        
        return len(self.plugins)
    
    def initialize_plugins(self) -> Dict[str, bool]:
        """
        Inicializa todos los plugins cargados
        
        Returns:
            Dict[str, bool]: Diccionario con nombre de plugin y éxito de inicialización
        """
        results = {}
        
        # Inicializar plugins
        for name, plugin in self.plugins.items():
            try:
                success = plugin.initialize()
                results[name] = success
                
                if success:
                    # Registrar comandos
                    self._register_plugin_commands(plugin)
                    
                    # Registrar hooks
                    self._register_plugin_hooks(plugin)
                    
                    logger.info(f"Plugin inicializado: {name}")
                else:
                    logger.warning(f"Plugin no se pudo inicializar: {name}")
            except Exception as e:
                logger.error(f"Error al inicializar plugin {name}: {e}")
                results[name] = False
        
        self.initialized = True
        return results
    
    def _register_plugin_commands(self, plugin: Plugin) -> None:
        """
        Registra los comandos proporcionados por un plugin
        
        Args:
            plugin: Plugin cuyos comandos se registrarán
        """
        plugin_commands = plugin.get_commands()
        for cmd_name, cmd_func in plugin_commands.items():
            # Evitar sobrescribir comandos existentes de mayor prioridad
            if cmd_name in self.commands:
                existing_plugin = self._find_plugin_by_command(cmd_name)
                if existing_plugin and existing_plugin.priority >= plugin.priority:
                    logger.warning(f"Comando '{cmd_name}' de {plugin.name} ignorado, ya existe en {existing_plugin.name} con mayor prioridad")
                    continue
            
            self.commands[cmd_name] = cmd_func
            logger.debug(f"Comando '{cmd_name}' registrado desde {plugin.name}")
    
    def _register_plugin_hooks(self, plugin: Plugin) -> None:
        """
        Registra los hooks proporcionados por un plugin
        
        Args:
            plugin: Plugin cuyos hooks se registrarán
        """
        plugin_hooks = plugin.get_hooks()
        for hook_name, hook_func in plugin_hooks.items():
            if hook_name not in self.hooks:
                self.hooks[hook_name] = []
            
            self.hooks[hook_name].append(hook_func)
            logger.debug(f"Hook '{hook_name}' registrado desde {plugin.name}")
    
    def _find_plugin_by_command(self, cmd_name: str) -> Optional[Plugin]:
        """
        Encuentra el plugin que registró un comando dado
        
        Args:
            cmd_name: Nombre del comando
            
        Returns:
            Optional[Plugin]: Plugin que registró el comando o None
        """
        for plugin in self.plugins.values():
            if cmd_name in plugin.get_commands():
                return plugin
        return None
    
    def _sort_by_priority(self, plugin_classes: List[Type[Plugin]]) -> List[Type[Plugin]]:
        """
        Ordena las clases de plugins por prioridad y dependencias
        
        Args:
            plugin_classes: Lista de clases de plugins
            
        Returns:
            List[Type[Plugin]]: Lista ordenada de clases de plugins
        """
        # Crear grafo de dependencias y mapa de prioridades
        dependencies = {}
        priorities = {}
        
        for plugin_class in plugin_classes:
            name = plugin_class.name
            dependencies[name] = plugin_class.dependencies
            priorities[name] = plugin_class.priority
        
        # Crear orden respetando dependencias
        sorted_names = self._topological_sort(dependencies)
        
        # Si hay ciclos, ordenar solo por prioridad
        if not sorted_names:
            logger.warning("Ciclo de dependencias detectado, ordenando solo por prioridad")
            sorted_names = sorted(priorities.keys(), key=lambda n: priorities[n], reverse=True)
        
        # Mapear nombres a clases
        name_to_class = {pc.name: pc for pc in plugin_classes}
        sorted_classes = [name_to_class[name] for name in sorted_names if name in name_to_class]
        
        return sorted_classes
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """
        Realiza un ordenamiento topológico del grafo de dependencias
        
        Args:
            graph: Grafo de dependencias (nodo -> dependencias)
            
        Returns:
            List[str]: Lista ordenada de nodos o lista vacía si hay ciclos
        """
        # Inicializar resultado y nodos visitados
        result = []
        visited = set()
        temp_visit = set()
        
        def visit(node):
            # Detectar ciclos
            if node in temp_visit:
                return False
            
            # Saltar nodos ya visitados
            if node in visited:
                return True
            
            # Marcar como temporalmente visitado
            temp_visit.add(node)
            
            # Visitar dependencias
            for dep in graph.get(node, []):
                if dep not in graph:
                    logger.warning(f"Dependencia {dep} no encontrada para {node}")
                    continue
                    
                if not visit(dep):
                    return False
            
            # Marcar como visitado permanentemente
            temp_visit.remove(node)
            visited.add(node)
            result.append(node)
            
            return True
        
        # Visitar todos los nodos
        for node in graph:
            if not visit(node):
                return []  # Ciclo detectado
        
        return result[::-1]  # Invertir para tener orden correcto
    
    def execute_command(self, cmd_name: str, *args, **kwargs) -> Any:
        """
        Ejecuta un comando registrado por nombre
        
        Args:
            cmd_name: Nombre del comando a ejecutar
            *args: Argumentos posicionales para el comando
            **kwargs: Argumentos nombrados para el comando
            
        Returns:
            Any: Resultado de la ejecución del comando
            
        Raises:
            KeyError: Si el comando no existe
        """
        if not self.initialized:
            raise RuntimeError("PluginManager no inicializado")
            
        if cmd_name not in self.commands:
            raise KeyError(f"Comando no encontrado: {cmd_name}")
            
        return self.commands[cmd_name](*args, **kwargs)
    
    def trigger_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Ejecuta todos los hooks registrados para un punto de extensión
        
        Args:
            hook_name: Nombre del hook a ejecutar
            *args: Argumentos posicionales para el hook
            **kwargs: Argumentos nombrados para el hook
            
        Returns:
            List[Any]: Lista de resultados de todos los hooks ejecutados
        """
        if not self.initialized:
            raise RuntimeError("PluginManager no inicializado")
            
        results = []
        
        for hook_func in self.hooks.get(hook_name, []):
            try:
                result = hook_func(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Error al ejecutar hook {hook_name}: {e}")
                results.append(None)
        
        return results
    
    def process_message(self, message: str) -> Optional[str]:
        """
        Procesa un mensaje a través de todos los plugins
        
        Args:
            message: Mensaje a procesar
            
        Returns:
            Optional[str]: Primera respuesta válida o None si ningún plugin responde
        """
        if not self.initialized:
            logger.warning("PluginManager no inicializado, no se procesará el mensaje")
            return None
            
        # Dar a cada plugin oportunidad de procesar el mensaje
        for plugin in self.plugins.values():
            if not plugin.enabled:
                continue
                
            try:
                if plugin.can_process_message(message):
                    response = plugin.process_message(message)
                    if response:
                        return response
            except Exception as e:
                logger.error(f"Error al procesar mensaje en plugin {plugin.name}: {e}")
        
        return None
    
    def get_plugin_info(self) -> List[Dict[str, Any]]:
        """
        Obtiene información de todos los plugins cargados
        
        Returns:
            List[Dict[str, Any]]: Lista de diccionarios con información de plugins
        """
        info = []
        
        for name, plugin in self.plugins.items():
            plugin_info = {
                "name": plugin.name,
                "description": plugin.description,
                "version": plugin.version,
                "author": plugin.author,
                "priority": plugin.priority,
                "enabled": plugin.enabled,
                "initialized": plugin.initialized,
                "commands": list(plugin.get_commands().keys()),
                "hooks": list(plugin.get_hooks().keys()),
                "dependencies": plugin.dependencies
            }
            info.append(plugin_info)
        
        return info
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Habilita un plugin por nombre
        
        Args:
            plugin_name: Nombre del plugin a habilitar
            
        Returns:
            bool: True si se habilitó correctamente, False en caso contrario
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin no encontrado: {plugin_name}")
            return False
            
        self.plugins[plugin_name].enabled = True
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Deshabilita un plugin por nombre
        
        Args:
            plugin_name: Nombre del plugin a deshabilitar
            
        Returns:
            bool: True si se deshabilitó correctamente, False en caso contrario
        """
        if plugin_name not in self.plugins:
            logger.warning(f"Plugin no encontrado: {plugin_name}")
            return False
            
        self.plugins[plugin_name].enabled = False
        return True
    
    def shutdown(self) -> None:
        """
        Cierra ordenadamente todos los plugins
        """
        if not self.initialized:
            return
            
        for name, plugin in self.plugins.items():
            try:
                plugin.shutdown()
                logger.debug(f"Plugin {name} cerrado correctamente")
            except Exception as e:
                logger.error(f"Error al cerrar plugin {name}: {e}")
        
        self.initialized = False
        logger.info("PluginManager cerrado correctamente")