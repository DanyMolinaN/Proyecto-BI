"""
Extractor de informacion corporativa e institucional de la EPN.

Extrae la mision, vision, principios y valores institucionales desde '/nosotros/',
los hitos cronologicos desde '/historia/', y la infraestructura cientifica desde
'/laboratorios_institucionales/' (Instituto Geofisico, ModeMat, CICAM, etc.).
"""

import re
from typing import Any, Dict, List
from bs4 import BeautifulSoup

from src.config import settings
from src.scrapers.base_scraper import BaseScraper
from src.utils.helpers import clean_text, extract_labeled_value, page_lines, remove_accents


class InstitucionalScraper(BaseScraper):
    """Extrae las dimensiones institucionales, historicas y cientificas de la universidad."""

    def _extract_nosotros(self) -> Dict[str, Any]:
        """Extrae principios, mision, vision y valores desde la pagina "nosotros".

        La pagina publica cada bloque como un encabezado ("MISION", "VISION", "Valores") seguido
        de su texto en la linea siguiente. Lo que no se encuentra queda en None (sin valores por defecto).

        Returns:
            Dict[str, Any]: mision, vision, valores, principios y fuente_url.
        """
        url = settings.endpoints.get("nosotros", f"{settings.base_url}/nosotros/")
        html_content = self.http_client.get(url)
        empty = {"mision": None, "vision": None, "valores": None, "principios": None, "fuente_url": url}
        if not html_content:
            self.logger.warning(f"No se pudo obtener {url}; se omite mision, vision y valores.")
            return empty

        lines = page_lines(BeautifulSoup(html_content, "html.parser"))
        norms = [remove_accents(l).lower().strip() for l in lines]

        mision = extract_labeled_value(lines, "Mision")
        vision = extract_labeled_value(lines, "Vision")

        # Principios: parrafos entre el encabezado "Principios" y "MISION"
        principios = None
        if "mision" in norms:
            end = norms.index("mision")
            starts = [i for i in range(end) if norms[i] == "principios"]
            if starts:
                principios = clean_text(" ".join(lines[starts[-1] + 1:end])) or None

        # Valores: nombres cortos (una palabra o dos) entre "Institucionales" y "Plan Estrategico"
        valores: List[str] = []
        if "institucionales" in norms:
            start = norms.index("institucionales") + 1
            stop = next((i for i in range(start, len(lines)) if norms[i].startswith("plan estrategico")), len(lines))
            for line in lines[start:stop]:
                if len(line) <= 22 and line[:1].isupper() and not line.endswith((".", ",")):
                    valores.append(line)

        return {
            "mision": clean_text(mision) or None,
            "vision": clean_text(vision) or None,
            "valores": ", ".join(valores) or None,
            "principios": principios,
            "fuente_url": url,
        }

    def _extract_historia(self) -> List[Dict[str, Any]]:
        """Extrae la cronologia de hitos de la pagina de historia.

        Estructura real: una linea con el anio, una linea opcional con el dia ("30 de agosto"),
        un titulo corto y la descripcion. Los registros sin anio legible conservan anio None.

        Returns:
            List[Dict[str, Any]]: Hitos con anio, titulo y descripcion.
        """
        url = settings.endpoints.get("historia", f"{settings.base_url}/historia/")
        html_content = self.http_client.get(url)
        if not html_content:
            self.logger.warning(f"No se pudo obtener {url}; se omiten los hitos historicos.")
            return []

        lines = page_lines(BeautifulSoup(html_content, "html.parser"))
        norms = [remove_accents(l).lower().strip() for l in lines]
        start = norms.index("historia") + 1 if "historia" in norms else 0
        stop = next((i for i in range(start, len(lines)) if norms[i].startswith(("direccion:", "llamanos"))), len(lines))

        hitos: List[Dict[str, Any]] = []
        block: List[str] = []
        anio = None

        def flush() -> None:
            body = [b for b in block if not re.fullmatch(r"\d{1,2} de [a-zñ]+", remove_accents(b).lower())
                    and not b.lower().startswith("powered by")]
            if anio is not None and len(body) >= 2:
                hitos.append({
                    "tipo_registro": "Hito Historico",
                    "anio": anio,
                    "titulo": body[0],
                    "descripcion": clean_text(" ".join(body[1:])),
                    "fuente_url": url,
                })

        for line in lines[start:stop]:
            if re.fullmatch(r"(1[89]\d{2}|20\d{2})", line):
                flush()
                anio, block = int(line), []
            else:
                block.append(line)
        flush()
        return hitos

    def _extract_laboratorios(self) -> List[Dict[str, Any]]:
        """Extrae centros e institutos de investigacion adscritos a la EPN.

        Returns:
            List[Dict[str, Any]]: Estructura cientifica institucional.
        """
        url = settings.endpoints.get("laboratorios_institucionales", f"{settings.base_url}/laboratorios_institucionales/")
        html_content = self.http_client.get(url)
        centros: List[Dict[str, Any]] = []

        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            headers = soup.find_all(["h2", "h3"])
            for h in headers:
                name = clean_text(h.get_text())
                if any(k in name.lower() for k in ["instituto", "centro", "laboratorio", "parque"]):
                    # Buscar parrafos subsiguientes para descripcion y ubicacion
                    desc = ""
                    ubicacion = None
                    curr = h.find_next_sibling()
                    while curr and curr.name in ["p", "div"]:
                        text_curr = clean_text(curr.get_text())
                        if "ubicación" in text_curr.lower() or "edificio" in text_curr.lower():
                            ubicacion = re.sub(r"^ubicaci[oó]n\s*:\s*", "", text_curr, flags=re.IGNORECASE)
                        elif len(text_curr) > 30 and not desc:
                            desc = text_curr
                        curr = curr.find_next_sibling()

                    centros.append({
                        "tipo_registro": "Estructura de Investigacion",
                        "nombre_centro": name,
                        "tipo_estructura": "Instituto" if "instituto" in name.lower() else "Centro de Investigacion",
                        "ubicacion": ubicacion,
                        "descripcion": desc or None,
                        "fuente_url": url,
                    })

        return centros

    def extract(self) -> List[Dict[str, Any]]:
        """Extrae y consolida todas las fuentes de informacion institucional.

        Returns:
            List[Dict[str, Any]]: Conjunto de registros institucionales, historicos y cientificos.
        """
        nosotros = self._extract_nosotros()
        historia = self._extract_historia()
        laboratorios = self._extract_laboratorios()

        records: List[Dict[str, Any]] = []

        # Identidad filosofica: solo lo que la pagina publica
        if nosotros["mision"]:
            records.append({
                "categoria": "Identidad Filosofica",
                "clave": "Mision",
                "contenido": nosotros["mision"],
                "metadato": nosotros["valores"],
                "url": nosotros["fuente_url"],
            })
        if nosotros["vision"]:
            records.append({
                "categoria": "Identidad Filosofica",
                "clave": "Vision",
                "contenido": nosotros["vision"],
                "metadato": nosotros["principios"],
                "url": nosotros["fuente_url"],
            })

        # Hitos historicos
        for h in historia:
            records.append({
                "categoria": "Hito Historico",
                "clave": str(h["anio"]) if h.get("anio") else "Sin anio",
                "contenido": h.get("descripcion", ""),
                "metadato": h.get("titulo", ""),
                "url": h.get("fuente_url", ""),
            })

        # Estructuras cientificas
        for lab in laboratorios:
            records.append({
                "categoria": "Centro de Investigacion",
                "clave": lab.get("nombre_centro", ""),
                "contenido": lab.get("descripcion", ""),
                "metadato": f"Tipo: {lab.get('tipo_estructura')}" + (f" | Ubicacion: {lab['ubicacion']}" if lab.get("ubicacion") else ""),
                "url": lab.get("fuente_url", ""),
            })

        return records
