"""
Extractor especializado para las facultades y unidades academicas de la EPN.

Navega a la seccion general de facultades y extrae los detalles individuales de cada
unidad: autoridades de decanato, descripcion, mision, vision, departamentos adscritos,
informacion de contacto y canales oficiales.
"""

import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from src.config import settings
from src.scrapers.base_scraper import BaseScraper
from src.utils.helpers import clean_text, extract_email, extract_phone


class FacultadesScraper(BaseScraper):
    """Extrae informacion dimensional y descriptiva de las facultades de la EPN."""

    # Siglas institucionales oficiales conocidas de la EPN para estandarizacion
    ACRONYMS_MAP = {
        "facultad de ciencias": "FC",
        "facultad de ciencias administrativas": "FCA",
        "facultad de ingenieria civil y ambiental": "FICA",
        "facultad de ingenieria de sistemas": "FIS",
        "facultad de ingenieria electrica y electronica": "FIEE",
        "facultad de ingenieria mecanica": "FIM",
        "facultad de ingenieria quimica y agroindustria": "FIQA",
        "facultad de geologia y petroleos": "FIGP",
        "facultad de ingenieria en geologia y petroleos": "FIGP",
        "escuela de formacion de tecnologos": "ESFOT",
    }

    def _infer_acronym(self, name: str) -> str:
        """Determina la sigla institucional a partir del nombre normalizado.

        Args:
            name (str): Nombre de la facultad.

        Returns:
            str: Sigla corta (ej: FIS, FIEE).
        """
        cleaned = re.sub(r"[áäà]", "a", name.lower())
        cleaned = re.sub(r"[éëè]", "e", cleaned)
        cleaned = re.sub(r"[íïì]", "i", cleaned)
        cleaned = re.sub(r"[óöò]", "o", cleaned)
        cleaned = re.sub(r"[úüù]", "u", cleaned)

        # Ordenar patrones por longitud descendente para que "ciencias administrativas" coincida antes que "ciencias"
        for pattern, acr in sorted(self.ACRONYMS_MAP.items(), key=lambda x: len(x[0]), reverse=True):
            if pattern in cleaned:
                return acr

        # Generar acronimo de fallback con iniciales
        words = [w for w in name.split() if w.lower() not in ["de", "la", "y", "en", "el"]]
        return "".join(w[0].upper() for w in words if w)

    def _get_faculty_urls(self) -> List[str]:
        """Obtiene las URLs de cada facultad a partir del directorio principal.

        Returns:
            List[str]: Lista de URLs absolutas de facultades.
        """
        directory_url = settings.endpoints.get("facultades", f"{settings.base_url}/facultades/")
        html_content = self.http_client.get(directory_url)
        if not html_content:
            self.logger.warning(f"No fue posible recuperar el directorio de facultades desde {directory_url}")
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        faculty_urls = []

        for link in soup.find_all("a", href=True):
            href = link["href"].strip()
            # Normalizar URL alternativa redundante de ingenieria civil
            if "facultad-de-ingenieria-civil-y-ambiental" in href:
                href = "https://www.epn.edu.ec/facultad-ingenieria-civil-ambiental/"
            if any(k in href for k in ["facultad-", "/esfot"]) and href.startswith("http"):
                if href != directory_url and href not in faculty_urls:
                    faculty_urls.append(href)

        self.logger.info(f"Localizadas {len(faculty_urls)} URLs de unidades academicas.")
        return faculty_urls

    def _parse_faculty_page(self, url: str) -> Dict[str, Any]:
        """Parsea la pagina de una facultad especifica para extraer sus atributos.

        Args:
            url (str): Direccion URL de la facultad.

        Returns:
            Dict[str, Any]: Atributos institucionales estructurados.
        """
        html_content = self.http_client.get(url)
        if not html_content:
            self.logger.warning(f"Facultad omitida: no se pudo obtener {url}")
            return {}

        soup = BeautifulSoup(html_content, "html.parser")

        # Nombre de la facultad
        name = ""
        h1 = soup.find("h1")
        if h1:
            raw_h1 = clean_text(h1.get_text())
            if not raw_h1.startswith("$") and any(k in raw_h1.lower() for k in ["facultad", "escuela", "ciencias"]):
                name = raw_h1

        if not name:
            title = soup.title.get_text() if soup.title else ""
            cleaned_title = clean_text(title.replace("EPN", "").replace("-", "").strip())
            if any(k in cleaned_title.lower() for k in ["facultad", "escuela", "ciencias"]):
                name = cleaned_title

        if not name:
            slug = url.strip("/").split("/")[-1]
            slug = slug.replace("facultad-de-", "").replace("facultad-", "")
            name = f"Facultad de {slug.replace('-', ' ').title()}"

        sigla = self._infer_acronym(name)

        # Autoridades: Decano y Subdecano
        decano = None
        subdecano = None
        # Separador de linea: evita que textos de elementos vecinos queden pegados ("...ToapaxiSubdecano:")
        text_all = soup.get_text(separator="\n")

        # Busqueda de decano y subdecano mediante expresiones regulares en texto
        decano_match = re.search(r"Decan[oa]\s*:\s*([^\n\r<]+)", text_all, re.IGNORECASE)
        if decano_match:
            raw_d = decano_match.group(1).split(",")[0]
            decano = clean_text(raw_d).strip(".")
            if "@" in decano:
                decano = None

        subdecano_match = re.search(r"Subdecan[oa]\s*:\s*([^\n\r<]+)", text_all, re.IGNORECASE)
        if subdecano_match:
            raw_s = subdecano_match.group(1).split(",")[0]
            subdecano = clean_text(raw_s).strip(".")
            if "@" in subdecano:
                subdecano = None

        # Mision y Vision
        mision = ""
        vision = ""
        paragraphs = soup.find_all(["p", "div"])
        for p in paragraphs:
            p_text = clean_text(p.get_text())
            if not mision and "misión" in p_text.lower() and len(p_text) > 40:
                mision = p_text
            elif not vision and "visión" in p_text.lower() and len(p_text) > 40:
                vision = p_text

        # Si no estan etiquetados explicitamente con la palabra mision/vision, tomar descripcion inicial
        descripcion = ""
        for p in soup.find_all("p"):
            p_clean = clean_text(p.get_text())
            if len(p_clean) > 80 and not p_clean.startswith("Decan"):
                descripcion = p_clean
                break

        # Departamentos adscritos
        departamentos = []
        dept_headers = soup.find_all(re.compile(r"h[2-4]"))
        for h in dept_headers:
            t = clean_text(h.get_text())
            if "departamento" in t.lower() or "escuela" in t.lower():
                departamentos.append(t)

        # Contacto
        contacto_email = extract_email(text_all)
        contacto_telefono = extract_phone(text_all)
        
        # Ubicacion en campus
        ubicacion_match = re.search(r"Ubicaci[oó]n\s*:\s*([^\n\r<]+)", text_all, re.IGNORECASE)
        ubicacion = clean_text(ubicacion_match.group(1)) if ubicacion_match else None

        return {
            "nombre": name,
            "sigla": sigla,
            "decano": decano,
            "subdecano": subdecano,
            "descripcion": descripcion,
            "mision": mision or None,
            "vision": vision or None,
            "url": url,
            "departamentos_adscritos": "; ".join(departamentos) if departamentos else None,
            "contacto_correo": contacto_email,
            "contacto_telefono": contacto_telefono,
            "ubicacion_campus": ubicacion,
        }

    def extract(self) -> List[Dict[str, Any]]:
        """Realiza la extraccion iterativa de todas las facultades identificadas.

        Returns:
            List[Dict[str, Any]]: Catalogo completo de facultades estructurado.
        """
        urls = self._get_faculty_urls()
        facultades = []
        for url in urls:
            self.logger.info(f"Extrayendo informacion de facultad: {url}")
            data = self._parse_faculty_page(url)
            if data:
                facultades.append(data)

        return facultades
