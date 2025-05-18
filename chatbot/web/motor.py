"""
Motor principal de búsqueda web con enfoque en privacidad
"""
import logging
import random
import re
import time
import requests
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
import hashlib
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from urllib.parse import urlparse

from .cache import CacheManager
from .utils import extraer_dominio, extraer_dominio_completo, normalizar_url, es_url_valida
from .extractores import get_extractor, SelectorExtractor

# Configurar logging
logger = logging.getLogger("web.motor")

class MotorWebPrivado:
    def __init__(self, cache_dir: str = "memory/web_cache", max_retry: int = 3):
        """
        Inicializa el motor de búsqueda web con enfoque en privacidad
        
        Args:
            cache_dir: Directorio para almacenar la caché de búsquedas
            max_retry: Número máximo de reintentos en caso de error
        """
        self.cache_dir = cache_dir
        self.max_retry = max_retry
        os.makedirs(cache_dir, exist_ok=True)
        
        # User agent por defecto
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        self.headers = {"User-Agent": self.user_agent}
        
        # Inicializar caché
        self.cache_manager = CacheManager(cache_dir)
        
        # Cargar preferencias
        self.preferences = self._load_preferences()
        logger.info(f"Motor web inicializado con caché en {cache_dir}")
        
    def _load_preferences(self) -> Dict[str, Any]:
        """
        Carga preferencias del usuario para la búsqueda
        
        Returns:
            Diccionario con las preferencias
        """
        prefs_file = os.path.join(self.cache_dir, "preferences.json")
        if os.path.exists(prefs_file):
            try:
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                    logger.info(f"Preferencias web cargadas: {len(prefs)} configuraciones")
                    return prefs
            except Exception as e:
                logger.error(f"Error al cargar preferencias: {e}")
                
        # Valores por defecto
        default_prefs = {
            "banned_domains": [],
            "preferred_domains": [],
            "max_results": 5,
            "search_engine": "duckduckgo",  # Más privado por defecto
            "cache_ttl": 86400,  # 24 horas en segundos
            "safe_search": True,  # Búsqueda segura activada por defecto
            "user_agents": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 Safari/537.36"
            ]
        }
        return default_prefs
        
    def _save_preferences(self) -> bool:
        """
        Guarda preferencias del usuario
        
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        try:
            prefs_file = os.path.join(self.cache_dir, "preferences.json")
            with open(prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, indent=2)
            logger.info("Preferencias web guardadas")
            return True
        except Exception as e:
            logger.error(f"Error al guardar preferencias: {e}")
            return False
            
    def actualizar_preferencia(self, clave: str, valor: Any) -> bool:
        """
        Actualiza una preferencia específica del usuario
        
        Args:
            clave: Nombre de la preferencia
            valor: Valor de la preferencia
            
        Returns:
            True si se actualizó correctamente, False en caso contrario
        """
        if clave in self.preferences:
            old_value = self.preferences[clave]
            self.preferences[clave] = valor
            success = self._save_preferences()
            if success:
                logger.info(f"Preferencia actualizada: {clave} = {valor} (anterior: {old_value})")
            return success
        
        logger.warning(f"Intento de actualizar preferencia inexistente: {clave}")
        return False
        
    def agregar_dominio_preferido(self, dominio: str) -> bool:
        """
        Agrega un dominio a la lista de preferidos
        
        Args:
            dominio: Dominio a agregar
            
        Returns:
            True si se agregó correctamente, False en caso contrario
        """
        if dominio not in self.preferences["preferred_domains"]:
            self.preferences["preferred_domains"].append(dominio)
            success = self._save_preferences()
            if success:
                logger.info(f"Dominio preferido agregado: {dominio}")
            return success
            
        logger.info(f"El dominio {dominio} ya está en la lista de preferidos")
        return True
        
    def bloquear_dominio(self, dominio: str) -> bool:
        """
        Bloquea un dominio para que no aparezca en resultados
        
        Args:
            dominio: Dominio a bloquear
            
        Returns:
            True si se bloqueó correctamente, False en caso contrario
        """
        if dominio not in self.preferences["banned_domains"]:
            self.preferences["banned_domains"].append(dominio)
            success = self._save_preferences()
            if success:
                logger.info(f"Dominio bloqueado: {dominio}")
            return success
            
        logger.info(f"El dominio {dominio} ya está bloqueado")
        return True
    
    def desbloquear_dominio(self, dominio: str) -> bool:
        """
        Elimina un dominio de la lista de bloqueados
        
        Args:
            dominio: Dominio a desbloquear
            
        Returns:
            True si se desbloqueó correctamente, False en caso contrario
        """
        if dominio in self.preferences["banned_domains"]:
            self.preferences["banned_domains"].remove(dominio)
            success = self._save_preferences()
            if success:
                logger.info(f"Dominio desbloqueado: {dominio}")
            return success
            
        logger.info(f"El dominio {dominio} no estaba bloqueado")
        return True
    
    def buscar_informacion(self, consulta: str, forzar_recarga: bool = False) -> List[Dict[str, Any]]:
        """
        Realiza una búsqueda web respetando la privacidad
        
        Args:
            consulta: La consulta a buscar
            forzar_recarga: Si True, ignora la caché
        
        Returns:
            Lista de resultados de búsqueda
        """
        # Verificar caché primero si no se fuerza recarga
        if not forzar_recarga:
            resultados_cache = self.cache_manager.get(consulta)
            if resultados_cache:
                logger.info(f"📚 Usando datos en caché para: '{consulta}'")
                return resultados_cache
        
        # Si llegamos aquí, debemos hacer una búsqueda nueva
        try:
            resultados = []
            # Usar DuckDuckGo por ser más privado
            consulta_encoded = requests.utils.quote(consulta)
            safe_search = "1" if self.preferences.get("safe_search", True) else "-1"
            url = f"https://html.duckduckgo.com/html/?q={consulta_encoded}&kp={safe_search}"
            
            # Seleccionar un User-Agent aleatorio
            user_agent = random.choice(self.preferences.get("user_agents", [self.user_agent]))
            headers = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache"
            }
            
            logger.info(f"🔎 Realizando búsqueda: '{consulta}'")
            
            # Realizar petición con reintentos
            response = None
            for intento in range(self.max_retry):
                try:
                    response = requests.get(url, headers=headers, timeout=15)
                    if response.status_code == 200:
                        break
                    logger.warning(f"Intento {intento+1}/{self.max_retry} falló con código {response.status_code}")
                    time.sleep(1)  # Esperar un segundo entre intentos
                except Exception as e:
                    logger.error(f"Error en intento {intento+1}/{self.max_retry}: {e}")
                    if intento == self.max_retry - 1:
                        raise
                    time.sleep(1)
            
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for result in soup.select('.result'):
                    titulo = result.select_one('.result__title')
                    snippet = result.select_one('.result__snippet')
                    url_elem = result.select_one('.result__url')
                    
                    if not all([titulo, snippet, url_elem]):
                        continue
                        
                    url_text = url_elem.get_text().strip()
                    
                    # Verificar si el dominio está bloqueado
                    if any(banned in url_text for banned in self.preferences["banned_domains"]):
                        logger.debug(f"Dominio bloqueado: {url_text}")
                        continue
                        
                    resultados.append({
                        "titulo": titulo.get_text().strip(),
                        "snippet": snippet.get_text().strip(),
                        "url": url_text,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Limitar resultados
                    if len(resultados) >= self.preferences["max_results"]:
                        break
                
                # Priorizar dominios preferidos
                if self.preferences["preferred_domains"]:
                    # Mover resultados preferidos al inicio
                    preferred = [r for r in resultados if 
                                any(domain in r["url"] for domain in self.preferences["preferred_domains"])]
                    others = [r for r in resultados if 
                             not any(domain in r["url"] for domain in self.preferences["preferred_domains"])]
                    resultados = preferred + others
                
                # Guardar en caché
                self.cache_manager.set(consulta, resultados)
                    
                # Aprender de esta búsqueda (guardar metadatos)
                self._aprender_de_busqueda(consulta, resultados)
                
                logger.info(f"✅ Búsqueda completada: {len(resultados)} resultados")
                    
            return resultados
        except Exception as e:
            logger.error(f"Error en búsqueda web: {e}")
            return []
    
    def _aprender_de_busqueda(self, consulta: str, resultados: List[Dict[str, Any]]) -> None:
        """
        Aprende de las búsquedas para mejorar futuras interacciones
        
        Args:
            consulta: Texto de la consulta realizada
            resultados: Lista de resultados obtenidos
        """
        try:
            hist_file = os.path.join(self.cache_dir, "search_history.jsonl")
            
            # Extraer posibles temas de interés de la consulta
            palabras_clave = re.findall(r'\b\w{4,}\b', consulta.lower())
            
            # Crear registro de búsqueda
            registro = {
                "timestamp": datetime.now().isoformat(),
                "consulta": consulta,
                "num_resultados": len(resultados),
                "dominios": [extraer_dominio(r["url"]) for r in resultados if "url" in r],
                "palabras_clave": palabras_clave
            }
            
            # Añadir al historial
            with open(hist_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(registro) + "\n")
                
            logger.debug(f"Registro de búsqueda guardado: {consulta}")
        except Exception as e:
            logger.error(f"Error al aprender de búsqueda: {e}")
    
    def obtener_contenido_pagina(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extrae el contenido de una página web con manejo mejorado
        
        Args:
            url: URL de la página a analizar
            
        Returns:
            Diccionario con el contenido y metadatos de la página, o None si hubo error
        """
        url = normalizar_url(url)

        try:
            # Verificar si la URL es válida
            if not es_url_valida(url):
                logger.error(f"URL inválida: {url}")
                return None

            # Verificar caché
            resultado_cache = self.cache_manager.get(url, prefix="page")
            if resultado_cache:
                logger.info(f"📚 Usando caché para URL: {url}")
                return resultado_cache

            logger.info(f"Descargando contenido de {url}")

            # Headers rotatorios para evitar bloqueos
            user_agents = self.preferences.get("user_agents", [self.user_agent])
            headers = {
                "User-Agent": random.choice(user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            }

            # Gestión de sesión para cookies
            session = requests.Session()
            
            # Varios intentos para manejar posibles errores
            response = None
            for intento in range(self.max_retry):
                try:
                    response = session.get(url, headers=headers, timeout=20)
                    break
                except (requests.Timeout, requests.ConnectionError) as e:
                    if intento == self.max_retry - 1:
                        raise
                    logger.warning(f"Reintentando descarga ({intento+1}/{self.max_retry}): {e}")
                    time.sleep(2)

            # Manejo de redirecciones
            if response.status_code in (301, 302, 307, 308) and 'Location' in response.headers:
                url_redireccion = response.headers['Location']
                if not url_redireccion.startswith(('http://', 'https://')):
                    base_url = '/'.join(url.split('/')[:3])  # http(s)://dominio.com
                    url_redireccion = f"{base_url}{url_redireccion}"
                logger.info(f"Siguiendo redirección a {url_redireccion}")
                response = session.get(url_redireccion, headers=headers, timeout=20)

            # Manejo de acceso denegado
            if response.status_code == 403:
                logger.warning("Acceso denegado (403). Reintentando con User-Agent alternativo...")
                time.sleep(2)
                headers["User-Agent"] = random.choice(user_agents)
                response = session.get(url, headers=headers, timeout=20)

            if response.status_code != 200:
                logger.error(f"Error HTTP {response.status_code} al acceder a {url}")
                return None

            # Detección del juego de caracteres
            encoding = response.encoding
            if encoding == 'ISO-8859-1' and 'charset=utf-8' in response.text.lower():
                encoding = 'utf-8'
            
            html_content = response.content.decode(encoding, errors='replace')
            soup = BeautifulSoup(html_content, 'html.parser')

            # Eliminar elementos no deseados
            for tag in soup(['script', 'style', 'footer', 'nav', 'header', 'aside', 'iframe', 'form', 'noscript']):
                tag.decompose()

            # Extraer título mejorado
            titulo = "Sin título"
            if soup.title:
                titulo = soup.title.string.strip()
            elif soup.find('meta', property='og:title'):
                titulo = soup.find('meta', property='og:title')['content'].strip()
            elif soup.find('h1'):
                titulo = soup.find('h1').get_text().strip()

            # Extraer descripción para resumen
            descripcion = ""
            if soup.find('meta', attrs={'name': 'description'}):
                descripcion = soup.find('meta', attrs={'name': 'description'})['content'].strip()
            elif soup.find('meta', property='og:description'):
                descripcion = soup.find('meta', property='og:description')['content'].strip()

            # Obtener el extractor específico para este sitio
            extractor = get_extractor(url)
            contenido = extractor(soup) if extractor else ""

            # Limpiar contenido final
            contenido = re.sub(r'\n{3,}', '\n\n', contenido)  # Eliminar líneas en blanco excesivas
            contenido = contenido.strip()

            # Extraer tablas si hay pocas
            tablas = []
            try:
                tablas_html = soup.find_all('table')
                tablas = self._extraer_tablas(soup) if len(tablas_html) <= 5 else []
            except Exception as e:
                logger.error(f"Error al extraer tablas: {e}")
                
            # Extraer otros datos
            datos_comerciales = {}
            datos_contacto = {}
            tipo_contenido = "pagina"
            imagenes = []

            try:
                datos_comerciales = self._extraer_datos_comerciales(soup, contenido)
            except Exception as e:
                logger.error(f"Error al extraer datos comerciales: {e}")
                
            try:
                datos_contacto = self._extraer_datos_contacto(soup, contenido)
            except Exception as e:
                logger.error(f"Error al extraer datos de contacto: {e}")
                
            try:
                tipo_contenido = self._detectar_tipo_contenido(url, soup)
            except Exception as e:
                logger.error(f"Error al detectar tipo de contenido: {e}")
                
            try:
                imagenes = self._extraer_imagenes(soup, url)
            except Exception as e:
                logger.error(f"Error al extraer imágenes: {e}")

            # Crear resultado con metadatos enriquecidos
            resultado = {
                "titulo": titulo,
                "descripcion": descripcion[:300] if descripcion else "",
                "contenido": contenido.strip(),
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "longitud": len(contenido),
                "tipo_contenido": tipo_contenido,
                "datos_comerciales": datos_comerciales,
                "datos_contacto": datos_contacto,
                "tablas": tablas,
                "imagenes": imagenes
            }

            # Guardar en caché
            self.cache_manager.set(url, resultado, prefix="page")

            logger.info(f"✅ Contenido extraído correctamente de {url} ({len(contenido)} caracteres)")
            return resultado

        except requests.exceptions.Timeout:
            logger.error(f"Tiempo de espera agotado al acceder a {url}")
            return {"titulo": "Error de tiempo de espera", "contenido": "La página tardó demasiado en responder.", "url": url}
        except requests.exceptions.TooManyRedirects:
            logger.error(f"Demasiadas redirecciones al acceder a {url}")
            return {"titulo": "Error de redirección", "contenido": "La página tiene demasiadas redirecciones.", "url": url}
        except requests.exceptions.SSLError:
            logger.error(f"Error SSL al acceder a {url}")
            return {"titulo": "Error de seguridad SSL", "contenido": "No se pudo establecer una conexión segura con el sitio.", "url": url}
        except Exception as e:
            logger.error(f"Error al obtener contenido de {url}: {e}")
            return {"titulo": "Error de extracción", "contenido": f"No se pudo obtener el contenido: {str(e)}", "url": url}

    def _extraer_tablas(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extrae tablas del HTML y las convierte a formato estructurado
    
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
        
        Returns:
            Lista de tablas extraídas en formato estructurado
        """
        tablas = []
        for idx, tabla_html in enumerate(soup.find_all('table')):
            try:
                # Extraer encabezados
                headers = []
                head_row = tabla_html.find('thead')
                if head_row:
                    for th in head_row.find_all(['th']):
                        headers.append(th.get_text().strip())
                else:
                    # Intentar con la primera fila
                    first_row = tabla_html.find('tr')
                    if first_row:
                        for th in first_row.find_all(['th', 'td']):
                            headers.append(th.get_text().strip())
            
                # Si no se encontraron encabezados, crear automáticos
                if not headers:
                    # Determinar número de columnas contando celdas en la primera fila
                    primera_fila = tabla_html.find('tr')
                    if primera_fila:
                        num_cols = len(primera_fila.find_all(['td', 'th']))
                        headers = [f"Columna {i+1}" for i in range(num_cols)]
            
                # Extraer filas de datos
                rows = []
                for tr in tabla_html.find_all('tr')[1:] if headers else tabla_html.find_all('tr'):
                    row_data = []
                    for td in tr.find_all(['td', 'th']):
                        cell_text = td.get_text().strip()
                        row_data.append(cell_text)
                
                    if row_data:  # Ignorar filas vacías
                        rows.append(row_data)
            
                # Verificar si todos los datos tienen la misma longitud que los encabezados
                if headers:
                    for i, row in enumerate(rows):
                        # Ajustar si hay desajuste en el número de columnas
                        if len(row) < len(headers):
                            rows[i] = row + [""] * (len(headers) - len(row))
                        elif len(row) > len(headers):
                            rows[i] = row[:len(headers)]
            
                # Si hay suficientes datos, crear la estructura de la tabla
                if rows and (len(rows) > 1 or len(headers) > 1):
                    tabla = {
                        "id": f"tabla_{idx+1}",
                        "encabezados": headers,
                        "filas": rows,
                        "num_filas": len(rows),
                        "num_columnas": len(headers) if headers else len(rows[0]) if rows else 0
                    }
                    tablas.append(tabla)
                
            except Exception as e:
                logger.error(f"Error al procesar tabla {idx+1}: {e}")
                continue
            
        return tablas

    def _extraer_datos_comerciales(self, soup: BeautifulSoup, contenido_texto: str) -> Dict[str, Any]:
        """
        Extrae información comercial como precios, ofertas, etc.
    
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            contenido_texto: Texto del contenido extraído
        
        Returns:
            Diccionario con datos comerciales extraídos
        """
        comercial = {
            "precios": [],
            "moneda": None,
            "ofertas": []
        }
    
        # Extraer precios (patrones comunes en EUR, USD, etc.)
        patrones_precio = [
            r'(?:\$|€|£)\s?([0-9]+(?:[,.][0-9]{1,2})?)',  # $10, $10.99, €10, etc.
            r'([0-9]+(?:[,.][0-9]{1,2})?)(?:\s?(?:\$|€|£|USD|EUR|GBP))',  # 10$, 10.99€, etc.
            r'precio:?\s*(?:\$|€|£)?\s?([0-9]+(?:[,.][0-9]{1,2})?)'  # precio: $10.99
        ]
    
        precios = []
        monedas = {"$": "USD", "€": "EUR", "£": "GBP"}
    
        for patron in patrones_precio:
            for match in re.finditer(patron, contenido_texto, re.IGNORECASE):
                precio = match.group(1).strip()
                # Detectar moneda
                simbolo = match.group(0)[0] if match.group(0)[0] in monedas else None
                if simbolo in monedas and not comercial["moneda"]:
                    comercial["moneda"] = monedas[simbolo]
                
                # Convertir a formato numérico
                try:
                    precio_normalizado = float(precio.replace(',', '.'))
                    precios.append(precio_normalizado)
                except:
                    pass
    
        # Eliminar duplicados y ordenar
        comercial["precios"] = sorted(list(set(precios)))
    
        # Buscar ofertas o descuentos
        patrones_ofertas = [
            r'(?:oferta|descuento|rebaja|ahorra)(?:[\s:]+)(\d+%|\d+\s+%)',
            r'(?:\d+)%\s+(?:de descuento|off|menos)'
        ]
    
        for patron in patrones_ofertas:
            ofertas = re.findall(patron, contenido_texto, re.IGNORECASE)
            for oferta in ofertas:
                comercial["ofertas"].append(oferta.strip())
    
        return comercial

    def _detectar_tipo_contenido(self, url: str, soup: BeautifulSoup) -> str:
        """
        Detecta el tipo de contenido (artículo, blog, tienda, etc.)
    
        Args:
            url: URL de la página
            soup: Objeto BeautifulSoup con el HTML parseado
        
        Returns:
            String con el tipo de contenido detectado
        """
        # Verificar metadatos para algunos tipos de contenido comunes
        og_type = soup.find('meta', property='og:type')
        if og_type and og_type.get('content'):
            og_content = og_type.get('content').lower()
            if 'article' in og_content:
                return 'articulo'
            elif 'product' in og_content:
                return 'producto'
            elif 'video' in og_content:
                return 'video'
    
        # Detectar por URL
        url_lower = url.lower()
        if re.search(r'/(blog|articulo|post|entrada)/', url_lower):
            return 'blog'
        elif re.search(r'/(product|producto)/', url_lower):
            return 'producto'
        elif re.search(r'/(video|watch)/', url_lower):
            return 'video'
        elif re.search(r'/(categoria|category)/', url_lower):
            return 'categoria'
    
        # Detectar por elementos específicos en la página
        if soup.find('article'):
            return 'articulo'
        elif soup.find(class_=lambda c: c and ('product' in c.lower() or 'precio' in c.lower())):
            return 'producto'
        elif soup.find('video') or soup.find('iframe', src=lambda s: s and ('youtube' in s or 'vimeo' in s)):
            return 'video'
    
        # Detectar blogs
        if soup.find_all('time') or soup.find('div', class_=lambda c: c and 'blog' in c.lower()):
            return 'blog'
    
        # Por defecto
        return 'pagina'

    def _extraer_imagenes(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extrae imágenes relevantes de la página
    
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            base_url: URL base para resolver rutas relativas
        
        Returns:
            Lista de diccionarios con información de imágenes
        """
        imagenes = []
        max_imagenes = 5  # Limitar a un número razonable de imágenes
    
        # Primero buscar imágenes de Open Graph (suelen ser las principales)
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            url_imagen = og_image.get('content')
            # Convertir URL relativa a absoluta si es necesario
            if url_imagen.startswith('/'):
                parsed_base = urlparse(base_url)
                url_imagen = f"{parsed_base.scheme}://{parsed_base.netloc}{url_imagen}"
            
            imagenes.append({
                "url": url_imagen,
                "alt": "Imagen principal",
                "tipo": "principal"
            })
    
        # Buscar imágenes con cierto tamaño (posiblemente relevantes)
        for img in soup.find_all('img', src=True):
            if len(imagenes) >= max_imagenes:
                break
            
            # Ignorar iconos y pequeñas imágenes UI
            src = img.get('src', '')
            if 'icon' in src.lower() or 'logo' in src.lower() or not src:
                continue
            
            # Verificar tamaño si está disponible
            width = img.get('width', '0')
            height = img.get('height', '0')
            
            try:
                w, h = int(width), int(height)
                if w < 100 or h < 100:  # Probablemente un icono
                    continue
            except:
                pass  # Si no podemos determinar el tamaño, continuamos
            
            # Convertir URL relativa a absoluta si es necesario
            url_imagen = src
            if url_imagen.startswith('//'):
                url_imagen = f"https:{url_imagen}"
            elif url_imagen.startswith('/'):
                parsed_base = urlparse(base_url)
                url_imagen = f"{parsed_base.scheme}://{parsed_base.netloc}{url_imagen}"
            elif not url_imagen.startswith(('http://', 'https://')):
                # URL relativa
                if base_url.endswith('/'):
                    url_imagen = f"{base_url}{url_imagen}"
                else:
                    url_imagen = f"{base_url}/{url_imagen}"
            
            # Extraer texto alternativo
            alt_text = img.get('alt', '')
            
            # Determinar tipo de imagen
            tipo = 'contenido'
            if 'banner' in url_imagen.lower() or 'hero' in url_imagen.lower():
                tipo = 'banner'
            elif 'thumb' in url_imagen.lower() or 'preview' in url_imagen.lower():
                tipo = 'miniatura'
            
            # Evitar duplicados
            if not any(img['url'] == url_imagen for img in imagenes):
                imagenes.append({
                    "url": url_imagen,
                    "alt": alt_text,
                    "tipo": tipo
                })
    
        return imagenes

    def obtener_fecha_actual(self) -> Dict[str, Any]:
        """
        Devuelve información sobre la fecha y hora actual (local, no requiere conexión)
        
        Returns:
            Diccionario con información de fecha y hora
        """
        ahora = datetime.now()
        return {
            "fecha": ahora.strftime("%d/%m/%Y"),
            "hora": ahora.strftime("%H:%M:%S"),
            "dia_semana": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"][ahora.weekday()],
            "timestamp": ahora.timestamp()
        }
        
    def obtener_estadisticas_aprendizaje(self) -> Dict[str, Any]:
        """
        Genera estadísticas sobre el aprendizaje del motor web
        
        Returns:
            Diccionario con estadísticas de búsqueda
        """
        hist_file = os.path.join(self.cache_dir, "search_history.jsonl")
        if not os.path.exists(hist_file):
            return {"busquedas_totales": 0}
            
        busquedas = []
        dominios = {}
        palabras_clave = {}
        
        try:
            with open(hist_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        registro = json.loads(line)
                        busquedas.append(registro)
                        
                        # Contar dominios
                        for dominio in registro.get("dominios", []):
                            dominios[dominio] = dominios.get(dominio, 0) + 1
                            
                        # Contar palabras clave
                        for palabra in registro.get("palabras_clave", []):
                            palabras_clave[palabra] = palabras_clave.get(palabra, 0) + 1
                    except Exception as e:
                        logger.error(f"Error al procesar línea de historial: {e}")
                        continue
                        
            # Ordenar por frecuencia
            dominios_top = sorted(dominios.items(), key=lambda x: x[1], reverse=True)[:10]
            palabras_top = sorted(palabras_clave.items(), key=lambda x: x[1], reverse=True)[:15]
            
            return {
                "busquedas_totales": len(busquedas),
                "dominios_frecuentes": dict(dominios_top),
                "palabras_clave_frecuentes": dict(palabras_top),
                "ultima_busqueda": busquedas[-1]["consulta"] if busquedas else None,
                "dominios_preferidos": self.preferences["preferred_domains"],
                "dominios_bloqueados": self.preferences["banned_domains"]
            }
        except Exception as e:
            logger.error(f"Error al obtener estadísticas de aprendizaje: {e}")
            return {
                "busquedas_totales": 0,
                "error": str(e)
            }

    def limpiar_cache(self, dias_antiguedad: int = 7) -> int:
        """
        Limpia archivos de caché más antiguos que un número específico de días
        
        Args:
            dias_antiguedad: Días mínimos de antigüedad para eliminar
            
        Returns:
            Número de archivos eliminados
        """
        return self.cache_manager.clear_old_items(dias_antiguedad)