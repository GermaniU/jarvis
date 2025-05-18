# JARVIS: Asistente Virtual Inteligente

![JARVIS](https://img.shields.io/badge/JARVIS-v1.0-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![LLM](https://img.shields.io/badge/LLM-Ollama-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

JARVIS es un asistente virtual de código abierto diseñado para interactuar con modelos de lenguaje locales a través de Ollama, incorporar memoria persistente, realizar búsquedas web privadas y analizar contenido en línea.

## 🌟 Características principales

### 💬 Interfaz conversacional
- **Chat natural**: Interactúa de forma conversacional con modelos LLM locales
- **Interfaz dual**: Modo consola y GUI basada en Gradio
- **Síntesis de voz**: Responde verbalmente mediante TTS incorporado

### 🧠 Sistema de memoria
- **Memoria persistente**: Almacena y recupera conversaciones pasadas
- **Embeddings vectoriales**: Búsqueda semántica de recuerdos relevantes
- **Contexto adaptativo**: Aprovecha conversaciones anteriores para mejorar respuestas

### 🔍 Capacidades web
- **Búsqueda privada**: Busca información en la web sin depender de APIs propietarias
- **Análisis de páginas**: Extrae contenido estructurado de sitios web
- **Extracción inteligente**: Procesamiento específico por tipo de sitio (GitHub, Stack Overflow, Wikipedia, etc.)
- **Caché local**: Almacena resultados para reducir tráfico y mejorar velocidad

### 🛠️ Características avanzadas
- **Análisis de datos**: Extracción de tablas, datos comerciales, información de contacto
- **Estadísticas de uso**: Seguimiento de búsquedas y dominios frecuentes
- **Personalización**: Preferencias de búsqueda y dominios favoritos/bloqueados

## 📋 Requisitos

- Python 3.11 o superior
- [Ollama](https://ollama.ai/) instalado y configurado
- Paquetes requeridos:
  - llama-index (0.8.34)
  - langchain (compatible con llama-index)
  - gradio (3.50.2+)
  - rich, requests, beautifulsoup4

## 🚀 Instalación

1. Clone este repositorio:
   ```bash
   git clone https://github.com/tuusuario/jarvis.git
   cd jarvis
   ```

2. Cree un entorno virtual:
   ```bash
   python -m venv .venv
   ```

3. Active el entorno:
   ```bash
   # En Windows
   .venv\Scripts\activate
   
   # En Linux/macOS
   source .venv/bin/activate
   ```

4. Instale las dependencias:
   ```bash
  pip install -r requirements.txt

   ```
   O manualmente:
   ```bash
   pip install langchain>=0.0.293
   pip install llama-index==0.8.34
   pip install gradio==3.50.2 rich==13.6.0 requests==2.32.3 beautifulsoup4==4.12.2
   pip install python-dotenv
   ```

## 🎮 Uso

### Modo interfaz gráfica (GUI)
```bash
python main.py -g
```

### Modo consola
```bash
python main.py
```

## 🖥️ Interfaz gráfica

La interfaz gráfica está organizada en pestañas:

### Pestaña "Chat Principal"
- **Conversación**: Interactúa naturalmente con JARVIS
- **Comandos especiales**: 
  - `buscar [término]`: Busca información en la web
  - `analizar [url]`: Analiza una página web en detalle

### Pestaña "Herramientas Web"
- **Búsqueda web**: Búsqueda manual de información
- **Análisis de páginas**: Extracción de información de URLs
- **Estadísticas**: Visualiza el uso del motor web
- **Historial**: Consulta búsquedas recientes

## 🧩 Estructura del proyecto

```
jarvis/
├── main.py             # Punto de entrada principal
├── gui.py              # Interfaz gráfica basada en Gradio
├── chatbot/
│   ├── interfaz.py     # Interfaz de consola
│   ├── llm_wrapper.py  # Wrapper para modelos LLM
│   ├── memoria.py      # Sistema de gestión de memoria
│   ├── web.py          # Motor de búsqueda web privado
│   └── voz.py          # Sistema de síntesis de voz
├── data/               # Directorio para documentos de conocimiento
├── memory/             # Directorio para almacenamiento de memoria
│   └── web_cache/      # Caché de búsquedas web
└── embeddings/         # Índices vectoriales persistentes
```

## 🔧 Componentes principales

### main.py
Punto de entrada que inicializa los componentes y lanza la interfaz.

### memoria.py
Sistema de memoria que utiliza embeddings vectoriales para:
- Guardar recuerdos de conversaciones
- Recuperar contexto relevante para preguntas nuevas
- Persistir índices para uso futuro

### web.py
Motor web con funcionalidades avanzadas:
- Búsqueda privada sin depender de APIs propietarias
- Extracción inteligente de contenido por tipo de sitio
- Análisis detallado de páginas web
- Caché local para mejorar rendimiento

### `llm_wrapper.py`
Interfaz simplificada para comunicación con modelos LLM locales:
- Integración con Ollama
- Gestión de contexto para mejorar respuestas
- Carga de documentos de conocimiento local

## 🛠️ Personalización

### Modelos LLM
Por defecto, JARVIS utiliza `deepseek-r1:14b` a través de Ollama. Puedes modificar el modelo en llm_wrapper.py.

### Embeddings
Los embeddings utilizan Ollama con el modelo `nomic-embed-text`. Puedes cambiarlo en memoria.py.

### Preferencias web
El motor web almacena preferencias como dominios favoritos/bloqueados en `memory/web_cache/preferences.json`.

## 🔒 Privacidad

JARVIS está diseñado con la privacidad en mente:
- Ejecuta modelos LLM localmente sin enviar datos a servicios externos
- El motor web proporciona resultados sin depender de APIs comerciales
- Todos los datos se almacenan localmente en tu sistema

## ⚙️ Características técnicas avanzadas

### Motor web
- **Extracción específica por sitio**: Lógica especializada para GitHub, Stack Overflow, Wikipedia, YouTube, Twitter, Reddit, Amazon y Medium
- **Análisis de páginas**: Extrae información estructurada como tablas, precios, emails y datos de contacto
- **Mitigación anti-bloqueo**: Rotación de User-Agent y manejo de redireccionamientos
- **Aprendizaje**: Recolecta estadísticas sobre búsquedas y dominios para mejorar resultados futuros

### Sistema de memoria
- **Embeddings vectoriales**: Convierte recuerdos en vectores para búsqueda semántica
- **Persistencia**: Guarda índices vectoriales para uso entre sesiones
- **Contexto adaptativo**: Recupera información relevante basada en la consulta actual

### Integración LLM
- **Ollama local**: Integración nativa con modelos ejecutados localmente
- **Manejo de contexto**: Formatea prompts con el contexto relevante obtenido de la memoria
- **Formato flexible**: Procesa varios formatos de respuesta para compatibilidad con diferentes modelos

## 📝 Próximas funcionalidades

- [ ] Soporte para múltiples modelos LLM
- [ ] Integración con bases de datos locales
- [ ] API REST para integración con otros sistemas
- [ ] Extensión del motor web con fuentes adicionales
- [ ] Reconocimiento de voz para interfaz manos libres

## 📄 Licencia

Este proyecto está licenciado bajo MIT License - vea el archivo LICENSE para más detalles.

## 🙏 Agradecimientos

- [llama-index](https://github.com/jerryjliu/llama_index) por las capacidades de indexación y recuperación
- [Ollama](https://ollama.ai/) por proporcionar una forma sencilla de ejecutar LLMs localmente
- [Gradio](https://www.gradio.app/) por la interfaz web interactiva
- Todos los contribuyentes de código abierto que hacen posible proyectos como este

---

**JARVIS** - Tu asistente virtual personal, privado y potente. ¡Disfruta conversando, aprendiendo y explorando!



### 1. Mejoras visuales y de usabilidad

- **Diseño más moderno:** Interfaz completamente rediseñada con mejor organización visual y mayor espacio.
- **Temas mejorados:** Sistema de temas oscuro/claro con transiciones suaves.
- **Diseño responsivo:** Mejor adaptación a diferentes tamaños de pantalla.
- **Indicadores visuales:** Estados del sistema claramente visibles en todo momento.

### 2. Nuevas funcionalidades

- **Sistema de configuración completo:** Panel dedicado para personalizar todos los aspectos del asistente.
- **Exportación de conversaciones:** Exporta chats a diferentes formatos (Markdown, TXT, JSON).
- **Guardado automático:** Sistema para guardar conversaciones por inactividad.
- **Comandos rápidos:** Acceso con un clic a las funciones más comunes.
- **Mejor visualización del proceso de pensamiento:** Opción para ver cómo "piensa" JARVIS.
- **Personalización de fuente:** Ajustes de tamaño de texto para mejor legibilidad.

### 3. Mejoras en el motor web

- **Búsquedas mejoradas:** Resultados más relevantes y formateo más legible.
- **Análisis web enriquecido:** Mayor detalle al analizar páginas web.
- **Configuración de fuentes preferidas/bloqueadas:** Control sobre qué sitios utilizar.

### 4. Mejoras técnicas

- **Estructura de código modular:** Mejor organización interna para facilitar el mantenimiento.
- **Gestión de errores mejorada:** Sistema robusto que maneja fallos de manera elegante.
- **Sistema de logging avanzado:** Mejor registro de actividades y errores.
- **Configuración persistente:** Guarda preferencias entre sesiones.
- **Manejo de inactividad:** Sistema que detecta períodos sin uso.

### 5. Experiencia de usuario mejorada

- **Mensajes de bienvenida más informativos:** Mejor introducción al sistema.
- **Indicadores de estado claros:** El usuario siempre sabe qué está pasando.
- **Mensajes de error más amigables:** Explicaciones claras cuando algo falla.
- **Información contextual:** Tooltips y ayudas para entender las funciones.
