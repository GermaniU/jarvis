@echo off
call .venv\Scripts\activate
pip install langchain>=0.0.293
pip install llama-index==0.8.34
pip install gradio==3.50.2 rich==13.6.0 requests==2.32.3 beautifulsoup4==4.12.2
pip install python-dotenv
echo Verificando instalacion...
python -c "import llama_index; import langchain; print('llama-index: ' + llama_index.__version__ + ', langchain: ' + langchain.__version__)"
echo Instalación completa!
pause
