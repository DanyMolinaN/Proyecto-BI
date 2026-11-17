"""
Extractor de carreras y programas academicos de grado, tecnologias y posgrado de la EPN.

Extrae programas desde las secciones oficiales 'oferta-de-grado' y 'oferta-de-posgrado',
ingresando a las fichas individuales de cada carrera para obtener atributos curriculares,
resoluciones CES, perfiles de ingreso/egreso y modalidades de ensenanza.
"""

import re
from typing import Any, Dict, List, Set, Tuple
from bs4 import BeautifulSoup

from src.config import settings
from src.scrapers.base_scraper import BaseScraper
from src.utils.helpers import (
    remove_accents,
    extract_labeled_value,
    page_lines,
    clean_text,
    extract_degree_level,
    extract_duration_periods,
    extract_modality,
)


class CarrerasScraper(BaseScraper):
    """Extrae informacion dimensional y descriptiva de las carreras ofrecidas por la EPN."""

    def _discover_program_urls(self) -> List[Tuple[str, str]]:
        """Descubre las URLs de programas de grado y posgrado en los portales oficiales.

        Returns:
            List[Tuple[str, str]]: Pares de (url_programa, nivel_sugerido).
        """
        urls: List[Tuple[str, str]] = []
        seen: Set[str] = set()

        # 1. Oferta de Grado
        grado_url = settings.endpoints.get("oferta_grado", f"{settings.base_url}/oferta-de-grado/")
        html_grado = self.http_client.get(grado_url)
        if html_grado:
            soup = BeautifulSoup(html_grado, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href in seen:
                    continue
                # Filtrar enlaces de carreras (ingenierias, licenciaturas, tecnologias)
                if any(href.startswith(f"{settings.base_url}/{p}") for p in ["ingenieria", "licenciatura", "tecnologia", "carrera"]):
                    if "oferta-de-grado" not in href:
                        level = "Tecnologia" if "tecnologia" in href else "Grado"
                        urls.append((href, level))
                        seen.add(href)

        # 2. Oferta de Posgrado
        posgrado_url = settings.endpoints.get("oferta_posgrado", f"{settings.base_url}/oferta-de-posgrado/")
        html_posgrado = self.http_client.get(posgrado_url)
        if html_posgrado:
            soup = BeautifulSoup(html_posgrado, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                if href in seen:
                    continue
                if any(k in href for k in ["maestria-", "doctorado-", "/doctorados/"]) and settings.base_url in href:
                    if not any(k in href for k in ["admision", "oferta-de-posgrado"]):
                        level = "Doctorado" if "doctorado" in href else "Maestria"
                        urls.append((href, level))
                        seen.add(href)

        self.logger.info(f"Identificados {len(urls)} programas academicos para analisis detallado.")
        return urls

    TAB_LABELS = {
        "perfil de ingreso", "objetivos", "perfil de egreso", "perfil profesional", "malla",
        "requisitos", "horarios", "graduacion", "contacto",
    }
    SECTION_STOPS = (
        "objetivos de la carrera", "resultados generales", "resultados especificos", "requisitos de graduacion",
        "coordinador", "personal administrativo", "unidad academica", "horario de atencion",
    )
    MAX_PROFILE_CHARS = 1000

    @staticmethod
    def _norm(line: str) -> str:
        return remove_accents(line).lower().strip().rstrip(":")

    def _content_lines(self, lines: List[str]) -> List[str]:
        """Devuelve las lineas posteriores al bloque de pestanas (PERFIL DE INGRESO ... CONTACTO)."""
        for i, line in enumerate(lines):
            if self._norm(line) == "perfil de ingreso" and i + 1 < len(lines) and self._norm(lines[i + 1]) in self.TAB_LABELS:
                j = i
                while j < len(lines) and self._norm(lines[j]) in self.TAB_LABELS:
                    j += 1
                return lines[j:]
        return []

    def _join(self, parts: List[str]) -> Any:
        text = clean_text(" ".join(p.lstrip("* ").strip() for p in parts))
        return text[: self.MAX_PROFILE_CHARS] or None

    def _extract_profiles(self, lines: List[str]) -> Tuple[Any, Any, Any]:
        """Extrae perfil de ingreso, perfil de egreso y campo ocupacional desde el contenido de la ficha.

        - Ingreso: parrafos que siguen a las pestanas, hasta el primer encabezado o vineta
          (en posgrados puede quedar incompleto si el texto continua en vinetas).
        - Egreso: solo "Resultados Generales" (grado); en posgrados no hay encabezado fiable y queda None.
        - Campo ocupacional: solo si existe un encabezado explicito; no se deduce.
        Lo que no se puede ubicar con certeza queda como None.
        """
        content = self._content_lines(lines)
        if not content:
            return None, None, None

        ingreso: List[str] = []
        k = 0
        while k < len(content):
            n = self._norm(content[k])
            if content[k].startswith("*") or any(n.startswith(st) for st in self.SECTION_STOPS):
                break
            ingreso.append(content[k])
            k += 1

        egreso: List[str] = []
        norms = [self._norm(c) for c in content]
        if "resultados generales" in norms:
            start = norms.index("resultados generales") + 1
            for line, n in zip(content[start:], norms[start:]):
                if n.startswith("resultados especificos") or n.startswith("requisitos de graduacion"):
                    break
                if re.fullmatch(r"rg\d+\.?", n):
                    continue
                egreso.append(line)
        # Posgrados: las vinetas tras el ingreso mezclan requisitos, objetivos y resultados sin
        # encabezado, por lo que no se puede afirmar cual es el perfil de egreso: queda None.

        campo: List[str] = []
        for i, n in enumerate(norms):
            if n in ("campo ocupacional", "campo laboral", "ambito laboral", "ocupacion profesional"):
                for line, nn in zip(content[i + 1:], norms[i + 1:]):
                    if any(nn.startswith(st) for st in self.SECTION_STOPS):
                        break
                    campo.append(line)
                break

        return self._join(ingreso), self._join(egreso), self._join(campo)

    def _parse_program_page(self, url: str, suggested_level: str) -> Dict[str, Any]:
        """Parsea los datos de la ficha tecnica de un programa academico.

        Args:
            url (str): URL de la carrera o maestria.
            suggested_level (str): Nivel formativo sugerido ('Grado', 'Posgrado', etc.).

        Returns:
            Dict[str, Any]: Registro de carrera con atributos curriculares.
        """
        html_content = self.http_client.get(url)
        if not html_content:
            self.logger.warning(f"Programa omitido: no se pudo obtener {url}")
            return {}

        soup = BeautifulSoup(html_content, "html.parser")
        # Las fichas de grado publican "etiqueta / valor" en lineas consecutivas (sin dos puntos)
        lines = page_lines(BeautifulSoup(html_content, "html.parser"))

        # Nombre de la carrera
        nombre = ""
        h1 = soup.find("h1")
        if h1:
            nombre = clean_text(h1.get_text())
        if not nombre:
            title = soup.title.get_text() if soup.title else ""
            nombre = clean_text(title.replace("EPN", "").replace("-", "").strip())
        if not nombre:
            nombre = url.strip("/").split("/")[-1].replace("-", " ").title()

        # Facultad de pertenencia
        facultad_nombre = ""
        campos_inferidos: List[str] = []
        known_faculties_map = {
            "sistemas": "Facultad de Ingenieria de Sistemas",
            "ciencias administrativas": "Facultad de Ciencias Administrativas",
            "ciencias": "Facultad de Ciencias",
            "civil": "Facultad de Ingenieria Civil y Ambiental",
            "electrica": "Facultad de Ingenieria Electrica y Electronica",
            "mecanica": "Facultad de Ingenieria Mecanica",
            "quimica": "Facultad de Ingenieria Quimica y Agroindustria",
            "geologia": "Facultad de Geologia y Petroleos",
            "petroleos": "Facultad de Geologia y Petroleos",
            "esfot": "Escuela de Formacion de Tecnologos",
            "tecnologos": "Escuela de Formacion de Tecnologos",
        }

        # 1. Dato publicado por el portal en la ficha ("Unidad Academica")
        facultad_nombre = extract_labeled_value(lines, "Unidad Academica")

        # 2. Si la ficha no lo publica (p. ej. maestrias), inferencia por nombre; se marca en campos_inferidos
        if not facultad_nombre:
            campos_inferidos.append("facultad")
            nombre_low = nombre.lower()
            if any(k in nombre_low for k in ["software", "computacion", "computación", "sistemas de informacion"]):
                facultad_nombre = "Facultad de Ingenieria de Sistemas"
            elif any(k in nombre_low for k in ["civil", "ambiental", "hidraulica", "recursos hidricos"]):
                facultad_nombre = "Facultad de Ingenieria Civil y Ambiental"
            elif any(k in nombre_low for k in ["electricidad", "electronica", "telecomunicacion", "ciberseguridad"]):
                facultad_nombre = "Facultad de Ingenieria Electrica y Electronica"
            elif any(k in nombre_low for k in ["mecanica", "mecatronica", "automotriz", "produccion", "materiales", "diseño"]):
                facultad_nombre = "Facultad de Ingenieria Mecanica"
            elif any(k in nombre_low for k in ["quimica", "agroindustria", "biociencias"]):
                facultad_nombre = "Facultad de Ingenieria Quimica y Agroindustria"
            elif any(k in nombre_low for k in ["geologia", "petroleos", "metalurgia"]):
                facultad_nombre = "Facultad de Geologia y Petroleos"
            elif any(k in nombre_low for k in ["administracion", "gerencia", "gestion integrados", "seguridad industrial"]):
                facultad_nombre = "Facultad de Ciencias Administrativas"
            elif any(k in nombre_low for k in ["economia", "matematica", "estadistica", "fisica"]):
                facultad_nombre = "Facultad de Ciencias"
            elif "tecnologia" in nombre_low:
                facultad_nombre = "Escuela de Formacion de Tecnologos"
            else:
                facultad_nombre = None  # No determinable: queda sin asignar en lugar de adivinar

        # Nivel de formacion
        nivel = extract_degree_level(nombre, suggested_level)

        # Modalidad, duracion, titulo y resolucion: solo si la ficha los publica
        modalidad = extract_modality(extract_labeled_value(lines, "Modalidad"))

        periodos = extract_duration_periods(extract_labeled_value(lines, "Duracion"))
        # Un periodo academico es un semestre; los anios se derivan de los periodos
        anios = round(periodos / 2.0, 1) if periodos is not None else None

        titulo_otorga = clean_text(extract_labeled_value(lines, "Titulo que otorga")) or None
        codigo_resolucion = extract_labeled_value(lines, "Resolucion de aprobacion CES")

        # Perfiles y campo ocupacional: se leen de la zona de contenido, nunca del menu ni de contenedores grandes
        perfil_ingreso, perfil_egreso, campo_ocupacional = self._extract_profiles(lines)

        # Malla curricular URL (busqueda de PDF)
        malla_url = url
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "malla" in href.lower() or href.endswith(".pdf"):
                malla_url = href if href.startswith("http") else f"{settings.base_url}{href}"
                break

        return {
            "nombre": nombre,
            "facultad_nombre": facultad_nombre,
            "nivel": nivel,
            "modalidad": modalidad,
            "duracion_periodos": periodos,
            "duracion_anios": anios,
            "creditos": None,  # no se publica en la ficha; antes se estimaba por nivel
            "titulo_otorga": titulo_otorga,
            "codigo_resolucion": codigo_resolucion,
            "perfil_ingreso": perfil_ingreso,
            "perfil_egreso": perfil_egreso,
            "campo_ocupacional": campo_ocupacional,
            "malla_curricular_url": malla_url,
            "url": url,
            "campos_inferidos": ",".join(campos_inferidos) or None,
        }

    def extract(self) -> List[Dict[str, Any]]:
        """Extrae el catalogo unificado de carreras y posgrados de la institucion.

        Returns:
            List[Dict[str, Any]]: Lista estructurada de programas formativos.
        """
        urls_with_level = self._discover_program_urls()
        programs = []

        for url, suggested_level in urls_with_level:
            self.logger.info(f"Parseando programa: {url}")
            data = self._parse_program_page(url, suggested_level)
            if data:
                programs.append(data)

        return programs
