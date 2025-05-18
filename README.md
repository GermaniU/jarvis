# Guía de Instalación y Migración de Jarvis 2.0

Este documento explica los pasos necesarios para instalar el nuevo sistema Jarvis 2.0 o actualizar desde una versión anterior. El proceso ha sido diseñado para ser lo más sencillo posible minimizando el riesgo de pérdida de datos.

## Requisitos del Sistema

- Python 3.8 o superior
- 4GB de RAM mínimo (8GB recomendado)
- 2GB de espacio en disco
- Conexión a Internet para búsquedas web y actualizaciones

### Dependencias Principales

- llama-index 0.9.x o superior
- pyttsx3 (para funcionalidad de voz)
- requests y beautifulsoup4 (para módulo web)
- gradio (para interfaz gráfica)

## Instalación desde Cero

### 1. Configuración del Entorno

```bash
# Crear y activar entorno virtual
python -m venv jarvis-env
source jarvis-env/bin/activate  # Linux/Mac
# o
jarvis-env\Scripts\activate.bat  # Windows

# Clonar el repositorio
git clone https://github.com/tu-repo/jarvis.git
cd jarvis

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración Inicial

```bash
# Crear directorios necesarios
mkdir -p memory
mkdir -p memory/web_cache
mkdir -p plugins
mkdir -p logs

# Copiar archivo de configuración de ejemplo
cp config_sample.py config.py

# Editar configuración según necesidades
nano config.py
```

### 3. Primer Inicio

```bash
# Probar en modo CLI
python main.py

# Probar en modo GUI
python main.py --gui
```

## Migración desde Versión Anterior

### 1. Respaldo de Datos

Antes de migrar, es fundamental realizar un respaldo de todos los datos:

```bash
# Respaldar directorio de memoria
cp -r memory memory_backup_$(date +%Y%m%d)

# Respaldar configuración
cp config.py config_backup.py

# Comprimir respaldo (opcional)
tar -czvf jarvis_backup_$(date +%Y%m%d).tar.gz memory_backup_* config_backup.py
```

### 2. Actualización de Código

```bash
# Si usas git
git pull origin main

# O reemplazar archivos manualmente
cp -r /ruta/al/nuevo/codigo/* .
```

### 3. Actualización de Estructura de Directorios

```bash
# Crear nuevos directorios necesarios
mkdir -p plugins
mkdir -p logs

# Migrar caché web (si existe)
if [ -d memory/web_cache ]; then
    # Ya existe estructura
    echo "Estructura de caché web encontrada"
else
    # Crear directorio para caché web
    mkdir -p memory/web_cache
    
    # Migrar archivos de caché si existen en otra ubicación
    if [ -d web_cache ]; then
        mv web_cache/* memory/web_cache/
    fi
fi
```

### 4. Migración de Plugins Personalizados

Si tenías plugins o extensiones personalizadas en la versión anterior:

1. Revisar estructura actual de plugins
2. Adaptar código existente al nuevo formato de plugins
3. Colocar en el directorio `plugins/`

Ejemplo de conversión de extensión a plugin:

```python
# Antes (extensión.py)
def mi_funcion(mensaje):
    # Código...
    return respuesta

# Después (plugins/mi_plugin.py)
from plugins import Plugin

class MiPlugin(Plugin):
    name = "mi_plugin"
    description = "Mi plugin personalizado"
    version = "1.0.0"
    
    def initialize(self):
        return True
        
    def get_commands(self):
        return {
            "mi_comando": self.mi_funcion
        }
        
    def mi_funcion(self, mensaje):
        # Código...
        return respuesta

def get_plugin_class():
    return MiPlugin
```

### 5. Actualización de Dependencias

```bash
# Actualizar dependencias
pip install --upgrade -r requirements.txt
```

### 6. Verificación

```bash
# Ejecutar en modo de diagnóstico
python main.py --debug

# Verificar logs en logs/jarvis_main.log
```

## Estructura de Directorios

Después de la instalación, la estructura debería ser similar a:

```
jarvis/
├── main.py              # Punto de entrada principal
├── config.py            # Configuración global
├── requirements.txt     # Dependencias
├── chatbot/             # Módulos principales
│   ├── __init__.py
│   ├── asistente.py     # Integración con LLM
│   ├── interfaz.py      # Interfaz de consola
│   ├── llm_wrapper.py   # Wrapper para LLM
│   ├── memoria.py       # Sistema de memoria completo
│   ├── memoria_simple.py # Sistema de memoria fallback
│   ├── voz.py           # Sistema de voz (legacy)
│   └── web/             # Módulo web refactorizado
│       ├── __init__.py
│       ├── cache.py     # Gestión de caché
│       ├── extractores.py # Extractores de contenido
│       ├── motor.py     # Motor web principal
│       └── utils.py     # Utilidades
├── plugins/             # Plugins del sistema
│   ├── __init__.py
│   ├── plugins.py       # Sistema de plugins
│   ├── voice_plugin.py  # Plugin de voz
│   └── ...              # Otros plugins
├── memory/              # Datos persistentes
│   ├── configuracion.json # Configuración del usuario
│   ├── *.txt            # Recuerdos guardados
│   └── web_cache/       # Caché de búsquedas web
├── embeddings/          # Índices vectoriales
└── logs/                # Archivos de registro
```

## Configuración Avanzada

### Personalización del Modelo LLM

Editar `config.py` para cambiar el modelo usado:

```python
# Usar modelo Ollama local
DEFAULT_MODEL = "ollama"
DEFAULT_MODEL_NAME = "deepseek-r1:14b"

# O usar modelo de API externa
# DEFAULT_MODEL = "anthropic"
# API_KEY = "tu_api_key_aquí"
```

### Activar/Desactivar Componentes

Para activar o desactivar componentes específicos:

```python
# En config.py
ENABLE_VOICE = True  # Activar/desactivar sistema de voz
ENABLE_WEB = True    # Activar/desactivar búsqueda web
ENABLE_GUI = True    # Preferir GUI si está disponible
```

### Configuración de Seguridad

```python
# En config.py
SECURE_MODE = True              # Activar modo seguro
ALLOWED_DOMAINS = ["wikipedia.org", "github.com"]  # Dominios permitidos para búsqueda
PRIVATE_MODE = False            # No guardar interacciones si es True
```

## Solución de Problemas

### Problema: Error al inicializar sistema de voz

**Síntoma**: Mensaje de error "No se pudo importar pyttsx3" o similar.

**Solución**:
```bash
pip install pyttsx3

# En Windows, puede necesitar:
pip install pywin32
```

### Problema: Error al inicializar embeddings

**Síntoma**: Mensaje "No se pudo inicializar modelo de embeddings".

**Solución**:
```bash
# Verificar que Ollama esté instalado y corriendo
ollama pull nomic-embed-text

# O configurar para usar otro modelo en config.py
DEFAULT_EMBEDDING_MODEL = "alternative"
```

### Problema: Interfaz gráfica no inicia

**Síntoma**: Error al intentar iniciar con `--gui` o cambio automático a CLI.

**Solución**:
```bash
# Reinstalar gradio
pip uninstall -y gradio
pip install gradio

# Verificar JavaScript en navegador
```

### Problema: Errores de plugin

**Síntoma**: Mensajes de error relacionados con plugins específicos.

**Solución**:
1. Verificar logs en `logs/jarvis_main.log`
2. Desactivar plugins problemáticos renombrándolos: `mv plugins/problematic_plugin.py plugins/problematic_plugin.py.disabled`
3. Reiniciar el sistema: `python main.py --debug`

## Políticas de Datos

El sistema Jarvis almacena los siguientes tipos de datos:

1. **Conversaciones**: Guardadas como archivos de texto en `memory/`
2. **Preferencias**: Configuración de usuario en `memory/configuracion.json`
3. **Caché web**: Búsquedas y contenido web en `memory/web_cache/`
4. **Embeddings**: Índices vectoriales en `embeddings/`

Para eliminar todos los datos:

```bash
# Eliminar todos los datos
rm -rf memory/*
rm -rf embeddings/*
```

Para exportar datos para respaldo:

```bash
# Exportar conversaciones
mkdir -p export
cp memory/*.txt export/

# Exportar configuración
cp memory/configuracion.json export/
```

## Actualizaciones Futuras

El sistema Jarvis está diseñado para facilitar las actualizaciones. Las futuras versiones mantendrán compatibilidad con esta estructura de datos y plugins. Se recomienda:

1. Siempre hacer un respaldo antes de actualizar
2. Revisar el registro de cambios para cada actualización
3. Seguir el procedimiento de actualización documentado

Para recibir notificaciones de actualizaciones:

```bash
# Configurar notificaciones por correo
python main.py --subscribe your@email.com
```

## Preguntas Frecuentes

**P: ¿Puedo usar Jarvis sin conexión a Internet?**  
R: Sí, pero con funcionalidad limitada. El sistema de memoria, voz y LLM local funcionarán, pero la búsqueda web no estará disponible.

**P: ¿Cómo cambio la voz predeterminada?**  
R: Usa el comando `/voces` para listar las disponibles y `/voz cambiar X` para seleccionar una.

**P: ¿Es posible añadir fuentes de conocimiento personalizadas?**  
R: Sí, coloca documentos en formato TXT o PDF en `memory/documents/` y reinicia el sistema.

**P: ¿Cómo puedo contribuir al proyecto?**  
R: Crea plugins personalizados y compártelos, o envía pull requests al repositorio principal.

## Soporte

Para obtener ayuda adicional:

- Documentación completa: [enlace]
- Canal de Discord: [enlace]
- Reportar bugs: [enlace al issue tracker]
- Email de soporte: support@jarvis-assistant.org


# Sistema de Plugins en JARVIS - Guía y Posibilidades de Expansión

## ¿Cómo funciona el sistema de plugins?

El sistema de plugins de JARVIS está diseñado como una arquitectura modular que permite extender las capacidades del asistente sin modificar su código base. Esta funcionalidad es crucial para mantener el núcleo limpio y a la vez permitir personalizaciones.

### Estructura principal:

1. **Clase base `Plugin`**: Define la interfaz que todos los plugins deben implementar.

2. **Gestor de plugins `PluginManager`**: Responsable de:
   - Descubrir plugins disponibles en el directorio plugins
   - Cargarlos según sus prioridades y dependencias
   - Inicializarlos correctamente
   - Gestionar comandos y puntos de extensión (hooks)

3. **Ciclo de vida de un plugin**:
   - **Descubrimiento**: El sistema busca archivos Python en la carpeta plugins
   - **Carga**: Instancia las clases derivadas de `Plugin`
   - **Inicialización**: Llama al método `initialize()` de cada plugin
   - **Ejecución**: Los plugins procesan mensajes o ejecutan comandos registrados
   - **Cierre**: Al finalizar, llama al método `shutdown()` para liberar recursos

### Puntos de extensión clave:

- **Comandos**: Funciones registradas para ser ejecutadas directamente
- **Procesamiento de mensajes**: Análisis y respuesta de mensajes del usuario
- **Hooks**: Puntos de extensión para modificar el comportamiento de otros componentes

## Plugins que podrías agregar a JARVIS

Además del plugin de voz que ya tienes implementado, aquí hay otros plugins útiles que podrías crear:

### 1. Plugin de Calendario y Recordatorios

```python
class CalendarPlugin(Plugin):
    """Plugin para gestión de calendario y recordatorios"""
    
    name = "calendar"
    description = "Gestiona eventos y recordatorios"
    version = "1.0.0"
    
    def initialize(self) -> bool:
        # Inicializar conexión con calendarios (Google Calendar, Outlook, etc.)
        # Cargar recordatorios pendientes
        return True
    
    def get_commands(self) -> Dict[str, Callable]:
        return {
            "recordar": self.cmd_add_reminder,
            "eventos": self.cmd_list_events,
            "agenda": self.cmd_show_agenda
        }
        
    def can_process_message(self, message: str) -> bool:
        patterns = [
            r"recuérdame", r"recordatorio", r"agenda", 
            r"calendario", r"evento", r"cita"
        ]
        return any(re.search(p, message.lower()) for p in patterns)
```

### 2. Plugin de Control de Domótica

```python
class HomeAutomationPlugin(Plugin):
    """Plugin para control de dispositivos IoT y domótica"""
    
    name = "smart_home"
    description = "Controla dispositivos del hogar inteligente"
    version = "1.0.0"
    
    def get_commands(self) -> Dict[str, Callable]:
        return {
            "luces": self.cmd_control_lights,
            "temperatura": self.cmd_control_thermostat,
            "dispositivos": self.cmd_list_devices
        }
        
    def can_process_message(self, message: str) -> bool:
        return any(kw in message.lower() for kw in [
            "luz", "luces", "encender", "apagar", "termostato", 
            "temperatura", "dispositivo"
        ])
```

### 3. Plugin de Gestión de Tareas y Proyectos

```python
class TaskManagerPlugin(Plugin):
    """Plugin para gestión de tareas y proyectos"""
    
    name = "tasks"
    description = "Gestiona tareas, proyectos y seguimiento de actividades"
    version = "1.0.0"
    
    def get_commands(self) -> Dict[str, Callable]:
        return {
            "tarea": self.cmd_add_task,
            "proyecto": self.cmd_manage_project,
            "pendientes": self.cmd_list_pending
        }
```

### 4. Plugin de Noticias y Clima

```python
class NewsWeatherPlugin(Plugin):
    """Plugin para obtener noticias y pronóstico del tiempo"""
    
    name = "news_weather"
    description = "Proporciona información de noticias y clima"
    version = "1.0.0"
    
    def initialize(self) -> bool:
        # Configurar APIs de noticias y clima
        self.news_api_key = self.config.get("news_api_key", "")
        self.weather_api_key = self.config.get("weather_api_key", "")
        return bool(self.news_api_key and self.weather_api_key)
    
    def get_commands(self) -> Dict[str, Callable]:
        return {
            "noticias": self.cmd_get_news,
            "clima": self.cmd_get_weather,
            "pronóstico": self.cmd_get_forecast
        }
```

### 5. Plugin de Música y Entretenimiento

```python
class MediaPlayerPlugin(Plugin):
    """Plugin para reproducción de música y contenido multimedia"""
    
    name = "media_player"
    description = "Controla la reproducción multimedia"
    version = "1.0.0"
    
    def get_commands(self) -> Dict[str, Callable]:
        return {
            "reproducir": self.cmd_play_music,
            "pausar": self.cmd_pause,
            "siguiente": self.cmd_next_track,
            "volumen": self.cmd_set_volume
        }
        
    # Este plugin podría integrarse con Spotify, YouTube Music, etc.
```

### 6. Plugin de Aprendizaje Personalizado

```python
class LearningPlugin(Plugin):
    """Plugin para aprendizaje y adaptación personalizada"""
    
    name = "learning"
    description = "Permite a JARVIS aprender preferencias y adaptar respuestas"
    
    def initialize(self) -> bool:
        # Inicializar base de datos de preferencias
        return True
        
    def on_response_generated(self, message: str, response: str, user_id: str = None) -> str:
        # Analizar respuestas y adaptarlas según preferencias aprendidas
        return self.adapt_response(response)
        
    def can_process_message(self, message: str) -> bool:
        return "aprende" in message.lower() or "recuerda que me gusta" in message.lower()
```

### 7. Plugin de Salud y Bienestar

```python
class HealthPlugin(Plugin):
    """Plugin para seguimiento de salud y bienestar"""
    
    name = "health"
    description = "Monitoriza y aconseja sobre hábitos saludables"
    
    def get_commands(self) -> Dict[str, Callable]:
        return {
            "agua": self.cmd_water_reminder,
            "ejercicio": self.cmd_exercise_tracking,
            "descanso": self.cmd_screen_break,
            "sueño": self.cmd_sleep_analytics
        }
```

### 8. Plugin de Traducciones

```python
class TranslationPlugin(Plugin):
    """Plugin para traducciones entre idiomas"""
    
    name = "translator"
    description = "Traduce texto entre diferentes idiomas"
    
    def initialize(self) -> bool:
        try:
            # Importar librería de traducción
            import googletrans
            self.translator = googletrans.Translator()
            return True
        except ImportError:
            logger.error("Librería de traducción no disponible")
            return False
            
    def get_commands(self) -> Dict[str, Callable]:
        return {
            "traducir": self.cmd_translate,
            "idiomas": self.cmd_list_languages
        }
        
    def cmd_translate(self, *args) -> str:
        """Traduce texto a otro idioma"""
        if len(args) < 2:
            return "Uso: traducir [idioma] [texto]"
            
        lang = args[0]
        text = " ".join(args[1:])
        
        try:
            result = self.translator.translate(text, dest=lang)
            return f"Traducción ({result.src} → {lang}):\n{result.text}"
        except Exception as e:
            return f"Error al traducir: {str(e)}"
```

## Recomendaciones para crear plugins efectivos

1. **Diseño modular**: Crea plugins que hagan una sola cosa bien.

2. **Gestión de dependencias**: Usa el sistema de dependencias para establecer el orden de carga necesario.

3. **Manejo de errores**: Implementa un manejo robusto de excepciones para evitar fallos en cascada.

4. **Documentación clara**: Incluye ayuda detallada sobre los comandos y funcionalidades.

5. **Configuración persistente**: Usa el sistema de configuración para guardar preferencias.

6. **Economía de recursos**: Libera adecuadamente recursos en `shutdown()`.

7. **Adaptabilidad**: Proporciona varios modos de interacción con el mismo plugin.

8. **Interoperabilidad**: Considera cómo tus plugins pueden interactuar entre sí usando el sistema de hooks.

El sistema de plugins de JARVIS es extremadamente versátil y permite una evolución continua del asistente según tus necesidades, sin tener que modificar el código central.



# Mejoras al Sistema Jarvis

## Refactorización y Nuevo Diseño

La refactorización del sistema Jarvis se centra en cinco áreas clave:

1. **Arquitectura modular basada en plugins**
2. **Mejora del motor web**
3. **Sistema de voz optimizado**
4. **Manejo robusto de errores y dependencias**
5. **Interfaces unificadas**

## 1. Sistema de Plugins

El nuevo sistema de plugins permite extender la funcionalidad de Jarvis de manera flexible:

- **Registro automático**: Los plugins se descubren y cargan automáticamente
- **Gestión de dependencias**: Resolución automática del orden de carga
- **Hooks**: Sistema de eventos para comunicación entre componentes
- **Punto de extensión unificado**: Facilita la adición de nuevas características

### Ejemplo: Plugin de Voz
```python
class VoicePlugin(Plugin):
    name = "voice"
    description = "Sistema de voz mejorado para Jarvis"
    version = "1.0.0"
    
    def initialize(self) -> bool:
        # Inicialización del plugin
        
    def get_commands(self) -> Dict[str, Callable]:
        return {
            "voz_activar": self.activar_voz,
            # Más comandos...
        }
```

## 2. Motor Web Refactorizado

El motor web ha sido dividido en componentes más manejables:

- **Cache**: Manejo eficiente de caché para contenido web
- **Extractores**: Sistema modular para extraer contenido por tipo de sitio
- **Utilidades**: Funciones auxiliares compartidas
- **Motor principal**: Coordinación de componentes

### Beneficios:
- **Mejor mantenibilidad**: Módulos especializados más fáciles de mantener
- **Rendimiento optimizado**: Mejor uso de caché y recursos
- **Extensibilidad**: Fácil adición de nuevos extractores para sitios específicos

## 3. Sistema Principal Mejorado

El archivo `main.py` implementa:

- **Inicialización ordenada** de componentes con manejo de dependencias
- **Fallbacks automáticos** cuando hay problemas con componentes
- **Sistema unificado** para CLI y GUI
- **Manejo centralizado** de mensajes y respuestas

```python
def inicializar(self) -> bool:
    # Inicialización ordenada de componentes
    if not self._inicializar_memoria():
        logger.critical("Error al inicializar sistema de memoria. Abortando.")
        return False
    
    self._inicializar_plugins()
    self._inicializar_llm()
    
    # Inicializar plugins
    if self.plugins:
        self.plugins.initialize_plugins()
```

## 4. Sistemas de Fallback

Se han implementado alternativas simplificadas para componentes críticos:

- **Memoria simplificada**: Versión básica sin embeddings para almacenar datos
- **Interfaces alternativas**: Cambio automático entre GUI y CLI según disponibilidad
- **Manejo de errores mejorado**: Registro detallado y recuperación de errores

## 5. Mejoras Adicionales

- **Sistema de logging mejorado**: Más información para diagnóstico
- **Configuración centralizada**: Preferencias del usuario gestionadas uniformemente
- **Documentación inline**: Mejor documentación del código
- **Tipado estático**: Uso de type hints para verificación de tipos

## Próximos Pasos

1. **Crear plugins adicionales para:**
   - Búsqueda web integrada como plugin
   - Integración de calendario y recordatorios
   - Tareas programadas y automatizaciones
   - Alertas y notificaciones personalizadas
   - Plugin de clima y noticias locales

2. **Mejorar la interfaz gráfica:**
   - Mejor integración con el sistema de plugins
   - Panel de estado de componentes en tiempo real
   - Configuración visual de plugins y preferencias
   - Temas visuales y personalización

3. **Optimización de rendimiento:**
   - Carga diferida de plugins no esenciales
   - Mejor gestión de memoria para dispositivos con recursos limitados
   - Alternativas para componentes pesados (LLM local/remoto)
   - Caché inteligente para respuestas frecuentes

4. **Seguridad y privacidad:**
   - Cifrado de datos sensibles en la memoria
   - Controles de acceso a funcionalidades críticas
   - Modo privado con registro limitado
   - Opciones para controlar el uso de servicios externos

5. **Mejoras de experiencia de usuario:**
   - Personalidad adaptativa basada en preferencias
   - Sistema de feedback para mejorar respuestas
   - Historial de interacciones con búsqueda avanzada
   - Completado predictivo de comandos

## Guía de Implementación

### 1. Actualización del Sistema Existente

Para actualizar una instalación existente de Jarvis:

1. **Respaldar configuración actual:**
   ```bash
   cp -r memory memory_backup
   ```

2. **Instalar los nuevos módulos:**
   ```bash
   # Instalar dependencias
   pip install -r requirements.txt
   
   # Crear estructura de directorios
   mkdir -p plugins
   ```

3. **Copiar los archivos refactorizados:**
   - Reemplazar `main.py`
   - Crear la estructura de directorios para `chatbot/web/`
   - Copiar los plugins a la carpeta `plugins/`

4. **Verificar la configuración:**
   ```bash
   python main.py --version
   ```

### 2. Creación de Nuevos Plugins

Para desarrollar plugins personalizados:

1. **Crear archivo de plugin en la carpeta `plugins/`:**
   ```python
   """
   mi_plugin.py - Plugin personalizado para Jarvis
   """
   from plugins import Plugin
   
   class MiPlugin(Plugin):
       name = "mi_plugin"
       description = "Plugin personalizado para Jarvis"
       version = "1.0.0"
       author = "Tu Nombre"
       
       def initialize(self) -> bool:
           # Código de inicialización
           return True
           
       def get_commands(self) -> Dict[str, Callable]:
           return {
               "mi_comando": self.mi_funcion
           }
           
       def mi_funcion(self, param=None):
           # Implementación del comando
           return "Resultado de mi_comando"
   ```

2. **Registrar función de carga:**
   ```python
   def get_plugin_class():
       """Devuelve la clase principal del plugin"""
       return MiPlugin
   ```

3. **Reiniciar Jarvis** para que detecte el nuevo plugin

### 3. Actualización de Documentación

Para mantener actualizada la documentación:

1. **Actualizar el archivo README.md** con las nuevas funcionalidades
2. **Documentar los comandos disponibles** en cada plugin
3. **Crear un manual del usuario** con ejemplos de uso
4. **Mantener la sección de preguntas frecuentes** con problemas comunes

## Conclusión

Las mejoras implementadas transforman a Jarvis en una plataforma más extensible, robusta y fácil de mantener. El sistema de plugins permite una personalización sin precedentes, mientras que la arquitectura modular garantiza que el código pueda crecer de manera sostenible.

La separación clara de responsabilidades entre los diferentes componentes facilita la colaboración entre desarrolladores y permite que cada parte del sistema evolucione a su propio ritmo sin afectar al resto.

Estas mejoras sientan las bases para que Jarvis pueda convertirse en un asistente verdaderamente personalizado y adaptado a las necesidades específicas de cada usuario.
