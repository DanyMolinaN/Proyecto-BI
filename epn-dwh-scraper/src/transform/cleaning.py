"""
Modulo de limpieza, normalizacion y modelado dimensional de datos.

Implementa transformaciones de calidad sobre los datos intermedios: tratamiento de nulos,
eliminacion de duplicados, correccion de codificaciones, construccion de claves
sustitutas y generacion de DataFrames estructurados segun el esquema dimensional estrella.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple
import pandas as pd

from src.utils.helpers import clean_text, generate_surrogate_key
from src.utils.logger import setup_logger

logger = setup_logger("cleaning")


class DataCleaner:
    """Transformador de colecciones crudas a entidades dimensionales normalizadas."""

    def __init__(self) -> None:
        """Inicializa estructuras y catalogos maestros de referencia."""
        self.reference_date = datetime.now()

    def build_dim_tiempo(self, start_year: int = 2023, end_year: int = 2027) -> pd.DataFrame:
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

        # Normalizacion de cadenas
        for col in ["nombre", "sigla", "decano", "subdecano", "descripcion", "mision", "vision", "url", "contacto_correo", "contacto_telefono", "ubicacion_campus"]:
            if col in df.columns:
                df[col] = df[col].apply(clean_text)
            else:
                df[col] = "No especificado"

        # Imputacion de nulos
        df["decano"] = df["decano"].replace("", "No especificado")
        df["subdecano"] = df["subdecano"].replace("", "No especificado")
        df["contacto_correo"] = df["contacto_correo"].replace("", "contacto@epn.edu.ec")

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

        # Normalizacion de textos
        text_cols = ["nombre", "facultad_nombre", "nivel", "modalidad", "titulo_otorga", "codigo_resolucion", "perfil_ingreso", "perfil_egreso", "campo_ocupacional", "url"]
        for c in text_cols:
            if c in df.columns:
                df[c] = df[c].apply(clean_text)
            else:
                df[c] = "No especificado"

        # Eliminacion de duplicados por nombre de carrera
        df["nombre_norm"] = df["nombre"].str.lower()
        df.drop_duplicates(subset=["nombre_norm"], inplace=True)
        df.drop(columns=["nombre_norm"], inplace=True)

        # Validacion de periodos y creditos
        df["duracion_periodos"] = pd.to_numeric(df["duracion_periodos"], errors="coerce").fillna(9).astype(int)
        df["duracion_anios"] = pd.to_numeric(df["duracion_anios"], errors="coerce").fillna(4.5).astype(float)
        df["creditos"] = pd.to_numeric(df["creditos"], errors="coerce").fillna(120).astype(int)

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
            "malla_curricular_url", "url"
        ]].copy().rename(columns={"nombre": "nombre_carrera", "url": "url_carrera"})

        # Mapeo de FKs hacia facultades de forma precisa
        def map_facultad_key(raw_fac_name: str) -> int:
            if not df_facultades.empty:
                raw_norm = clean_text(raw_fac_name).lower()
                # 1. Coincidencia por nombre completo o palabras clave principales
                for _, fac_row in sorted(df_facultades.iterrows(), key=lambda r: len(r[1]["nombre"]), reverse=True):
                    fac_norm = clean_text(fac_row["nombre"]).lower()
                    if fac_norm in raw_norm or raw_norm in fac_norm:
                        return fac_row["facultad_key"]

                # 2. Coincidencia por sigla exacta con límites de palabra
                for _, fac_row in df_facultades.iterrows():
                    sigla = fac_row["sigla"].lower()
                    if re.search(r"\b" + re.escape(sigla) + r"\b", raw_norm):
                        return fac_row["facultad_key"]

                return df_facultades.iloc[0]["facultad_key"]
            return generate_surrogate_key("facultad", "EPN")

        df["facultad_key"] = df["facultad_nombre"].apply(map_facultad_key)
        df["nivel_key"] = df["nivel"].apply(lambda n: generate_surrogate_key("nivel", n))
        df["modalidad_key"] = df["modalidad"].apply(lambda m: generate_surrogate_key("modalidad", m))

        # 4. Tabla de Hechos Oferta Academica
        current_time_key = int(datetime.now().strftime("%Y%m%d"))
        df["oferta_key"] = df.apply(lambda r: generate_surrogate_key("oferta", r["carrera_key"], r["facultad_key"]), axis=1)
        df["tiempo_extraccion_key"] = current_time_key
        df["es_acreditada"] = 1

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

        # Limpieza textual
        for col in ["nombre_completo", "titulo_academico", "cargo", "tipo_cargo", "unidad_adscripcion", "periodo_gestion", "correo_contacto", "biografia", "fuente_url"]:
            if col in df.columns:
                df[col] = df[col].apply(clean_text)
            else:
                df[col] = "No especificado"

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
        df["es_vigente"] = 1
        df["fecha_inicio_vigencia"] = "2023-11-01"
        df["fecha_fin_vigencia"] = "9999-12-31"

        df_dim_autoridad = df[[
            "autoridad_key", "nombre_completo", "titulo_academico",
            "correo_contacto", "biografia", "es_vigente",
            "fecha_inicio_vigencia", "fecha_fin_vigencia"
        ]].copy()

        # 3. Mapeo a facultades para la tabla de hechos
        def map_facultad_key(raw_unidad: str) -> int:
            if not df_facultades.empty:
                raw_norm = clean_text(raw_unidad).lower()
                for _, fac_row in sorted(df_facultades.iterrows(), key=lambda r: len(r[1]["nombre"]), reverse=True):
                    fac_norm = clean_text(fac_row["nombre"]).lower()
                    if fac_norm in raw_norm or raw_norm in fac_norm:
                        return fac_row["facultad_key"]

                for _, fac_row in df_facultades.iterrows():
                    sigla = fac_row["sigla"].lower()
                    if re.search(r"\b" + re.escape(sigla) + r"\b", raw_norm):
                        return fac_row["facultad_key"]

                return df_facultades.iloc[0]["facultad_key"]
            return generate_surrogate_key("facultad", "EPN")

        df["facultad_key"] = df["unidad_adscripcion"].apply(map_facultad_key)
        df["cargo_key"] = df["cargo"].apply(lambda c: generate_surrogate_key("cargo", c))
        df["designacion_key"] = df.apply(lambda r: generate_surrogate_key("designacion", r["autoridad_key"], r["cargo_key"]), axis=1)
        df["tiempo_designacion_key"] = 20231101
        df["es_titular"] = pd.to_numeric(df["es_titular"], errors="coerce").fillna(1).astype(int)

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

        for col in ["post_id", "fecha_publicacion", "titulo", "categoria", "resumen", "url"]:
            if col in df.columns:
                df[col] = df[col].apply(clean_text)
            else:
                df[col] = ""

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
        def parse_date_key(d_str: str) -> int:
            try:
                dt = datetime.strptime(d_str[:10], "%Y-%m-%d")
                return int(dt.strftime("%Y%m%d"))
            except Exception:
                return int(datetime.now().strftime("%Y%m%d"))

        df["tiempo_publicacion_key"] = df["fecha_publicacion"].apply(parse_date_key)
        df["categoria_key"] = df["categoria"].apply(lambda c: generate_surrogate_key("categoria_noticia", c))
        df["noticia_key"] = df["url"].apply(lambda u: generate_surrogate_key("noticia", u))
        df["longitud_caracteres"] = df["resumen"].str.len()
        df["conteo_palabras"] = df["resumen"].apply(lambda t: len(t.split()))

        df_fact_comunicacion = df[[
            "noticia_key", "categoria_key", "tiempo_publicacion_key",
            "titulo", "longitud_caracteres", "conteo_palabras", "url"
        ]].copy()

        return df_dim_categoria, df_fact_comunicacion
