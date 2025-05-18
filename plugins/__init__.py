"""
plugins.py - Sistema de plugins para Jarvis
"""
import os
import importlib
import logging
import inspect
import sys
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
        """Inicializa el plugin"""
        self.jarvis = jarvis_instance
        self.enabled = True
        self.config = {}
        self.initialize()
    
    def initialize(self) -> bool:
        """
        Método de inicialización que debe ser implementado por cada plugin
        
        Returns:
            bool: True si la inicialización fue exitosa, False en caso contrario
        """
        return True
    
    def shutdown(self) -> bool:
        """
        Método para realizar tareas de limpieza al desactivar el plugin
        
        Returns:
            bool: True si la limpieza fue exitosa, False en caso contrario
        """
        return True
    
    def get_commands(self) -> Dict[str, Callable]:
        """
        Devuelve un diccionario de comandos que registra este plugin
        
        Returns:
            Dict[str, Callable]: Diccionario con nombres de comandos y sus funciones
        """
        return {}
    
    def can_process_message(self, message: str) -> bool:
        """
        Determina si este plugin puede procesar un mensaje específico
        
        Args:
            message: Mensaje a evaluar
            
        Returns:
            bool: True si el plugin puede procesar este mensaje
        """
        return False
    
    def process_message(self, message: str, user_id: str = None) -> Optional[str]:
        """
        Procesa un mensaje y devuelve una respuesta
        
        Args:
            message: Mensaje a procesar
            user_id: Identificador del usuario (opcional)
            
        Returns:
            Optional[str]: Respuesta generada o None si no procesa
        """
        return None
    
    def on_response_generated(self, message: str, response: str, user_id: str = None) -> str:
        """
        Hook que se ejecuta después de que se genera una respuesta
        Permite modificar o añadir información a la respuesta
        
        Args:
            message: Mensaje original
            response: Respuesta generada
            user_id: Identificador del usuario (opcional)
            
        Returns:
            str: Respuesta posiblemente modificada
        """
        return response
    
    def get_help(self) -> str:
        """
        Proporciona texto de ayuda para este plugin
        
        Returns:
            str: Texto de ayuda formateado
        """
        commands = self.get_commands()
        help_text = f"## {self.name} v{self.version}\n\n"
        help_text += f"{self.description}\n\n"
        
        if commands:
            help_text += "### Comandos disponibles\n\n"
            for cmd_name, cmd_func in commands.items():
                doc = cmd_func.__doc__ or "Sin descripción"
                help_text += f"- **{cmd_name}**: {doc.strip()}\n"
        
        return help_text
    
    def load_config(self) -> Dict[str, Any]:
        """
        Carga la configuración del plugin desde el sistema
        
        Returns:
            Dict[str, Any]: Configuración del plugin
        """
        config_dir = os.path.join("config", "plugins")
        config_file = os.path.join(config_dir, f"{self.name}.json")
        
        # Crear directorio si no existe
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"Error al crear directorio de configuración: {e}")
                return {}
        
        # Intentar cargar configuración
        try:
            import json
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    logger.info(f"Configuración cargada para plugin {self.name}")
                    return self.config
        except Exception as e:
            logger.error(f"Error al cargar configuración del plugin {self.name}: {e}")
            
        return {}
    
    def save_config(self) -> bool:
        """
        Guarda la configuración actual del plugin
        
        Returns:
            bool: True si se guardó correctamente
        """
        config_dir = os.path.join("config", "plugins")
        config_file = os.path.join(config_dir, f"{self.name}.json")
        
        # Crear directorio si no existe
        if not os.path.exists(config_dir):
            try:
                os.makedirs(config_dir, exist_ok=True)
            except Exception as e:
                logger.error(f"Error al crear directorio de configuración: {e}")
                return False
        
        # Guardar configuración
        try:
            import json
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuración guardada para plugin {self.name}")
            return True
        except Exception as e:
            logger.error(f"Error al guardar configuración del plugin {self.name}: {e}")
            return False
    
    def register_scheduled_task(self, task_func: Callable, interval_seconds: int) -> bool:
        """
        Registra una tarea programada para ejecutarse periódicamente
        
        Args:
            task_func: Función a ejecutar
            interval_seconds: Intervalo en segundos entre ejecuciones
            
        Returns:
            bool: True si se registró correctamente
        """
        if self.jarvis is None:
            logger.error(f"No se puede registrar tarea programada para {self.name}: instancia Jarvis no disponible")
            return False
            
        if hasattr(self.jarvis, 'scheduler') and self.jarvis.scheduler is not None:
            try:
                self.jarvis.scheduler.add_task(task_func, interval_seconds, self.name)
                logger.info(f"Tarea programada registrada para plugin {self.name}")
                return True
            except Exception as e:
                logger.error(f"Error al registrar tarea programada para {self.name}: {e}")
        else:
            logger.warning(f"No se puede registrar tarea programada para {self.name}: programador no disponible")
            
        return False
    
    def get_web_components(self) -> Dict[str, Any]:
        """
        Devuelve componentes para la interfaz web
        
        Returns:
            Dict[str, Any]: Diccionario con componentes para la UI
        """
        return {}
    
    def handle_api_call(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja llamadas API dirigidas al plugin
        
        Args:
            endpoint: Punto final API específico
            data: Datos de la solicitud
            
        Returns:
            Dict[str, Any]: Respuesta de la API
        """
        return {"error": "API no implementada para este plugin"}

class PluginManager:
    """Gestor de plugins para Jarvis"""
    
    def __init__(self, jarvis_instance=None, plugins_dir: str = "plugins"):
        """
        Inicializa el gestor de plugins
        
        Args:
            jarvis_instance: Instancia principal de Jarvis
            plugins_dir: Directorio donde buscar plugins
        """
        self.jarvis = jarvis_instance
        self.plugins_dir = plugins_dir
        self.plugins = {}  # name -> instance
        self.commands = {}  # command -> (plugin, function)
        
        # Crear directorio de plugins si no existe
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir, exist_ok=True)
            
        logger.info("Gestor de plugins inicializado")
    
    def discover_plugins(self) -> List[str]:
        """
        Descubre plugins disponibles (archivos .py en el directorio de plugins)
        
        Returns:
            List[str]: Lista de nombres de módulos de plugin encontrados
        """
        plugin_modules = []
        
        try:
            for item in os.listdir(self.plugins_dir):
                # Ignorar __init__.py, plugins.py, y otros archivos especiales
                if (item.endswith(".py") and 
                    not item.startswith("__") and 
                    item != "plugins.py"):
                    plugin_modules.append(item[:-3])  # Quitar extensión .py
        except Exception as e:
            logger.error(f"Error al descubrir plugins: {e}")
        
        logger.info(f"Plugins descubiertos: {plugin_modules}")
        return plugin_modules
    
    def load_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """
        Carga un plugin específico por nombre
        
        Args:
            plugin_name: Nombre del módulo del plugin
            
        Returns:
            Optional[Plugin]: Instancia del plugin o None si falló
        """
        # Si ya está cargado, devolver la instancia
        if plugin_name in self.plugins:
            return self.plugins[plugin_name]
            
        try:
            # Importar módulo dinámicamente
            module_path = f"{self.plugins_dir}.{plugin_name}"
            module = importlib.import_module(module_path)
            
            # Buscar subclases de Plugin en el módulo
            plugin_classes = []
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, Plugin) and obj is not Plugin:
                    plugin_classes.append(obj)
            
            if not plugin_classes:
                logger.warning(f"No se encontraron clases de Plugin en {plugin_name}")
                return None
            
            # Usar la primera clase de plugin encontrada
            plugin_class = plugin_classes[0]
            plugin_instance = plugin_class(self.jarvis)
            
            # Verificar nombre único
            if plugin_instance.name in self.plugins:
                logger.warning(f"Plugin con nombre duplicado: {plugin_instance.name}")
                return None
            
            # Cargar configuración
            plugin_instance.load_config()
            
            # Registrar plugin y sus comandos
            self.plugins[plugin_instance.name] = plugin_instance
            self._register_plugin_commands(plugin_instance)
            
            logger.info(f"Plugin cargado: {plugin_instance.name} v{plugin_instance.version}")
            return plugin_instance
                
        except Exception as e:
            logger.error(f"Error al cargar plugin {plugin_name}: {e}")
            return None
    
    def load_all_plugins(self) -> Dict[str, Plugin]:
        """
        Carga todos los plugins disponibles
        
        Returns:
            Dict[str, Plugin]: Diccionario de plugins cargados (nombre -> instancia)
        """
        # Descubrir plugins disponibles
        plugin_modules = self.discover_plugins()
        
        # Ordenar para dependencias
        loaded_plugins = {}
        
        # Primer intento: cargar plugins sin dependencias
        for plugin_name in plugin_modules:
            plugin = self.load_plugin(plugin_name)
            if plugin and not plugin.dependencies:
                loaded_plugins[plugin.name] = plugin
        
        # Segundo intento: cargar plugins con dependencias
        remaining = [p for p in plugin_modules if p not in [plugin.name for plugin in loaded_plugins.values()]]
        for plugin_name in remaining:
            self.load_plugin(plugin_name)  # Intentar cargar los restantes
        
        logger.info(f"Plugins cargados: {len(self.plugins)}/{len(plugin_modules)}")
        return self.plugins
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Desactiva y descarga un plugin
        
        Args:
            plugin_name: Nombre del plugin a descargar
            
        Returns:
            bool: True si se descargó correctamente
        """
        if plugin_name not in self.plugins:
            logger.warning(f"No se puede descargar plugin no encontrado: {plugin_name}")
            return False
        
        plugin = self.plugins[plugin_name]
        
        # Eliminar comandos registrados
        for cmd_name, (plg, _) in list(self.commands.items()):
            if plg.name == plugin_name:
                del self.commands[cmd_name]
        
        # Ejecutar limpieza del plugin
        try:
            plugin.shutdown()
        except Exception as e:
            logger.error(f"Error en shutdown del plugin {plugin_name}: {e}")
        
        # Eliminar plugin
        del self.plugins[plugin_name]
        logger.info(f"Plugin descargado: {plugin_name}")
        
        return True
    
    def _register_plugin_commands(self, plugin: Plugin) -> None:
        """
        Registra los comandos proporcionados por un plugin
        
        Args:
            plugin: Instancia del plugin
        """
        commands = plugin.get_commands()
        
        for cmd_name, cmd_func in commands.items():
            # Verificar duplicados
            if cmd_name in self.commands:
                existing_plugin = self.commands[cmd_name][0].name
                # Si el nuevo plugin tiene mayor prioridad, sobrescribir
                if plugin.priority > self.commands[cmd_name][0].priority:
                    logger.warning(f"Comando '{cmd_name}' de {existing_plugin} sobrescrito por {plugin.name} (prioridad mayor)")
                    self.commands[cmd_name] = (plugin, cmd_func)
                else:
                    logger.warning(f"Comando '{cmd_name}' de {plugin.name} ignorado, ya existe en {existing_plugin}")
            else:
                self.commands[cmd_name] = (plugin, cmd_func)
        
        logger.debug(f"Registrados {len(commands)} comandos para {plugin.name}")
    
    def execute_command(self, cmd_name: str, *args, **kwargs) -> Any:
        """
        Ejecuta un comando registrado
        
        Args:
            cmd_name: Nombre del comando
            *args, **kwargs: Argumentos para pasar al comando
            
        Returns:
            Any: Resultado de la ejecución del comando
        """
        if cmd_name not in self.commands:
            logger.warning(f"Comando no encontrado: {cmd_name}")
            return f"Comando '{cmd_name}' no encontrado"
        
        plugin, func = self.commands[cmd_name]
        
        if not plugin.enabled:
            logger.warning(f"Intento de ejecutar comando de plugin desactivado: {plugin.name}")
            return f"El plugin '{plugin.name}' está desactivado"
        
        try:
            logger.debug(f"Ejecutando comando '{cmd_name}' del plugin '{plugin.name}'")
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error al ejecutar comando '{cmd_name}': {e}")
            return f"Error al ejecutar '{cmd_name}': {str(e)}"
    
    def process_message(self, message: str, user_id: str = None) -> Optional[str]:
        """
        Intenta procesar un mensaje con plugins compatibles
        
        Args:
            message: Mensaje a procesar
            user_id: ID del usuario (opcional)
            
        Returns:
            Optional[str]: Respuesta si algún plugin procesó el mensaje, None en caso contrario
        """
        # Ordenar plugins por prioridad (mayor primero)
        plugins_sorted = sorted(
            self.plugins.values(),
            key=lambda p: p.priority,
            reverse=True
        )
        
        # Intentar procesar con cada plugin habilitado
        for plugin in plugins_sorted:
            if not plugin.enabled:
                continue
                
            try:
                if plugin.can_process_message(message):
                    logger.debug(f"Mensaje procesado por plugin: {plugin.name}")
                    return plugin.process_message(message, user_id)
            except Exception as e:
                logger.error(f"Error al procesar mensaje con plugin {plugin.name}: {e}")
        
        return None
    
    def modify_response(self, message: str, response: str, user_id: str = None) -> str:
        """
        Permite a los plugins modificar la respuesta generada
        
        Args:
            message: Mensaje original
            response: Respuesta generada
            user_id: ID del usuario (opcional)
            
        Returns:
            str: Respuesta posiblemente modificada
        """
        modified_response = response
        
        # Aplicar modificaciones de cada plugin habilitado
        for plugin in self.plugins.values():
            if plugin.enabled:
                try:
                    modified_response = plugin.on_response_generated(message, modified_response, user_id)
                except Exception as e:
                    logger.error(f"Error en plugin {plugin.name} al modificar respuesta: {e}")
        
        return modified_response
    
    def get_help(self) -> str:
        """
        Obtiene texto de ayuda de todos los plugins
        
        Returns:
            str: Texto de ayuda formateado
        """
        help_text = "# Ayuda de Plugins\n\n"
        
        if not self.plugins:
            help_text += "No hay plugins cargados.\n"
            return help_text
        
        # Plugins por categoría
        for plugin in sorted(self.plugins.values(), key=lambda p: p.name):
            if plugin.enabled:
                help_text += f"## {plugin.name}\n\n"
                help_text += f"{plugin.description}\n\n"
                help_text += f"**Versión:** {plugin.version} | **Autor:** {plugin.author}\n\n"
                
                # Comandos del plugin
                commands = plugin.get_commands()
                if commands:
                    help_text += "### Comandos\n\n"
                    for cmd_name, cmd_func in commands.items():
                        doc = cmd_func.__doc__ or "Sin descripción"
                        help_text += f"- **{cmd_name}**: {doc.strip()}\n"
                    help_text += "\n"
                
        return help_text
    
    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene el estado de todos los plugins
        
        Returns:
            Dict[str, Dict[str, Any]]: Estado de los plugins
        """
        status = {}
        
        for name, plugin in self.plugins.items():
            plugin_info = {
                "name": name,
                "description": plugin.description,
                "version": plugin.version,
                "author": plugin.author,
                "enabled": plugin.enabled,
                "priority": plugin.priority,
                "dependencies": plugin.dependencies,
                "commands": list(plugin.get_commands().keys())
            }
            status[name] = plugin_info
            
        return status
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        Activa un plugin
        
        Args:
            plugin_name: Nombre del plugin
            
        Returns:
            bool: True si se activó correctamente
        """
        if plugin_name not in self.plugins:
            logger.warning(f"No se puede activar plugin no encontrado: {plugin_name}")
            return False
            
        self.plugins[plugin_name].enabled = True
        logger.info(f"Plugin activado: {plugin_name}")
        return True
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        Desactiva un plugin
        
        Args:
            plugin_name: Nombre del plugin
            
        Returns:
            bool: True si se desactivó correctamente
        """
        if plugin_name not in self.plugins:
            logger.warning(f"No se puede desactivar plugin no encontrado: {plugin_name}")
            return False
            
        self.plugins[plugin_name].enabled = False
        logger.info(f"Plugin desactivado: {plugin_name}")
        return True
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Recarga un plugin
        
        Args:
            plugin_name: Nombre del plugin
            
        Returns:
            bool: True si se recargó correctamente
        """
        if plugin_name not in self.plugins:
            logger.warning(f"No se puede recargar plugin no encontrado: {plugin_name}")
            return False
            
        # Obtener módulo original
        module_name = None
        for name, plugin in self.plugins.items():
            if name == plugin_name:
                module_name = plugin.__class__.__module__.split(".")[-1]
                break
                
        if not module_name:
            logger.error(f"No se pudo determinar el módulo para {plugin_name}")
            return False
            
        # Descargar y volver a cargar
        self.unload_plugin(plugin_name)
        
        # Recargar módulo
        try:
            module_path = f"{self.plugins_dir}.{module_name}"
            importlib.reload(sys.modules[module_path])
        except Exception as e:
            logger.error(f"Error al recargar módulo {module_name}: {e}")
        
        # Cargar plugin
        plugin = self.load_plugin(module_name)
        
        return plugin is not None
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """
        Obtiene la instancia de un plugin por nombre
        
        Args:
            plugin_name: Nombre del plugin
            
        Returns:
            Optional[Plugin]: Instancia del plugin o None si no existe
        """
        return self.plugins.get(plugin_name)
    
    def initialize_plugins(self) -> List[str]:
        """
        Inicializa todos los plugins cargados
        
        Returns:
            List[str]: Nombres de los plugins inicializados correctamente
        """
        initialized = []
        
        for name, plugin in self.plugins.items():
            try:
                success = plugin.initialize()
                if success:
                    logger.info(f"Plugin inicializado: {name}")
                    initialized.append(name)
                else:
                    logger.warning(f"Plugin {name} no se inicializó correctamente")
            except Exception as e:
                logger.error(f"Error al inicializar plugin {name}: {e}")
        
        logger.info(f"Se inicializaron {len(initialized)}/{len(self.plugins)} plugins")
        return initialized
    
    def load_plugins(self) -> int:
        """
        Carga todos los plugins disponibles
        
        Returns:
            int: Número de plugins cargados con éxito
        """
        plugins = self.load_all_plugins()
        return len(plugins)

# Exportar clases principales
__all__ = ['Plugin', 'PluginManager']