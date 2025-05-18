class AnalizadorTexto:
    """Herramientas para analizar y extraer información de textos"""
    
    @staticmethod
    def extraer_entidades(texto):
        """
        Extrae entidades como nombres, lugares, organizaciones
        usando expresiones regulares simples
        """
        entidades = {
            "personas": [],
            "organizaciones": [],
            "lugares": [],
            "fechas": [],
            "cantidades": []
        }
        
        # Patrones simples (para un análisis más sofisticado se necesitaría NLP)
        import re
        
        # Buscar posibles nombres propios (palabras que empiezan con mayúscula)
        nombres = re.findall(r'\b[A-Z][a-zñáéíóúü]+ [A-Z][a-zñáéíóúü]+\b', texto)
        entidades["personas"] = list(set(nombres))
        
        # Buscar organizaciones (palabras con mayúsculas seguidas, o terminadas en Inc., SA, etc.)
        orgs = re.findall(r'\b[A-Z][a-zA-Z\s&]+(Inc\.|SA|S\.A\.|S\.L\.|Corp\.|Corporation)\b', texto)
        entidades["organizaciones"] = list(set(orgs))
        
        # Buscar posibles lugares (después de "en", "desde", etc.)
        lugares_pattern = r'(?:en|desde|hacia|en|de|a) ([A-Z][a-zñáéíóúü]+(?:\s[A-Z][a-zñáéíóúü]+)*)'
        lugares = re.findall(lugares_pattern, texto)
        entidades["lugares"] = list(set(lugares))
        
        # Buscar fechas
        fechas_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # 01/01/2023
            r'\b\d{1,2} de [a-zñáéíóúü]+ (?:de|del) \d{2,4}\b'  # 1 de enero de 2023
        ]
        
        fechas = []
        for pattern in fechas_patterns:
            fechas.extend(re.findall(pattern, texto))
        entidades["fechas"] = list(set(fechas))
        
        # Buscar cantidades (números con unidades)
        cantidades = re.findall(r'\b\d+(?:,\d+)? (?:euros|dólares|kg|kilogramos|metros|km|años|horas)\b', texto)
        entidades["cantidades"] = list(set(cantidades))
        
        return entidades
    
    @staticmethod
    def resumir_texto(texto, max_oraciones=5):
        """
        Crea un resumen simple extrayendo las oraciones más relevantes
        basado en frecuencia de palabras
        """
        import re
        
        # Dividir en oraciones
        oraciones = re.split(r'(?<=[.!?])\s+', texto)
        if len(oraciones) <= max_oraciones:
            return texto
            
        # Calcular frecuencia de palabras
        palabras = re.findall(r'\b\w{3,}\b', texto.lower())
        frecuencias = {}
        for palabra in palabras:
            frecuencias[palabra] = frecuencias.get(palabra, 0) + 1
            
        # Excluir palabras comunes
        palabras_comunes = {'que', 'con', 'para', 'por', 'como', 'pero', 'una', 'los', 'las', 'del', 'este', 'esta'}
        for palabra in palabras_comunes:
            if palabra in frecuencias:
                del frecuencias[palabra]
                
        # Calcular relevancia de cada oración
        puntuaciones = []
        for oracion in oraciones:
            puntuacion = sum(frecuencias.get(palabra.lower(), 0) 
                            for palabra in re.findall(r'\b\w{3,}\b', oracion))
            puntuaciones.append((puntuacion, oracion))
            
        # Ordenar por relevancia y tomar las mejores
        mejores_oraciones = sorted(puntuaciones, reverse=True)[:max_oraciones]
        
        # Reordenar según posición original
        orden_original = []
        for _, oracion in mejores_oraciones:
            indice = oraciones.index(oracion)
            orden_original.append((indice, oracion))
            
        resumen = " ".join(oracion for _, oracion in sorted(orden_original))
        return resumen