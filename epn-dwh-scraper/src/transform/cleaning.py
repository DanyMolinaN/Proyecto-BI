"""
Modulo de limpieza, normalizacion y modelado dimensional de datos.

Implementa transformaciones de calidad sobre los datos intermedios: tratamiento de nulos,
eliminacion de duplicados, correccion de codificaciones, construccion de claves
sustitutas y generacion de DataFrames estructurados segun el esquema dimensional estrella.
"""

import difflib
import re
from datetime import datetime
from typing import Any, Dict, List, Tuple
import pandas as pd

from src.utils.helpers import clean_text, generate_surrogate_key, remove_accents
from src.utils.logger import setup_logger

logger = setup_logger("cleaning")


def _text_or_none(value: Any) -> Any:
    """Normaliza texto y devuelve None cuando no hay dato (nunca se inventa un valor)."""
    return clean_text(value) or None


def _clean_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Aplica limpieza textual; las columnas ausentes o vacias quedan como NULL."""
    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(_text_or_none)
        else:
            df[col] = None
    return df


def _to_int64(values: Any) -> pd.Series:
    """Convierte a Int64 nullable sin pasar por float64 (las claves hash de 56 bits perderian precision)."""
    return pd.Series(pd.array([None if (v is None or pd.isna(v)) else int(v) for v in values], dtype="Int64"))


def _match_facultad_key(raw_name: Any, df_facultades: pd.DataFrame) -> Any:
    """Resuelve la clave de facultad por nombre o sigla; devuelve None si no hay coincidencia.

    La comparacion ignora tildes y mayusculas, y admite variaciones menores de redaccion
    (ej: "Facultad de Geologia y Petroleos" vs "Facultad de Ingenieria Geologia y Petroleos").
    """
    raw_norm = remove_accents(clean_text(raw_name)).lower()
    if not raw_norm or df_facultades.empty:
        return None
    names = {
        fac_row["facultad_key"]: remove_accents(clean_text(fac_row["nombre"])).lower()
        for _, fac_row in df_facultades.iterrows()
    }
    for key, fac_norm in sorted(names.items(), key=lambda kv: len(kv[1]), reverse=True):
        if fac_norm and (fac_norm in raw_norm or raw_norm in fac_norm):
            return key
    for _, fac_row in df_facultades.iterrows():
        sigla = clean_text(fac_row["sigla"]).lower()
        if sigla and re.search(r"\b" + re.escape(sigla) + r"\b", raw_norm):
            return fac_row["facultad_key"]
    close = difflib.get_close_matches(raw_norm, list(names.values()), n=1, cutoff=0.8)
    if close:
        return next(k for k, v in names.items() if v == close[0])
    return None


class DataCleaner:
    """Transformador de colecciones crudas a entidades dimensionales normalizadas."""

    def __init__(self) -> None:
        """Inicializa estructuras y catalogos maestros de referencia."""
        self.reference_date = datetime.now()

    def build_dim_tiempo(self, start_year: int = 2015, end_year: int = 2035) -> pd.DataFrame:
        """Genera la dimension tiempo con granularidad diaria y atributos de calendario academico.

        Args:
            start_year (int): Anio inicial del periodo temporal.
            end_year (int): Anio final del periodo temporal.

        Returns:
            pd.DataFrame: Dimension tiempo estructurada para BI.
        """
        dates = pd.date_range(start=f"{start_year}-01-01", end=f"{end_year}-12-31", freq="D")
        records = []
        month_names = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
            5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
            9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }

        for dt in dates:
            time_key = int(dt.strftime("%Y%m%d"))
            records.append({
                "tiempo_key": time_key,
                "fecha": dt.strftime("%Y-%m-%d"),
                "anio": dt.year,
                "mes": dt.month,
                "mes_nombre": month_names[dt.month],
                "trimestre": (dt.month - 1) // 3 + 1,
                "semestre": 1 if dt.month <= 6 else 2,
                "dia": dt.day,
                "dia_semana": dt.strftime("%A"),
                "es_fin_de_semana": 1 if dt.weekday() >= 5 else 0,
            })

        df = pd.DataFrame(records)
        df.drop_duplicates(subset=["tiempo_key"], inplace=True)
        return df

    def clean_facultades(self, raw_facultades: List[Dict[str, Any]]) -> pd.DataFrame:
        """Limpia y estructura la dimension de facultades y unidades academicas.

        Args:
            raw_facultades (List[Dict[str, Any]]): Lista de diccionarios parseados.

        Returns:
            pd.DataFrame: DataFrame de dim_facultad con claves sustitutas deterministas.
        """
        if not raw_facultades:
            return pd.DataFrame()

        df = pd.DataFrame(raw_facultades)

        # Normalizacion de cadenas; lo ausente queda NULL
        df = _clean_columns(df, ["nombre", "sigla", "decano", "subdecano", "descripcion", "mision", "vision", "url", "departamentos_adscritos", "contacto_correo", "contacto_telefono", "ubicacion_campus"])

        # Eliminacion de duplicados por nombre normalizado
        df["nombre_norm"] = df["nombre"].str.lower()
        df.drop_duplicates(subset=["nombre_norm"], inplace=True)
        df.drop(columns=["nombre_norm"], inplace=True)

        # Generacion de clave sustituta
        df["facultad_key"] = df["sigla"].apply(lambda s: generate_surrogate_key("facultad", s))

        # Reordenamiento
        columns_order = [
            "facultad_key", "nombre", "sigla", "decano", "subdecano",
            "descripcion", "mision", "vision", "url", "departamentos_adscritos",
            "contacto_correo", "contacto_telefono", "ubicacion_campus"
        ]
        available_cols = [c for c in columns_order if c in df.columns]
        return df[available_cols].reset_index(drop=True)

    def clean_carreras(self, raw_carreras: List[Dict[str, Any]], df_facultades: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Limpia y desacopla la oferta academica en dimensiones y tabla de hechos.

        Args:
            raw_carreras (List[Dict[str, Any]]): Catalogo crudo de programas.
            df_facultades (pd.DataFrame): Dimension facultades para resolución de claves foraneas.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
                (dim_carrera, dim_nivel_formacion, dim_modalidad, fact_oferta_academica)
        """
        if not raw_carreras:
            empty_df = pd.DataFrame()
            return empty_df, empty_df, empty_df, empty_df

        df = pd.DataFrame(raw_carreras)

        # Normalizacion de textos; lo ausente queda NULL
        df = _clean_columns(df, ["nombre", "facultad_nombre", "nivel", "modalidad", "titulo_otorga", "codigo_resolucion", "perfil_ingreso", "perfil_egreso", "campo_ocupacional", "url", "malla_curricular_url", "campos_inferidos"])
        # Nivel y modalidad son claves de dimension: se usa un miembro explicito "No especificado"
        df["nivel"] = df["nivel"].fillna("No especificado")
        df["modalidad"] = df["modalidad"].fillna("No especificado")

        # Eliminacion de duplicados por nombre de carrera
        df["nombre_norm"] = df["nombre"].str.lower()
        df.drop_duplicates(subset=["nombre_norm"], inplace=True)
        df.drop(columns=["nombre_norm"], inplace=True)

        # Metricas: se convierten a numerico y lo faltante queda NULL (sin valores por defecto)
        df["duracion_periodos"] = pd.to_numeric(df["duracion_periodos"] if "duracion_periodos" in df.columns else pd.Series([None] * len(df)), errors="coerce").astype("Int64")
        df["duracion_anios"] = pd.to_numeric(df["duracion_anios"] if "duracion_anios" in df.columns else pd.Series([None] * len(df)), errors="coerce").astype("float64")
        df["creditos"] = pd.to_numeric(df["creditos"] if "creditos" in df.columns else pd.Series([None] * len(df)), errors="coerce").astype("Int64")

        # 1. Dimension Nivel de Formacion
        niveles_unicos = df["nivel"].unique()
        niveles_data = []
        for n in niveles_unicos:
            niveles_data.append({
                "nivel_key": generate_surrogate_key("nivel", n),
                "codigo_nivel": n[:3].upper(),
                "nombre_nivel": n,
                "ciclo_academico": "Cuarto Nivel" if n in ["Maestria", "Doctorado"] else "Tercer Nivel",
            })
        df_dim_nivel = pd.DataFrame(niveles_data)

        # 2. Dimension Modalidad
        modalidades_unicas = df["modalidad"].unique()
        modalidades_data = []
        for m in modalidades_unicas:
            modalidades_data.append({
                "modalidad_key": generate_surrogate_key("modalidad", m),
                "nombre_modalidad": m,
                "descripcion": f"Estudios en modalidad {m} aprobada por el CES.",
            })
        df_dim_modalidad = pd.DataFrame(modalidades_data)

        # 3. Dimension Carrera
        df["carrera_key"] = df["nombre"].apply(lambda n: generate_surrogate_key("carrera", n))
        df_dim_carrera = df[[
            "carrera_key", "nombre", "titulo_otorga", "codigo_resolucion",
            "perfil_ingreso", "perfil_egreso", "campo_ocupacional",
            "malla_curricular_url", "url", "campos_inferidos"
        ]].copy().rename(columns={"nombre": "nombre_carrera", "url": "url_carrera"})

        # Mapeo de FKs hacia facultades; sin coincidencia queda NULL (se reporta en validacion)
        df["facultad_key"] = _to_int64([_match_facultad_key(n, df_facultades) for n in df["facultad_nombre"]]).values
        df["nivel_key"] = df["nivel"].apply(lambda n: generate_surrogate_key("nivel", n))
        df["modalidad_key"] = df["modalidad"].apply(lambda m: generate_surrogate_key("modalidad", m))

        # 4. Tabla de Hechos Oferta Academica
        current_time_key = int(datetime.now().strftime("%Y%m%d"))
        df["oferta_key"] = df.apply(lambda r: generate_surrogate_key("oferta", r["carrera_key"], r["facultad_key"]), axis=1)
        df["tiempo_extraccion_key"] = current_time_key
        # La acreditacion no se extrae del portal: se deja NULL hasta contar con una fuente
        df["es_acreditada"] = pd.Series([pd.NA] * len(df), dtype="Int64")

        df_fact_oferta = df[[
            "oferta_key", "carrera_key", "facultad_key", "nivel_key",
            "modalidad_key", "tiempo_extraccion_key", "duracion_periodos",
            "duracion_anios", "creditos", "es_acreditada"
        ]].copy().rename(columns={"creditos": "creditos_totales"})

        return df_dim_carrera, df_dim_nivel, df_dim_modalidad, df_fact_oferta

    def clean_autoridades(self, raw_autoridades: List[Dict[str, Any]], df_facultades: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Limpia autoridades, clasifica cargos y construye tabla de hechos de autoridades.

        Args:
            raw_autoridades (List[Dict[str, Any]]): Registros en bruto de directivos.
            df_facultades (pd.DataFrame): Dimension facultades para relacion institucional.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
                (dim_autoridad, dim_cargo, fact_designacion_autoridades)
        """
        if not raw_autoridades:
            empty = pd.DataFrame()
            return empty, empty, empty

        df = pd.DataFrame(raw_autoridades)

        df = _clean_columns(df, ["nombre_completo", "titulo_academico", "cargo", "tipo_cargo", "unidad_adscripcion", "periodo_gestion", "correo_contacto", "biografia", "fuente_url"])
        df = df[df["nombre_completo"].notna() & df["cargo"].notna()]

        # Eliminacion de duplicados
        df["nombre_norm"] = df["nombre_completo"].str.lower()
        df.drop_duplicates(subset=["nombre_norm"], inplace=True)
        df.drop(columns=["nombre_norm"], inplace=True)

        # 1. Dimension Cargo
        cargos_unicos = df["cargo"].unique()
        cargos_data = []
        for c in cargos_unicos:
            tipo = "Gobierno Central" if any(k in c.lower() for k in ["rector", "vicerrector"]) else "Direccion de Facultad"
            cargos_data.append({
                "cargo_key": generate_surrogate_key("cargo", c),
                "nombre_cargo": c,
                "tipo_gobierno": tipo,
            })
        df_dim_cargo = pd.DataFrame(cargos_data)

        # 2. Dimension Autoridad (con atributos SCD Tipo 2 para auditoria historica)
        df["autoridad_key"] = df["nombre_completo"].apply(lambda n: generate_surrogate_key("autoridad", n))
        # El portal no publica la fecha de posesion: la vigencia inicia en la primera captura.
        # El historial real se construye en transform/scd2.py comparando contra lo ya cargado.
        df["es_vigente"] = 1
        df["fecha_inicio_vigencia"] = self.reference_date.strftime("%Y-%m-%d")
        df["fecha_fin_vigencia"] = "9999-12-31"

        df_dim_autoridad = df[[
            "autoridad_key", "nombre_completo", "titulo_academico",
            "correo_contacto", "biografia", "es_vigente",
            "fecha_inicio_vigencia", "fecha_fin_vigencia"
        ]].copy()

        # 3. Mapeo a facultades: las autoridades centrales (Rectorado) no pertenecen a una facultad
        df["facultad_key"] = _to_int64([_match_facultad_key(u, df_facultades) for u in df["unidad_adscripcion"]]).values
        df["cargo_key"] = df["cargo"].apply(lambda c: generate_surrogate_key("cargo", c))
        df["designacion_key"] = df.apply(lambda r: generate_surrogate_key("designacion", r["autoridad_key"], r["cargo_key"]), axis=1)
        # Fecha de captura: el portal no indica la fecha de designacion
        df["tiempo_designacion_key"] = int(self.reference_date.strftime("%Y%m%d"))
        df["es_titular"] = pd.to_numeric(df["es_titular"], errors="coerce").astype("Int64")

        df_fact_autoridades = df[[
            "designacion_key", "autoridad_key", "cargo_key", "facultad_key",
            "es_titular", "tiempo_designacion_key"
        ]].copy()

        return df_dim_autoridad, df_dim_cargo, df_fact_autoridades

    def clean_noticias(self, raw_noticias: List[Dict[str, Any]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Estructura las categorias de noticias y la tabla de hechos de comunicacion.

        Args:
            raw_noticias (List[Dict[str, Any]]): Novedades y publicaciones crudas.

        Returns:
            Tuple[pd.DataFrame, pd.DataFrame]: (dim_categoria_noticia, fact_comunicacion_institucional)
        """
        if not raw_noticias:
            empty = pd.DataFrame()
            return empty, empty

        df = pd.DataFrame(raw_noticias)

        df = _clean_columns(df, ["post_id", "fecha_publicacion", "titulo", "categoria", "resumen", "url"])
        df = df[df["url"].notna()]
        df["categoria"] = df["categoria"].fillna("Sin categoria")
        df["resumen"] = df["resumen"].fillna("")

        # Evitar duplicados por post_id o url
        df.drop_duplicates(subset=["url"], inplace=True)

        # 1. Dimension Categoria Noticia
        categorias_unicas = df["categoria"].unique()
        cat_data = []
        for cat in categorias_unicas:
            cat_data.append({
                "categoria_key": generate_surrogate_key("categoria_noticia", cat),
                "nombre_categoria": cat,
            })
        df_dim_categoria = pd.DataFrame(cat_data)

        # 2. Fact Comunicacion Institucional
        def parse_date_key(d_str: Any) -> Any:
            try:
                dt = datetime.strptime(str(d_str)[:10], "%Y-%m-%d")
                return int(dt.strftime("%Y%m%d"))
            except Exception:
                return None  # fecha ilegible: NULL en lugar de usar la fecha de hoy

        df["tiempo_publicacion_key"] = _to_int64([parse_date_key(d) for d in df["fecha_publicacion"]]).values
        df["categoria_key"] = df["categoria"].apply(lambda c: generate_surrogate_key("categoria_noticia", c))
        df["noticia_key"] = df["url"].apply(lambda u: generate_surrogate_key("noticia", u))
        df["longitud_caracteres"] = df["resumen"].str.len()
        df["conteo_palabras"] = df["resumen"].apply(lambda t: len(t.split()))

        df_fact_comunicacion = df[[
            "noticia_key", "categoria_key", "tiempo_publicacion_key",
            "titulo", "longitud_caracteres", "conteo_palabras", "url"
        ]].copy()

        return df_dim_categoria, df_fact_comunicacion
