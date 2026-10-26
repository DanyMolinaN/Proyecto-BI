"""
Funciones auxiliares para transformacion textual, extraccion y normalizacion.

Contiene utilidades de procesamiento de texto, extraccion mediante expresiones
regulares y generacion de identificadores deterministas.
"""

import hashlib
import html
import re
import unicodedata
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


def extract_modality(text: Optional[str]) -> str:
    """Identifica la modalidad de estudio a partir del texto del programa.

    Args:
        text (Optional[str]): Texto descriptivo o campo de modalidad.

    Returns:
        str: Modalidad estandar ('Presencial', 'Semipresencial', 'En Linea', 'Dual', 'Hibrida').
    """
    if not text:
        return "Presencial"
    t_lower = text.lower()
    if "dual" in t_lower:
        return "Dual"
    if "linea" in t_lower or "línea" in t_lower or "virtual" in t_lower:
        return "En Linea"
    if "semipresencial" in t_lower:
        return "Semipresencial"
    if "hibrid" in t_lower:
        return "Hibrida"
    return "Presencial"


def generate_surrogate_key(*args: Any) -> int:
    """Genera una clave sustituta determinista entera a partir de atributos clave.

    Utiliza una funcion hash SHA-256 convertida a entero de 64 bits para garantizar
    idempotencia en la generacion de llaves dimensionales.

    Args:
        *args: Valores o atributos componentes de la clave natural.

    Returns:
        int: Clave sustituta determinista no negativa.
    """
    payload = "|".join(str(a or "").strip().lower() for a in args)
    hash_obj = hashlib.sha256(payload.encode("utf-8"))
    # Entero positivo acotado a 63 bits para compatibilidad SQL INTEGER
    return int(hash_obj.hexdigest()[:14], 16)
