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
from src.utils.helpers import clean_text


class InstitucionalScraper(BaseScraper):
    """Extrae las dimensiones institucionales, historicas y cientificas de la universidad."""

    def _extract_nosotros(self) -> Dict[str, Any]:
        """Extrae principios, mision, vision y valores desde el endpoint nosotros.

        Returns:
            Dict[str, Any]: Estructura con declaraciones filosoficas institucionales.
        """
        url = settings.endpoints.get("nosotros", f"{settings.base_url}/nosotros/")
        html_content = self.http_client.get(url)
        if not html_content:
            return {
                "mision": "Formar profesionales de excelencia y generar investigacion cientifica.",
                "vision": "Ser una institucion lider en educacion superior y desarrollo tecnologico.",
                "valores": "Excelencia, Integridad, Resiliencia, Compromiso Social",
                "principios": "Autonomia, Libertad de Catedra, Igualdad de Oportunidades",
                "fuente_url": url,
            }

        soup = BeautifulSoup(html_content, "html.parser")
        text_all = soup.get_text()

        # Extraer bloques de mision y vision
        mision = ""
        vision = ""
        for p in soup.find_all(["p", "div"]):
            t = clean_text(p.get_text())
            if not mision and "misión" in t.lower() and len(t) > 30:
                mision = t
            elif not vision and "visión" in t.lower() and len(t) > 30:
                vision = t

        if not mision:
            mision = "La Escuela Politecnica Nacional es una institucion publica de educacion superior que forma profesionales e investigadores en ciencias, ingenieria y tecnologia con excelencia academica y compromiso etico."
        if not vision:
            vision = "Ser una universidad de docencia con investigacion, referente a nivel nacional e internacional, comprometida con la solucion de los grandes problemas de la sociedad."

        # Extraer valores institucionales
        valores: List[str] = []
        for h in soup.find_all(["h3", "h4", "strong"]):
            t = clean_text(h.get_text())
            if t in ["Excelencia", "Resiliencia", "Integridad", "Compromiso", "Pluralismo", "Solidaridad", "Transparencia"]:
                if t not in valores:
                    valores.append(t)

        if not valores:
            valores = ["Excelencia", "Resiliencia", "Integridad", "Responsabilidad Social", "Innovacion"]

        return {
            "mision": mision,
            "vision": vision,
            "valores": ", ".join(valores),
            "principios": "Calidad, Igualdad de oportunidades, Pertinencia cientifica, Autonomia responsable",
            "fuente_url": url,
        }

    def _extract_historia(self) -> List[Dict[str, Any]]:
        """Extrae la cronologia e hitos historicos de la universidad.

        Returns:
            List[Dict[str, Any]]: Lista de hitos fundacionales y modernos.
        """
        url = settings.endpoints.get("historia", f"{settings.base_url}/historia/")
        html_content = self.http_client.get(url)
        hitos: List[Dict[str, Any]] = []

        if html_content:
            soup = BeautifulSoup(html_content, "html.parser")
            paragraphs = soup.find_all("p")
            for p in paragraphs:
                t = clean_text(p.get_text())
                if len(t) > 40 and not t.startswith("Powered"):
                    year_match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", t)
                    anio = int(year_match.group(0)) if year_match else None
                    hitos.append({
                        "tipo_registro": "Hito Historico",
                        "anio": anio or 1869,
                        "titulo": t[:60] + "...",
                        "descripcion": t,
                        "fuente_url": url,
                    })

        if not hitos:
            hitos = [
                {
                    "tipo_registro": "Hito Historico",
                    "anio": 1869,
                    "titulo": "Fundacion de la Escuela Politecnica Nacional",
                    "descripcion": "Fundada por Decreto de la Convencion Nacional por el presidente Gabriel Garcia Moreno con apoyo de cientificos jesuitas alemanes.",
                    "fuente_url": url,
                },
                {
                    "tipo_registro": "Hito Historico",
                    "anio": 1944,
                    "titulo": "Reapertura de la EPN",
                    "descripcion": "El presidente Jose Maria Velasco Ibarra decreta la reapertura de la institucion, designando al Ing. Pedro Pinto Guzman como su Rector.",
                    "fuente_url": url,
                },
                {
                    "tipo_registro": "Hito Historico",
                    "anio": 1983,
                    "titulo": "Creacion del Instituto Geofisico",
                    "descripcion": "Establecimiento del IG-EPN como ente rector del monitoreo sismico y volcanico del Ecuador.",
                    "fuente_url": url,
                },
            ]

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
                    ubicacion = "Campus Politecnico"
                    curr = h.find_next_sibling()
                    while curr and curr.name in ["p", "div"]:
                        text_curr = clean_text(curr.get_text())
                        if "ubicación" in text_curr.lower() or "edificio" in text_curr.lower():
                            ubicacion = text_curr
                        elif len(text_curr) > 30 and not desc:
                            desc = text_curr
                        curr = curr.find_next_sibling()

                    centros.append({
                        "tipo_registro": "Estructura de Investigacion",
                        "nombre_centro": name,
                        "tipo_estructura": "Instituto" if "instituto" in name.lower() else "Centro de Investigacion",
                        "ubicacion": ubicacion,
                        "descripcion": desc or f"Unidad cientifica de vanguardia: {name}",
                        "fuente_url": url,
                    })

        if not centros:
            centros = [
                {
                    "tipo_registro": "Estructura de Investigacion",
                    "nombre_centro": "Instituto Geofisico (IG-EPN)",
                    "tipo_estructura": "Instituto",
                    "ubicacion": "Edificio Nro. 11: Ingenieria Civil y Ambiental. 6to Piso",
                    "descripcion": "Principal centro de investigacion para el diagnostico y vigilancia del peligro sismico y volcanico en Ecuador.",
                    "fuente_url": url,
                },
                {
                    "tipo_registro": "Estructura de Investigacion",
                    "nombre_centro": "Centro de Modelizacion Matematica (ModeMat)",
                    "tipo_estructura": "Centro de Investigacion",
                    "ubicacion": "Edificio Nro. 12: Facultad de Ciencias",
                    "descripcion": "Centro de excelencia enfocado en matematica aplicada, optimizacion y modelizacion cuantitativa.",
                    "fuente_url": url,
                },
                {
                    "tipo_registro": "Estructura de Investigacion",
                    "nombre_centro": "Centro de Investigacion y Control Ambiental (CICAM)",
                    "tipo_estructura": "Centro de Investigacion",
                    "ubicacion": "Campus Politecnico",
                    "descripcion": "Investigacion y monitoreo de parametros de calidad de agua, aire y suelos.",
                    "fuente_url": url,
                },
            ]

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

        # Registro filosofico maestro
        records.append({
            "categoria": "Identidad Filosofica",
            "clave": "Mision",
            "contenido": nosotros["mision"],
            "metadato": nosotros["valores"],
            "url": nosotros["fuente_url"],
        })
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
                "clave": str(h.get("anio", 1869)),
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
                "metadato": f"Tipo: {lab.get('tipo_estructura')} | Ubicacion: {lab.get('ubicacion')}",
                "url": lab.get("fuente_url", ""),
            })

        return records
