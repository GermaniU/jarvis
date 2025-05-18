JARVIS - Asistente IA Minimalista
JARVIS es un asistente de IA minimalista basado en modelos LLM (Large Language Models) que ofrece una implementación liviana y flexible, ideal para sistemas con recursos limitados o para quienes buscan una solución simple pero potente.
🌟 Características

Implementación minimalista: Diseñado para ser ligero y eficiente
Interfaz dual: Modo consola y modo gráfico (GUI opcional)
Integración web: Capacidad de búsqueda web (opcional)
Motor de chat modular: Basado en el framework LlamaIndex
Fácil de personalizar: Arquitectura modular para extender funcionalidades

🛠️ Requisitos

Python 3.8+
Ollama (para modelos locales)
Dependencias listadas en requirements.txt

📋 Dependencias
llama-index==0.9.4
llama-index-embeddings-huggingface==0.2.3
llama-index-llms-ollama==0.1.1
llama-index-embeddings-ollama==0.1.1
bs4==0.0.2
rich==13.5.3
gradio==3.50.2
requests==2.31.0
🚀 Instalación

Clonar el repositorio:
git clone https://github.com/su-usuario/jarvis.git
cd jarvis

Crear y activar un entorno virtual:
python -m venv .venv
source .venv/Scripts/activate  # En Windows con Git Bash
# O
.\.venv\Scripts\Activate.ps1   # En Windows con PowerShell

Instalar las dependencias:
pip install -r requirements.txt

Configurar Ollama (si se usa localmente):
ollama pull deepseek-coder  # O cualquier otro modelo compatible


🎮 Uso
Modo Consola
python main.py
Modo GUI
python main.py --gui
# o
python main.py -g
📁 Estructura del Proyecto
jarvis/
├── .venv/                 # Entorno virtual (no incluido en git)
├── chatbot/               # Módulo principal
│   ├── llm_wrapper.py     # Wrapper para el motor LLM
│   ├── web.py             # Implementación de búsqueda web
│   └── interfaz.py        # Interfaz de consola
├── gui.py                 # Interfaz gráfica (opcional)
├── main.py                # Punto de entrada principal
├── requirements.txt       # Dependencias del proyecto
└── README.md              # Esta documentación
🧩 Personalización
Cambiar modelo LLM
Edite el archivo chatbot/llm_wrapper.py para configurar un modelo diferente.
Extender funcionalidades
La arquitectura modular permite agregar nuevas capacidades creando nuevos módulos en el directorio chatbot/.
📝 Logging
JARVIS incluye un sistema de registro que guarda información en:

Consola (stdout)
Archivo jarvis_main.log

🤝 Contribuciones
Las contribuciones son bienvenidas. Por favor, abra un issue primero para discutir lo que le gustaría cambiar.
📜 Licencia
MIT

Desarrollado con ❤️ para simplificar la interacción con modelos de IA.
