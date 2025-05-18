import pyttsx3
import re
import threading
import time

class SistemaVoz:
    def __init__(self, velocidad=145, volumen=0.85, voz_index=None):
        """
        Inicializa el sistema de voz mejorado con pyttsx3
        Args:
            velocidad: Velocidad del habla (130-160 es un rango natural)
            volumen: Volumen (0.0 a 1.0)
            voz_index: Índice específico de voz a usar
        """
        self.engine = pyttsx3.init()
        self.disponible = True
        self.lock = threading.Lock()
        self.is_speaking = False
        self._configurar_voz(velocidad, volumen, voz_index)
        print("✅ Sistema de voz pyttsx3 inicializado")
        
    def _configurar_voz(self, velocidad, volumen, voz_index):
        """Configura los parámetros de la voz"""
        # Establecer velocidad y volumen
        self.engine.setProperty('rate', velocidad)
        self.engine.setProperty('volume', volumen)
        
        # Obtener voces disponibles
        voces = self.engine.getProperty('voices')
        if not voces:
            print("⚠️ No se encontraron voces en el sistema")
            return
            
        # Buscar voces en español primero
        voces_es_mx = [v for v in voces if any(lang in v.id.lower() for lang in ['mexican', 'es-mx', 'spanish-mexico'])]
        voces_es = [v for v in voces if any(lang in v.id.lower() for lang in ['spanish', 'es', 'esp'])]
        
        # Decidir qué voz usar
        if voz_index is not None and 0 <= voz_index < len(voces):
            # Usar voz específica por índice
            self.engine.setProperty('voice', voces[voz_index].id)
            print(f"📢 Usando voz: {voces[voz_index].name}")
        elif voces_es_mx:  # Primero intenta con español mexicano
            self.engine.setProperty('voice', voces_es_mx[0].id)
            print(f"📢 Usando voz en español mexicano: {voces_es_mx[0].name}")
        elif voces_es:  # Luego cualquier español
            self.engine.setProperty('voice', voces_es[0].id)
            print(f"📢 Usando voz en español: {voces_es[0].name}")
        else:
            # Usar la primera voz disponible
            self.engine.setProperty('voice', voces[0].id)
            print(f"📢 Usando voz predeterminada: {voces[0].name}")
            
    def hablar(self, texto, async_mode=True):
        """
        Convierte texto a voz y lo reproduce
        Args:
            texto: El texto a convertir en voz
            async_mode: Si es True, habla en un hilo separado (no bloquea)
        """
        if not self.disponible:
            return False
            
        try:
            # Intentar adquirir el lock de forma no bloqueante
            if not self.lock.acquire(blocking=False):
                print("Otra instancia de habla está en curso, saltando esta solicitud")
                return False
                
            try:
                # Limpia el texto de marcas o caracteres especiales
                texto_limpio = self.limpiar_texto(texto)
                
                if async_mode:
                    # Liberar el lock antes de iniciar el hilo para evitar deadlocks
                    self.lock.release()
                    
                    # Hablar en un hilo separado
                    thread = threading.Thread(target=self._hablar_seguro, args=(texto_limpio,))
                    thread.daemon = True
                    thread.start()
                    return True
                else:
                    # Modo síncrono (bloqueante)
                    try:
                        resultado = self._hablar_seguro(texto_limpio)
                    finally:
                        self.lock.release()
                    return resultado
            except:
                self.lock.release()
                raise
        except Exception as e:
            print(f"Error al hablar: {e}")
            return False
            
    def _hablar_seguro(self, texto):
        """Método interno para hablar con motor separado por instancia"""
        if not texto:
            return False
            
        # Dividir texto largo en fragmentos manejables
        partes = self._dividir_texto(texto)
        
        try:
            # Crear un nuevo motor cada vez
            engine_temp = pyttsx3.init()
            engine_temp.setProperty('rate', self.engine.getProperty('rate'))
            engine_temp.setProperty('volume', self.engine.getProperty('volume'))
            engine_temp.setProperty('voice', self.engine.getProperty('voice'))
            
            # Acumular todas las partes antes de llamar a runAndWait
            for parte in partes:
                if parte.strip():
                    engine_temp.say(parte)
                    
            # Ejecutar una sola vez para todas las partes acumuladas
            engine_temp.runAndWait()
            
            # Limpiar recursos
            del engine_temp
            return True
            
        except Exception as e:
            print(f"Error en _hablar_seguro: {e}")
            return False
            
    def _dividir_texto(self, texto, max_length=300):
        """Divide un texto largo en fragmentos manejables por puntuación"""
        if not texto or len(texto) <= max_length:
            return [texto]
            
        # Intentar dividir por puntos
        fragmentos = re.split(r'(?<=[.!?])\s+', texto)
        resultado = []
        acumulado = ""
        
        for fragmento in fragmentos:
            if len(acumulado) + len(fragmento) <= max_length:
                acumulado += fragmento + " "
            else:
                if acumulado:
                    resultado.append(acumulado.strip())
                acumulado = fragmento + " "
                
        if acumulado:  # Añadir el último fragmento
            resultado.append(acumulado.strip())
            
        return resultado
            
    def limpiar_texto(self, texto):
        """Limpia el texto de marcas de formato o códigos especiales"""
        if not texto:
            return ""
            
        # Eliminar códigos de formato rich o markdown
        texto = re.sub(r'\[.*?\]', '', texto)  # Elimina [texto] de rich
        texto = re.sub(r'\*\*(.*?)\*\*', r'\1', texto)  # Elimina **negrita**
        texto = re.sub(r'\*(.*?)\*', r'\1', texto)  # Elimina *cursiva*
        texto = re.sub(r'`(.*?)`', r'\1', texto)  # Elimina `código`
        
        # Mejorar la pronunciación
        texto = texto.replace("Jarvis", "Járvis")  # Mejor pronunciación de Jarvis
        
        return texto
        
    def detener(self):
        """Detiene la reproducción de voz"""
        if self.disponible and self.is_speaking:
            try:
                self.engine.stop()
            except:
                pass
            
    def cambiar_velocidad(self, nueva_velocidad):
        """Cambia la velocidad de habla"""
        if self.disponible and 50 <= nueva_velocidad <= 300:
            self.engine.setProperty('rate', nueva_velocidad)
            return True
        return False
        
    def cambiar_volumen(self, nuevo_volumen):
        """Cambia el volumen de habla (0.0 a 1.0)"""
        if self.disponible and 0 <= nuevo_volumen <= 1:
            self.engine.setProperty('volume', nuevo_volumen)
            return True
        return False
        
    def listar_voces(self):
        """Muestra y devuelve las voces disponibles en el sistema"""
        if not self.disponible:
            return []
            
        voces = self.engine.getProperty('voices')
        print(f"🎤 Voces disponibles ({len(voces)}):")
        
        for i, voz in enumerate(voces):
            # Intentar determinar idioma
            idioma = "Desconocido"
            if hasattr(voz, 'languages') and voz.languages:
                idioma = voz.languages[0]
            elif "spanish" in voz.id.lower():
                idioma = "Español"
            elif "english" in voz.id.lower():
                idioma = "Inglés"
                
            genero = getattr(voz, 'gender', 'Desconocido')
            print(f"  {i}. ID: {voz.id}")
            print(f"     Nombre: {voz.name}")
            print(f"     Idioma: {idioma}")
            print(f"     Género: {genero}")
        
        return voces
        
    def cambiar_voz(self, indice):
        """Cambia la voz al índice especificado"""
        if not self.disponible:
            return False
            
        voces = self.engine.getProperty('voices')
        if 0 <= indice < len(voces):
            self.engine.setProperty('voice', voces[indice].id)
            print(f"🎤 Voz cambiada a: {voces[indice].name}")
            return True
        else:
            print("❌ Índice de voz no válido")
            return False