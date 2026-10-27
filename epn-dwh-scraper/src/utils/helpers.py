"""
Funciones auxiliares para transformacion textual, extraccion y normalizacion.

Contiene utilidades de procesamiento de texto, extraccion mediante expresiones
regulares y generacion de identificadores deterministas.
"""

import hashlib
import html
import re
import unicodedata
import pandas as pd
from typing import Any, Optional


def clean_text(text: Optional[str]) -> str:
    """Limpia cadenas de texto eliminando saltos de linea redundantes y espacios extras.

    Args:
        text (Optional[str]): Cadena original a normalizar.

    Returns:
        str: Cadena limpia sin espacios dobles ni caracteres de escape sueltos.
    """
    if not text:
        return ""
    # Decodificar entidades HTML (&amp;, &#8211;, etc.)
    decoded = html.unescape(text)
    # Reemplazar caracteres especiales de espacio
    normalized = decoded.replace("\xa0", " ").replace("\u200b", " ")
    # Colapsar espacios continuos y saltos de linea
    cleaned = re.sub(r"\s+", " ", normalized)
    return cleaned.strip()


def remove_accents(text: str) -> str:
    """Remueve tildes y diacriticos manteniendo caracteres base legibles.

    Args:
        text (str): Cadena con posibles tildes.

    Returns:
        str: Cadena con caracteres sin diacriticos.
    """
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def extract_email(text: Optional[str]) -> Optional[str]:
    """Extrae la primera direccion de correo electronico valida encontrada en el texto.

    Args:
        text (Optional[str]): Texto donde buscar la direccion de correo.

    Returns:
        Optional[str]: Direccion de correo electronico en minusculas o None.
    """
    if not text:
        return None
    match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    if match:
        return match.group(0).lower().strip()
    return None


def extract_phone(text: Optional[str]) -> Optional[str]:
    """Normaliza y extrae un numero telefonico ecuatoriano a formato estandar.

    Args:
        text (Optional[str]): Cadena de texto con informacion telefonica.

    Returns:
        Optional[str]: Numero telefonico estandarizado o None.
    """
    if not text:
        return None
    # Patron comun para telefonos en EPN: (+593) 2 2976 300 o PBX
    match = re.search(r"(\+?593[\s\d\(\)-]{7,18}|\(?02\)?[\s\d-]{7,12}|\b2976\s*300\b)", text)
    if match:
        clean = re.sub(r"[^\d+]", " ", match.group(0))
        return re.sub(r"\s+", " ", clean).strip()
    return None


_NUMBER_WORDS = {
    "uno": 1, "un": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6, "siete": 7,
    "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12, "trece": 13, "catorce": 14,
}


def page_lines(soup: Any) -> list:
    """Devuelve las lineas de texto visibles de una pagina (sin scripts ni estilos), una por elemento."""
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return [ln.strip() for ln in soup.get_text("\n").splitlines() if ln.strip()]


def extract_labeled_value(lines: list, *labels: str) -> Optional[str]:
    """Busca el valor de una ficha "etiqueta / valor".

    Soporta ambos formatos del portal: la etiqueta en una linea y el valor en la siguiente
    ("Duracion" / "Nueve (9) periodos") o ambos en la misma linea ("Duracion: 9 periodos").

    Args:
        lines (list): Lineas de texto de la pagina.
        *labels (str): Etiquetas aceptadas (sin tildes ni mayusculas relevantes).

    Returns:
        Optional[str]: Valor encontrado o None.
    """
    wanted = [remove_accents(lb).lower().rstrip(":") for lb in labels]
    for i, line in enumerate(lines):
        norm = remove_accents(line).lower()
        for lb in wanted:
            if norm.rstrip(":").strip() == lb and i + 1 < len(lines):
                return lines[i + 1]
            if norm.startswith(lb + ":") and len(line) > len(lb) + 1:
                value = line.split(":", 1)[1].strip()
                if value:
                    return value
    return None


def extract_duration_periods(text: Optional[str]) -> Optional[int]:
    """Extrae el numero de semestres o periodos academicos indicados en texto.

    Args:
        text (Optional[str]): Cadena con la descripcion de la duracion (ej: 'Nueve (9) periodos').

    Returns:
        Optional[int]: Cantidad entera de periodos academicos, o None.
    """
    if not text:
        return None
    match = re.search(r"\(?(\d{1,2})\)?\s*(semestres|periodos|períodos|niveles)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # Numero escrito con palabras: "Nueve periodos academicos"
    word = re.search(r"\b(" + "|".join(_NUMBER_WORDS) + r")\b\s*(?:\(\d+\)\s*)?(semestres|periodos|períodos|niveles)", text.lower())
    if word:
        return _NUMBER_WORDS[word.group(1).lower()]
    
    # Busqueda secundaria solo del digito si la cadena es corta
    digits = re.findall(r"\b(\d{1,2})\b", text)
    if digits:
        val = int(digits[0])
        if 1 <= val <= 14:
            return val
    return None


def extract_degree_level(career_name: str, raw_level: Optional[str] = None) -> str:
    """Clasifica el nivel de formacion academica segun el nombre de la carrera.

    Args:
        career_name (str): Nombre del programa academico.
        raw_level (Optional[str], optional): Nivel reportado en la pagina.

    Returns:
        str: Nivel normalizado ('Tecnologia', 'Grado', 'Maestria', 'Doctorado').
    """
    name_lower = career_name.lower()
    if raw_level:
        raw_lower = raw_level.lower()
        if "doctor" in raw_lower:
            return "Doctorado"
        if "maestr" in raw_lower or "posgrado" in raw_lower:
            return "Maestria"
        if "tecnol" in raw_lower:
            return "Tecnologia"

    if "doctorado" in name_lower or "phd" in name_lower:
        return "Doctorado"
    if "maestr" in name_lower or "master" in name_lower:
        return "Maestria"
    if "tecnolog" in name_lower or "tecnico" in name_lower:
        return "Tecnologia"
    return "Grado"


def extract_modality(text: Optional[str]) -> Optional[str]:
    """Identifica la modalidad de estudio a partir del texto del programa.

    Args:
        text (Optional[str]): Texto descriptivo o campo de modalidad.

    Returns:
        Optional[str]: Modalidad estandar ('Presencial', 'Semipresencial', 'En Linea', 'Dual', 'Hibrida')
        o None si el texto no la menciona.
    """
    if not text:
        return None
    t_lower = text.lower()
    if "dual" in t_lower:
        return "Dual"
    if "linea" in t_lower or "línea" in t_lower or "virtual" in t_lower:
        return "En Linea"
    if "semipresencial" in t_lower:
        return "Semipresencial"
    if "hibrid" in t_lower:
        return "Hibrida"
    if "presencial" in t_lower:
        return "Presencial"
    return None


def generate_surrogate_key(*args: Any) -> int:
    """Genera una clave sustituta determinista entera a partir de atributos clave.

    Utiliza una funcion hash SHA-256 convertida a entero de 64 bits para garantizar
    idempotencia en la generacion de llaves dimensionales.

    Args:
        *args: Valores o atributos componentes de la clave natural.

    Returns:
        int: Clave sustituta determinista no negativa.
    """
    # Los valores nulos (None, NaN, pd.NA) se tratan como cadena vacia
    payload = "|".join("" if (a is None or pd.isna(a)) else str(a).strip().lower() for a in args)
    hash_obj = hashlib.sha256(payload.encode("utf-8"))
    # Entero positivo acotado a 63 bits para compatibilidad SQL INTEGER
    return int(hash_obj.hexdigest()[:14], 16)
