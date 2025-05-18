"""
web.py - Motor de búsqueda web con enfoque en privacidad
"""
import random
import time
import requests
import json
import os
import re
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import hashlib
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urlparse, urljoin

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jarvis_web.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("web")

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
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        self.headers = {"User-Agent": self.user_agent}
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
            
    def _get_cache_path(self, query: str) -> str:
        """
        Genera una ruta de caché para una consulta
        
        Args:
            query: Consulta de búsqueda
            
        Returns:
            Ruta al archivo de caché
        """
        # Crear un hash de la consulta para el nombre de archivo
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{query_hash}.json")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """
        Verifica si la caché es válida basada en TTL
        
        Args:
            cache_path: Ruta al archivo de caché
            
        Returns:
            True si la caché es válida, False en caso contrario
        """
        if not os.path.exists(cache_path):
            return False
            
        file_time = os.path.getmtime(cache_path)
        now = datetime.now().timestamp()
        return (now - file_time) < self.preferences["cache_ttl"]
        
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
        cache_path = self._get_cache_path(consulta)
        
        # Verificar caché primero si no se fuerza recarga
        if not forzar_recarga and self._is_cache_valid(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    resultados = json.load(f)
                    logger.info(f"📚 Usando datos en caché para: '{consulta}'")
                    return resultados
            except Exception as e:
                logger.error(f"Error al leer caché: {e}")
        
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
            
            if response.status_code == 200:
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
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(resultados, f, indent=2)
                    
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
                "dominios": [self._extraer_dominio(r["url"]) for r in resultados if "url" in r],
                "palabras_clave": palabras_clave
            }
            
            # Añadir al historial
            with open(hist_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(registro) + "\n")
                
            logger.debug(f"Registro de búsqueda guardado: {consulta}")
        except Exception as e:
            logger.error(f"Error al aprender de búsqueda: {e}")
            
    def _extraer_dominio(self, url: str) -> str:
        """
        Extrae el dominio base de una URL
        
        Args:
            url: URL completa
            
        Returns:
            Dominio extraído
        """
        match = re.search(r'(?:https?:\/\/)?(?:www\.)?([^\/]+)', url)
        return match.group(1) if match else url

    def _extraer_dominio_completo(self, url: str) -> str:
        """
        Extrae el dominio con protocolo de una URL (http://dominio.com)
        
        Args:
            url: URL completa
            
        Returns:
            Dominio con protocolo
        """
        match = re.search(r'^(https?://[^/]+)', url)
        return match.group(1) if match else url

    def obtener_contenido_pagina(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Extrae el contenido de una página web con manejo mejorado
        
        Args:
            url: URL de la página a analizar
            
        Returns:
            Diccionario con el contenido y metadatos de la página, o None si hubo error
        """
        url = url.strip()

        try:
            # Asegurar que la URL comience con http:// o https://
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Verificar si la URL es válida
            parsed_url = urlparse(url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                logger.error(f"URL inválida: {url}")
                return None

            # Generar hash de la URL para caché
            url_hash = hashlib.md5(url.encode()).hexdigest()
            cache_path = os.path.join(self.cache_dir, f"page_{url_hash}.json")

            # Verificar caché
            if self._is_cache_valid(cache_path):
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        cached_result = json.load(f)
                        logger.info(f"📚 Usando caché para URL: {url}")
                        return cached_result
                except Exception as e:
                    logger.error(f"Error al leer caché: {e}")

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
                if any(x in url for x in ["coinbase", "bitcoin", "crypto", "binance"]):
                    logger.info("Usando fuente alternativa para criptomonedas.")
                    return self._obtener_datos_cripto_alternativa(url)
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

            # Extracción específica por sitio
            contenido = ""
            site_extractors = {
                "github.com": self._extraer_github,
                "stackoverflow.com": self._extraer_stackoverflow,
                "stackexchange.com": self._extraer_stackoverflow,
                "wikipedia.org": self._extraer_wikipedia,
                "youtube.com": self._extraer_youtube,
                "youtu.be": self._extraer_youtube,
                "twitter.com": self._extraer_twitter,
                "x.com": self._extraer_twitter,
                "reddit.com": self._extraer_reddit,
                "amazon.": self._extraer_amazon,
                "medium.com": self._extraer_medium
            }
            
            # Intentar usar extractores específicos
            for domain, extractor in site_extractors.items():
                if domain in url:
                    contenido = extractor(soup)
                    if contenido:
                        break
                        
            # Si no se extrajo contenido con extractores específicos
            if not contenido:
                if "docs." in url or ".documentation" in url or "/docs/" in url:
                    contenido = self._extraer_documentacion(soup)
                    
            # Si aún no hay contenido útil, usar estrategia general
            if not contenido:
                contenido = self._extraer_contenido_general(soup)

            # Limpiar contenido final
            contenido = re.sub(r'\n{3,}', '\n\n', contenido)  # Eliminar líneas en blanco excesivas
            contenido = contenido.strip()

            # Extraer tablas si hay pocas
            tablas_html = soup.find_all('table')
            tablas = self._extraer_tablas(soup) if len(tablas_html) <= 5 else []
            
            # Extraer otros datos
            datos_comerciales = self._extraer_datos_comerciales(soup, contenido)
            datos_contacto = self._extraer_datos_contacto(soup, contenido)
            
            # Crear resultado con metadatos enriquecidos
            resultado = {
                "titulo": titulo,
                "descripcion": descripcion[:300] if descripcion else "",
                "contenido": contenido.strip(),
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "longitud": len(contenido),
                "tipo_contenido": self._detectar_tipo_contenido(url, soup),
                "datos_comerciales": datos_comerciales,
                "datos_contacto": datos_contacto,
                "tablas": tablas,
                "imagenes": self._extraer_imagenes(soup, url)
            }

            # Guardar en caché
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=2, ensure_ascii=False)

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

    def _extraer_contenido_general(self, soup: BeautifulSoup) -> str:
        """
        Extrae contenido general de una página web cuando no hay extractores específicos
        
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            
        Returns:
            Contenido extraído
        """
        # Estrategia de extracción principal: detectar el contenedor más relevante
        candidatos = soup.find_all(['article', 'main', 'section', 'div'])
        candidatos = [c for c in candidatos if len(c.get_text(strip=True)) > 300]

        if candidatos:
            # Ordenar candidatos por longitud de contenido
            mejor = sorted(candidatos, key=lambda c: len(c.get_text()), reverse=True)[0]
            
            # Priorizar elementos principales 
            parrafos = []
            
            # Extraer encabezados para estructura
            for h in mejor.find_all(['h1', 'h2', 'h3', 'h4']):
                text = h.get_text(strip=True)
                if len(text) > 5:
                    nivel = int(h.name[1])
                    if nivel == 1:
                        parrafos.append(f"\n\n## {text}\n")
                    elif nivel == 2:
                        parrafos.append(f"\n\n### {text}\n")
                    else:
                        parrafos.append(f"\n\n#### {text}\n")
            
            # Extraer párrafos, listas y bloques de código
            for elem in mejor.find_all(['p', 'ul', 'ol', 'pre', 'code', 'blockquote']):
                if elem.name == 'p':
                    text = elem.get_text(strip=True)
                    if len(text) > 30:
                        parrafos.append(text)
                elif elem.name in ('ul', 'ol'):
                    items = []
                    for li in elem.find_all('li'):
                        item_text = li.get_text(strip=True)
                        if len(item_text) > 10:
                            items.append(f"• {item_text}")
                    if items:
                        parrafos.append("\n".join(items))
                elif elem.name in ('pre', 'code'):
                    code_text = elem.get_text(strip=True)
                    if len(code_text) > 20:
                        parrafos.append(f"```\n{code_text}\n```")
                elif elem.name == 'blockquote':
                    quote_text = elem.get_text(strip=True)
                    if len(quote_text) > 30:
                        parrafos.append(f"> {quote_text}")
            
            return "\n\n".join(parrafos)

        # Último recurso: extraer todos los párrafos significativos
        parrafos = []
        # Extraer encabezados principales primero
        for h in soup.find_all(['h1', 'h2']):
            text = h.get_text(strip=True)
            if len(text) > 5:
                parrafos.append(f"\n## {text}\n")
        
        # Luego extraer párrafos largos
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if len(text) > 50:  # Solo párrafos significativos
                parrafos.append(text)
        
        return "\n\n".join(parrafos[:15])  # Limitar a 15 párrafos para evitar contenido excesivo

    def _detectar_tipo_contenido(self, url: str, soup: Optional[BeautifulSoup] = None) -> str:
        """
        Detecta el tipo de contenido de la página
        
        Args:
            url: URL de la página
            soup: Objeto BeautifulSoup (opcional)
            
        Returns:
            Tipo de contenido detectado
        """
        # Detección basada en URL (no depende de soup)
        if "github.com" in url:
            return "repositorio"
        elif "wikipedia.org" in url:
            return "enciclopedia"
        elif "stackoverflow.com" in url:
            return "q&a"
        elif "youtube.com" in url or "youtu.be" in url:
            return "video"
        elif "twitter.com" in url or "x.com" in url:
            return "social"
        elif "amazon" in url or "ebay" in url or "shop" in url or "store" in url:
            return "comercio"
        
        # Detección basada en soup (solo si soup es válido)
        if soup is not None:
            if soup.find("article"):
                return "blog"
            elif soup.find("meta", property="og:type"):
                return soup.find("meta", property="og:type")["content"]
        
        # Valor predeterminado
        return "web"

    def _extraer_tablas(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Extrae tablas de datos y las convierte a formato estructurado
        
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            
        Returns:
            Lista de tablas extraídas con metadatos
        """
        tablas_extraidas = []
        
        for i, tabla in enumerate(soup.find_all('table')):
            try:
                # Detectar si la tabla tiene encabezados
                encabezados = []
                thead = tabla.find('thead')
                if thead:
                    encabezados = [th.get_text().strip() for th in thead.find_all('th')]
                
                # Si no hay thead, buscar en la primera fila
                if not encabezados:
                    primera_fila = tabla.find('tr')
                    if primera_fila:
                        # Intentar con th primero
                        encabezados = [th.get_text().strip() for th in primera_fila.find_all('th')]
                        # Si no hay th, usar td
                        if not encabezados:
                            encabezados = [td.get_text().strip() for td in primera_fila.find_all('td')]
                
                # Procesar filas
                filas = []
                for tr in tabla.find_all('tr')[1:] if encabezados else tabla.find_all('tr'):
                    fila = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                    if fila:  # Ignorar filas vacías
                        filas.append(fila)
                
                # Convertir a formato estructurado si hay encabezados
                datos_tabla = []
                if encabezados and filas:
                    for fila in filas:
                        if len(fila) == len(encabezados):
                            datos_tabla.append(dict(zip(encabezados, fila)))
                
                if filas:
                    tablas_extraidas.append({
                        "indice": i+1,
                        "filas": len(filas),
                        "columnas": len(filas[0]) if filas else 0,
                        "encabezados": encabezados,
                        "datos_brutos": filas[:10],  # Limitar a 10 filas para reducir tamaño
                        "datos_estructurados": datos_tabla[:10] if encabezados else []
                    })
            except Exception as e:
                logger.error(f"Error al procesar tabla: {e}")
        
        return tablas_extraidas

    def _extraer_imagenes(self, soup: BeautifulSoup, url_base: str) -> List[Dict[str, str]]:
        """
        Extrae imágenes con metadatos y contexto
        
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            url_base: URL base para resolver rutas relativas
            
        Returns:
            Lista de imágenes extraídas con metadatos
        """
        imagenes = []
        
        for i, img in enumerate(soup.find_all('img')):
            try:
                # Obtener atributos básicos
                src = img.get('src', '')
                if not src:
                    continue
                    
                # Normalizar URL
                if src.startswith('/'):
                    src = f"{self._extraer_dominio_completo(url_base)}{src}"
                elif not src.startswith(('http://', 'https://')):
                    # Es una URL relativa
                    src = f"{url_base.rstrip('/')}/{src.lstrip('/')}"
                
                # Recolectar metadatos
                alt = img.get('alt', '')
                title = img.get('title', '')
                width = img.get('width', '')
                height = img.get('height', '')
                
                # Determinar el contexto (texto cercano)
                contexto = ""
                
                # Buscar texto en elementos padres o hermanos
                parent = img.parent
                if parent:
                    # Buscar en texto del padre directo
                    parent_text = parent.get_text().strip()
                    if parent_text:
                        contexto = parent_text[:100] + "..." if len(parent_text) > 100 else parent_text
                    else:
                        # Buscar en figcaption si existe
                        figcaption = parent.find('figcaption')
                        if figcaption:
                            contexto = figcaption.get_text().strip()
                
                # Si aún no tenemos contexto, buscar en encabezados cercanos
                if not contexto:
                    for heading in ['h1', 'h2', 'h3', 'h4']:
                        prev_heading = img.find_previous(heading)
                        if prev_heading and prev_heading.get_text().strip():
                            contexto = prev_heading.get_text().strip()
                            break
                
                # Limitar imágenes a las primeras 20 para evitar sobrecarga
                if len(imagenes) < 20:
                    imagenes.append({
                        "indice": i+1,
                        "src": src,
                        "alt": alt,
                        "title": title,
                        "dimensiones": f"{width}x{height}" if width and height else "",
                        "contexto": contexto
                    })
                else:
                    break
            except Exception as e:
                logger.error(f"Error al procesar imagen: {e}")
        
        return imagenes

    def _extraer_datos_comerciales(self, soup: BeautifulSoup, contenido_texto: str) -> Dict[str, Any]:
        """
        Extrae precios, SKUs, información de producto y disponibilidad
        
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            contenido_texto: Texto del contenido extraído
            
        Returns:
            Diccionario con datos comerciales extraídos
        """
        datos = {
            "precios": [],
            "sku": None,
            "disponibilidad": None,
            "rating": None,
            "moneda": None
        }
        
        # Detectar moneda predominante
        monedas = {
            "$": "USD",
            "€": "EUR",
            "£": "GBP",
            "¥": "JPY",
            "₹": "INR",
            "A$": "AUD",
            "C$": "CAD",
            "MX$": "MXN"
        }
        
        moneda_encontrada = None
        for simbolo, codigo in monedas.items():
            if simbolo in contenido_texto:
                moneda_encontrada = codigo
                break
        
        datos["moneda"] = moneda_encontrada
        
        # Extraer precios usando patrones comunes
        patrones_precio = [
            r'\$\s*(\d+(?:[.,]\d{1,2})?)',  # $XX.XX
            r'(\d+(?:[.,]\d{1,2})?)\s*\$',   # XX.XX$
            r'€\s*(\d+(?:[.,]\d{1,2})?)',    # €XX.XX
            r'(\d+(?:[.,]\d{1,2})?)\s*€',    # XX.XX€
            r'£\s*(\d+(?:[.,]\d{1,2})?)',    # £XX.XX
            r'(\d+(?:[.,]\d{1,2})?)\s*£',    # XX.XX£
            r'price["\':\s]+(\d+(?:[.,]\d{1,2})?)',  # price: XX.XX
            r'(?:price|cost|total)[\W_]+(\d+(?:[.,]\d{1,2})?)',  # price XX.XX
            r'(\d+(?:[.,]\d{1,2})?)\s*(?:euros|dollars|USD|EUR)'  # XX.XX dollars
        ]
        
        for patron in patrones_precio:
            matches = re.findall(patron, contenido_texto)
            datos["precios"].extend(matches)
        
        # Eliminar duplicados y normalizar
        datos["precios"] = list(set(datos["precios"]))
        
        # Buscar SKU
        sku_matches = re.search(r'(?:SKU|sku|product[_\s-]*id|item[_\s-]*number)[\W_]+([a-zA-Z0-9-]{4,20})', contenido_texto)
        if sku_matches:
            datos["sku"] = sku_matches.group(1)
        
        # Buscar disponibilidad
        if re.search(r'out\s+of\s+stock|agotado|no\s+disponible', contenido_texto, re.IGNORECASE):
            datos["disponibilidad"] = "No disponible"
        elif re.search(r'in\s+stock|disponible|available', contenido_texto, re.IGNORECASE):
            datos["disponibilidad"] = "En stock"
        
        # Buscar rating
        rating_match = re.search(r'([0-5](?:\.[0-9])?)[\s/]+5', contenido_texto)
        if rating_match:
            datos["rating"] = rating_match.group(1)
        
        return datos

    def _extraer_datos_contacto(self, soup: BeautifulSoup, contenido_texto: str) -> Dict[str, Any]:
        """
        Extrae emails, teléfonos, direcciones y otros datos de contacto
        
        Args:
            soup: Objeto BeautifulSoup con el HTML parseado
            contenido_texto: Texto del contenido extraído
            
        Returns:
            Diccionario con datos de contacto extraídos
        """
        contacto = {
            "emails": [],
            "telefonos": [],
            "direcciones": [],
            "redes_sociales": {}
        }
        
        # Extraer emails
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', contenido_texto)
        contacto["emails"] = list(set(emails))  # Eliminar duplicados
        
        # Extraer teléfonos (múltiples formatos)
        patrones_telefono = [
            r'\+\d{1,4}[\s-]?\d{1,3}[\s-]?\d{3,4}[\s-]?\d{3,4}',  # +XX XXX XXXX XXX
            r'\(\d{3,4}\)[\s-]?\d{3}[\s-]?\d{4}',  # (XXX) XXX XXXX
            r'\d{3}[\s-]?\d{2,3}[\s-]?\d{2,3}[\s-]?\d{2,3}'  # XXX XX XX XX
        ]
        
        telefonos = []
        for patron in patrones_telefono:
            telefonos.extend(re.findall(patron, contenido_texto))
        contacto["telefonos"] = list(set(telefonos))  # Eliminar duplicados
        
        # Extraer direcciones (heurística simple)
        # Buscar patrones comunes como códigos postales
        lineas = contenido_texto.split('\n')
        for i, linea in enumerate(lineas):
            if re.search(r'\b\d{5}\b|\b[A-Z]{1,2}\d{1,2}\s\d[A-Z]{2}\b', linea):  # Código postal US o UK
                # Tomar 2 líneas antes y después como posible dirección
                inicio = max(0, i-2)
                fin = min(len(lineas), i+3)
                direccion_potencial = ' '.join(lineas[inicio:fin]).strip()
                if len(direccion_potencial) > 10 and len(direccion_potencial) < 200:
                    contacto["direcciones"].append(direccion_potencial)
        
        # Extraer enlaces a redes sociales
        redes_sociales = {
            'facebook': r'(?:facebook\.com|fb\.com)/([a-zA-Z0-9._%+-]+)',
            'twitter': r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)',
            'instagram': r'instagram\.com/([a-zA-Z0-9_.]+)',
            'linkedin': r'linkedin\.com/(?:in|company)/([a-zA-Z0-9_-]+)',
            'youtube': r'youtube\.com/(?:user|channel)/([a-zA-Z0-9_-]+)',
            'github': r'github\.com/([a-zA-Z0-9_-]+)'
        }
        
        for red, patron in redes_sociales.items():
            for a in soup.find_all('a', href=re.compile(patron)):
                try:
                    match = re.search(patron, a['href'])
                    if match:
                        contacto["redes_sociales"][red] = match.group(1)
                except:
                    continue
        
        return contacto

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
        try:
            now = datetime.now()
            segundos_antiguedad = dias_antiguedad * 86400
            archivos_eliminados = 0
            
            for archivo in os.listdir(self.cache_dir):
                # Solo procesar archivos JSON (caché)
                if not archivo.endswith('.json') or archivo == 'preferences.json':
                    continue
                    
                ruta_archivo = os.path.join(self.cache_dir, archivo)
                tiempo_mod = os.path.getmtime(ruta_archivo)
                antiguedad = now.timestamp() - tiempo_mod
                
                if antiguedad > segundos_antiguedad:
                    os.remove(ruta_archivo)
                    archivos_eliminados += 1
                    
            logger.info(f"Limpieza de caché: {archivos_eliminados} archivos eliminados")
            return archivos_eliminados
        except Exception as e:
            logger.error(f"Error al limpiar caché: {e}")
            return 0
            
    # Implementaciones de extractores específicos por sitio
    
    def _extraer_github(self, soup: BeautifulSoup) -> str:
        """Extrae contenido específico de GitHub"""
        contenido = ""
        
        # README
        readme = soup.find('article', class_='markdown-body entry-content container-lg')
        if not readme:
            readme = soup.find('div', class_='markdown-body')
        
        if readme:
            contenido = readme.get_text(separator="\n", strip=True)
            
            # Procesar encabezados para mejor formato
            contenido = re.sub(r'(^|\n)# ([^\n]+)', r'\1## \2', contenido)
            contenido = re.sub(r'(^|\n)## ([^\n]+)', r'\1### \2', contenido)
            
            # Extraer info del repositorio si está disponible
            repo_info = []
            
            # Descripción
            description = soup.find('p', class_='f4 my-3')
            if description:
                repo_info.append(description.get_text(strip=True))
            
            # Lenguajes
            langs = soup.find('div', class_='mb-2 repository-lang-stats-graph')
            if langs:
                repo_info.append(f"Lenguajes: {langs.get('aria-label', '')}")
                
            # Estrellas, forks, etc.
            for link in soup.find_all('a', class_='Link--muted'):
                text = link.get_text(strip=True)
                if text and any(x in text.lower() for x in ['star', 'fork', 'watch']):
                    repo_info.append(text)
                    
            if repo_info:
                contenido = "# Información del repositorio\n" + "\n".join(repo_info) + "\n\n# README\n" + contenido
        
        return contenido

    def _extraer_stackoverflow(self, soup: BeautifulSoup) -> str:
        """Extrae contenido específico de Stack Overflow"""
        contenido = ""
        
        # Pregunta
        question = soup.find('div', id=lambda x: x and x.startswith('question'))
        if question:
            # Título
            title = question.find('a', class_='question-hyperlink')
            if not title:
                title = soup.find('h1')
                
            if title:
                contenido += f"# {title.get_text(strip=True)}\n\n"
            
            # Contenido de la pregunta
            question_body = question.find('div', class_='post-text')
            if not question_body:
                question_body = question.find('div', class_='s-prose')
                
            if question_body:
                contenido += question_body.get_text(separator="\n", strip=True) + "\n\n"
            
            # Respuestas
            answers = soup.find_all('div', id=lambda x: x and x.startswith('answer'))
            if answers:
                contenido += "# Respuestas\n\n"
                
                for i, answer in enumerate(answers[:3], 1):  # Limitar a 3 respuestas
                    contenido += f"## Respuesta {i}\n"
                    
                    # Marcar si es respuesta aceptada
                    if 'accepted-answer' in answer.get('class', []):
                        contenido += "✓ RESPUESTA ACEPTADA\n\n"
                    
                    # Contenido de la respuesta
                    answer_body = answer.find('div', class_='post-text')
                    if not answer_body:
                        answer_body = answer.find('div', class_='s-prose')
                        
                    if answer_body:
                        contenido += answer_body.get_text(separator="\n", strip=True) + "\n\n"
        
        return contenido

    def _extraer_wikipedia(self, soup: BeautifulSoup) -> str:
        """Extrae contenido específico de Wikipedia"""
        contenido = ""
        
        # Título
        title = soup.find('h1', id='firstHeading')
        if title:
            contenido += f"# {title.get_text(strip=True)}\n\n"
        
        # Resumen (primer párrafo)
        content_div = soup.find('div', id='mw-content-text')
        if content_div:
            # Extraer el resumen inicial
            paragraphs = content_div.find_all('p')
            for p in paragraphs:
                if len(p.get_text(strip=True)) > 100:
                    contenido += p.get_text(strip=True) + "\n\n"
                    break
            
            # Extraer secciones principales
            for section in content_div.find_all(['h2', 'h3'], recursive=True):
                # Ignorar secciones no relevantes
                if any(x in section.get_text().lower() for x in ['referencias', 'véase también', 'enlaces externos']):
                    continue
                    
                section_title = section.get_text(strip=True).replace('[editar]', '')
                section_level = "##" if section.name == 'h2' else "###"
                
                contenido += f"{section_level} {section_title}\n\n"
                
                # Extraer contenido de la sección
                current = section.find_next()
                while current and current.name not in ['h2', 'h3', 'h4']:
                    if current.name == 'p' and len(current.get_text(strip=True)) > 30:
                        contenido += current.get_text(strip=True) + "\n\n"
                    elif current.name in ['ul', 'ol']:
                        for li in current.find_all('li', recursive=False):
                            li_text = li.get_text(strip=True)
                            if len(li_text) > 15:
                                contenido += f"• {li_text}\n"
                        contenido += "\n"
                    
                    try:
                        current = current.find_next()
                    except:
                        break
        
        return contenido

    def _extraer_youtube(self, soup: BeautifulSoup) -> str:
        """Extrae información de videos de YouTube"""
        contenido = ""
        
        # Título
        title = soup.find('meta', itemprop='name')
        if title:
            contenido += f"# {title['content']}\n\n"
        else:
            title = soup.find('meta', property='og:title')
            if title:
                contenido += f"# {title['content']}\n\n"
        
        # Descripción
        description = soup.find('meta', itemprop='description')
        if description and description['content']:
            contenido += "## Descripción\n\n" + description['content'] + "\n\n"
        else:
            description = soup.find('meta', property='og:description')
            if description:
                contenido += "## Descripción\n\n" + description['content'] + "\n\n"
        
        # Datos del canal
        channel = soup.find('meta', itemprop='channelName')
        if channel:
            contenido += f"• Canal: {channel['content']}\n"
        
        # Fecha de publicación
        date = soup.find('meta', itemprop='datePublished')
        if date:
            contenido += f"• Publicado: {date['content']}\n"
        
        # Duración
        duration = soup.find('meta', itemprop='duration')
        if duration:
            contenido += f"• Duración: {duration['content']}\n"
        
        return contenido

    def _extraer_twitter(self, soup: BeautifulSoup) -> str:
        """Extrae contenido específico de Twitter/X"""
        contenido = ""
        
        # Meta título (generalmente contiene el nombre del usuario)
        title = soup.find('meta', property='og:title')
        if title:
            contenido += f"# Tweet de {title['content']}\n\n"
        
        # Descripción (generalmente contiene el texto del tweet)
        description = soup.find('meta', property='og:description')
        if description:
            contenido += f"{description['content']}\n\n"
        
        # Información adicional (fecha, interacciones, etc.)
        meta_info = []
        
        # Fecha
        date = soup.find('meta', property='og:article:published_time')
        if date:
            from dateutil import parser
            try:
                fecha_obj = parser.parse(date['content'])
                meta_info.append(f"Fecha: {fecha_obj.strftime('%Y-%m-%d %H:%M')}")
            except:
                meta_info.append(f"Fecha: {date['content']}")
        
        if meta_info:
            contenido += "## Información\n" + "\n".join(meta_info) + "\n\n"
        
        return contenido

    def _extraer_reddit(self, soup: BeautifulSoup) -> str:
        """Extrae contenido específico de Reddit"""
        contenido = ""
        
        # Título del post
        title = soup.find('h1')
        if title:
            contenido += f"# {title.get_text(strip=True)}\n\n"
        
        # Contenido del post
        post_body = soup.find('div', attrs={'data-test-id': 'post-content'})
        if post_body:
            contenido += post_body.get_text(strip=True) + "\n\n"
        
        # Comentarios principales
        comments = soup.find_all('div', class_=lambda c: c and 'Comment' in c)
        if comments:
            contenido += "## Comentarios destacados\n\n"
            
            for i, comment in enumerate(comments[:5], 1):  # Limitar a 5 comentarios
                comment_text = comment.get_text(strip=True)
                if len(comment_text) > 50:  # Solo comentarios sustanciales
                    contenido += f"### Comentario {i}\n{comment_text[:500]}...\n\n"
        
        return contenido

    def _extraer_amazon(self, soup: BeautifulSoup) -> str:
        """Extrae contenido específico de Amazon"""
        contenido = ""
        
        # Título del producto
        title = soup.find('span', id='productTitle')
        if not title:
            title = soup.find('h1')
            
        if title:
            contenido += f"# {title.get_text(strip=True)}\n\n"
        
        # Precio
        price = soup.find('span', id='priceblock_ourprice')
        if not price:
            price = soup.find('span', class_='a-offscreen')
            
        if price:
            contenido += f"**Precio:** {price.get_text(strip=True)}\n\n"
        
        # Disponibilidad
        availability = soup.find('span', id='availability')
        if availability:
            contenido += f"**Disponibilidad:** {availability.get_text(strip=True)}\n\n"
        
        # Valoraciones
        rating = soup.find('span', id='acrPopover')
        if rating:
            contenido += f"**Valoración:** {rating.get('title', '')}\n\n"
        
        # Descripción del producto
        description = soup.find('div', id='productDescription')
        if description:
            contenido += "## Descripción\n\n" + description.get_text(strip=True) + "\n\n"
        
        # Características
        feature_bullets = soup.find('div', id='feature-bullets')
        if feature_bullets:
            contenido += "## Características\n\n"
            for li in feature_bullets.find_all('li'):
                contenido += f"• {li.get_text(strip=True)}\n"
            contenido += "\n"
        
        # Detalles técnicos
        tech_details = soup.find('table', id='productDetails_techSpec_section_1')
        if tech_details:
            contenido += "## Detalles técnicos\n\n"
            for row in tech_details.find_all('tr'):
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    contenido += f"• **{th.get_text(strip=True)}:** {td.get_text(strip=True)}\n"
            contenido += "\n"
        
        return contenido
    def _extraer_medium(self, soup: BeautifulSoup) -> str:
        """Extrae contenido específico de artículos de Medium"""
        contenido = ""
        
        # Título del artículo
        title = soup.find('h1')
        if title:
            contenido += f"# {title.get_text(strip=True)}\n\n"
        
        # Autor y fecha
        author = soup.find('a', class_=lambda x: x and 'author' in x)
        if not author:
            author = soup.find('a', attrs={'rel': 'author'})
        
        date = soup.find('time')
        
        if author or date:
            meta_info = []
            if author:
                meta_info.append(f"Autor: {author.get_text(strip=True)}")
            if date:
                meta_info.append(f"Publicado: {date.get_text(strip=True)}")
            
            contenido += " | ".join(meta_info) + "\n\n"
        
        # Subtítulo o descripción
        subtitle = soup.find('h2')
        if subtitle:
            subtitle_text = subtitle.get_text(strip=True)
            if subtitle_text:
                contenido += f"## {subtitle_text}\n\n"
        
        # Contenido principal
        article = soup.find('article')
        if article:
            # Extraer párrafos
            for p in article.find_all('p'):
                text = p.get_text(strip=True)
                if len(text) > 20:  # Evitar párrafos vacíos o muy cortos
                    contenido += text + "\n\n"
            
            # Extraer encabezados para mantener la estructura
            for h in article.find_all(['h2', 'h3']):
                text = h.get_text(strip=True)
                if text and len(text) > 5:
                    level = "##" if h.name == 'h2' else "###"
                    contenido += f"\n{level} {text}\n\n"
            
            # Extraer listas
            for ul in article.find_all('ul'):
                contenido += "\n"
                for li in ul.find_all('li'):
                    li_text = li.get_text(strip=True)
                    if li_text:
                        contenido += f"• {li_text}\n"
                contenido += "\n"
            
            # Extraer citas
            for blockquote in article.find_all('blockquote'):
                quote_text = blockquote.get_text(strip=True)
                if quote_text:
                    contenido += f"> {quote_text}\n\n"
            
            # Extraer código fuente
            for pre in article.find_all('pre'):
                code_text = pre.get_text(strip=True)
                if code_text:
                    contenido += f"```\n{code_text}\n```\n\n"
        
        # Si no hay artículo, buscar contenido en secciones
        if not contenido or len(contenido) < 200:
            sections = soup.find_all('section')
            parrafos = []
            
            for section in sections:
                for p in section.find_all('p'):
                    text = p.get_text(strip=True)
                    if len(text) > 50:  # Solo párrafos significativos
                        parrafos.append(text)
            
            if parrafos:
                contenido += "\n\n".join(parrafos)
        
        # Palabras clave o etiquetas
        tags = soup.find_all('a', class_=lambda x: x and 'tag' in x.lower())
        if tags:
            tag_list = [tag.get_text(strip=True) for tag in tags if tag.get_text(strip=True)]
            if tag_list:
                contenido += "\n\n## Etiquetas\n"
                contenido += ", ".join(tag_list)
        
        # Tiempo de lectura
        reading_time = soup.find(text=re.compile(r'\d+ min read', re.IGNORECASE))
        if reading_time:
            contenido += f"\n\nTiempo de lectura: {reading_time.strip()}"
        
        return contenido
        
    def _extraer_documentacion(self, soup: BeautifulSoup) -> str:
        """Extrae contenido de páginas de documentación técnica"""
        contenido = ""
        
        # Título principal
        title = soup.find('h1')
        if title:
            contenido += f"# {title.get_text(strip=True)}\n\n"
        
        # Descripción o resumen inicial
        for p in soup.find_all('p')[:3]:  # Primeros párrafos como posible introducción
            if len(p.get_text(strip=True)) > 50:
                contenido += p.get_text(strip=True) + "\n\n"
                break
        
        # Extraer secciones principales con sus encabezados
        for h in soup.find_all(['h2', 'h3', 'h4']):
            text = h.get_text(strip=True)
            if len(text) < 5 or any(skip in text.lower() for skip in ['índice', 'contenido', 'table of']):
                continue
                
            level = "##" if h.name == 'h2' else "###" if h.name == 'h3' else "####"
            contenido += f"\n{level} {text}\n\n"
            
            # Extraer contenido hasta el siguiente encabezado del mismo nivel o superior
            next_h = h.find_next(['h2', 'h3', 'h4'])
            current = h.find_next()
            
            while current and (not next_h or current != next_h):
                if current.name == 'p' and len(current.get_text(strip=True)) > 30:
                    contenido += current.get_text(strip=True) + "\n\n"
                elif current.name in ['ul', 'ol']:
                    for li in current.find_all('li'):
                        li_text = li.get_text(strip=True)
                        if len(li_text) > 10:
                            contenido += f"• {li_text}\n"
                    contenido += "\n"
                elif current.name == 'pre' or current.name == 'code':
                    code_text = current.get_text(strip=True)
                    if len(code_text) > 20:
                        contenido += f"```\n{code_text}\n```\n\n"
                
                try:
                    current = current.find_next()
                except:
                    break
        
        # Si no extraímos suficiente contenido, intentar con selectores específicos comunes en docs
        if len(contenido) < 500:
            article = soup.find(['article', 'main', '.content', '.documentation', '.docs'])
            if article:
                for p in article.find_all('p'):
                    if len(p.get_text(strip=True)) > 50:
                        contenido += p.get_text(strip=True) + "\n\n"
                
                # Extraer ejemplos de código
                for code in article.find_all(['pre', 'code']):
                    code_text = code.get_text(strip=True)
                    if len(code_text) > 50:
                        contenido += f"```\n{code_text}\n```\n\n"
        
        return contenido
    
    def _obtener_datos_cripto_alternativa(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de criptomonedas usando APIs públicas como alternativa
        
        Args:
            url: URL original que no se pudo acceder
            
        Returns:
            Diccionario con datos alternativos o None si no se pudieron obtener
        """
        try:
            # Determinar qué criptomoneda se está buscando
            cripto_id = "bitcoin"  # Por defecto
            
            # Extraer ID de la cripto de la URL
            cripto_map = {
                "bitcoin": ["bitcoin", "btc"],
                "ethereum": ["ethereum", "eth"],
                "cardano": ["cardano", "ada"],
                "dogecoin": ["dogecoin", "doge"],
                "ripple": ["ripple", "xrp"],
                "solana": ["solana", "sol"],
                "polkadot": ["polkadot", "dot"]
            }
            
            url_lower = url.lower()
            for id, terms in cripto_map.items():
                if any(term in url_lower for term in terms):
                    cripto_id = id
                    break
                    
            # Usar la API pública de CoinGecko
            api_url = f"https://api.coingecko.com/api/v3/coins/{cripto_id}"
            
            headers = {
                "User-Agent": random.choice(self.preferences.get("user_agents", [self.user_agent])),
                "Accept": "application/json"
            }
            
            logger.info(f"Obteniendo datos alternativos para {cripto_id} desde API")
            
            # Hacer la solicitud con reintentos
            for intento in range(self.max_retry):
                try:
                    response = requests.get(api_url, headers=headers, timeout=15)
                    if response.status_code == 200:
                        break
                    logger.warning(f"Intento {intento+1}/{self.max_retry} falló con código {response.status_code}")
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"Error en intento {intento+1}/{self.max_retry}: {e}")
                    if intento == self.max_retry - 1:
                        raise
                    time.sleep(1)
            
            if response.status_code == 200:
                data = response.json()
                
                # Construir un resultado similar al que retornaría obtener_contenido_pagina
                result = {
                    "titulo": f"{data['name']} ({data['symbol'].upper()}) - Datos actualizados",
                    "url": api_url,
                    "contenido": f"""
# {data['name']} ({data['symbol'].upper()})

## Precios Actuales
Precio actual: ${data['market_data']['current_price']['usd']} USD
Cambio 24h: {data['market_data']['price_change_percentage_24h']}%

## Capitalización de Mercado
${data['market_data']['market_cap']['usd']} USD

## Datos de Mercado
Volumen 24h: ${data['market_data']['total_volume']['usd']} USD
Máximo histórico: ${data['market_data']['ath']['usd']} USD
Fecha máximo histórico: {data['market_data']['ath_date']['usd']}

## Descripción
{data.get('description', {}).get('es', data.get('description', {}).get('en', 'No disponible'))[:500]}...
                    """,
                    "datos_comerciales": {
                        "precios": [str(data['market_data']['current_price']['usd'])],
                        "moneda": "USD",
                        "disponibilidad": "En circulación",
                        "rating": str(data.get('sentiment_votes_up_percentage', 0)/20)  # Convertir a escala 0-5
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"Datos alternativos obtenidos para {cripto_id}")
                return result
            else:
                logger.error(f"No se pudieron obtener datos alternativos: Error {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error al obtener datos alternativos: {e}")
            return None