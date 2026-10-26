"""
Orquestador principal por linea de comandos (CLI) del pipeline ETL institucional de la EPN.

Coordina la ejecucion modular o integral de las fases de Extraccion (scrapers),
Transformacion (limpieza, enriquecimiento y aseguramiento de calidad) y
Carga (almacenamiento en CSV y base de datos relacional del Data Warehouse).
"""

import argparse
import sys
from pathlib import Path
from typing import Dict
import pandas as pd

from src.config import settings
from src.load.to_csv import CsvLoader
from src.load.to_database import DatabaseLoader
from src.scrapers.autoridades_scraper import AutoridadesScraper
from src.scrapers.carreras_scraper import CarrerasScraper
from src.scrapers.facultades_scraper import FacultadesScraper
from src.scrapers.institucional_scraper import InstitucionalScraper
from src.scrapers.noticias_scraper import NoticiasScraper
from src.transform.cleaning import DataCleaner
from src.transform.validation import DataValidator
from src.utils.http_client import HttpClient
from src.utils.logger import setup_logger

logger = setup_logger("orchestrator")


class ETLPipeline:
    """Gestiona el flujo integral de datos desde el portal web hasta el Data Warehouse."""

    def __init__(self, use_cache: bool = True, force_refresh: bool = False) -> None:
        """Inicializa los componentes del pipeline con las directivas de ejecucion.

        Args:
            use_cache (bool): Si es True, utiliza la cache de archivos HTML/JSON en data/raw.
            force_refresh (bool): Si es True, fuerza la descarga remota de todas las paginas.
        """
        self.use_cache = use_cache
        self.force_refresh = force_refresh
        self.http_client = HttpClient()
        self.cleaner = DataCleaner()
        self.validator = DataValidator()
        self.csv_loader = CsvLoader()
        self.db_loader = DatabaseLoader()

    def run_scrapers(self, modules: list[str]) -> Dict[str, list]:
        """Ejecuta los extractores web solicitados y almacena su resultado en data/interim/.

        Args:
            modules (list[str]): Lista de modulos a ejecutar ('facultades', 'carreras', etc.).

        Returns:
            Dict[str, list]: Datos crudos extraidos por cada modulo.
        """
        logger.info(f"Iniciando fase de extraccion para modulos: {', '.join(modules)}")
        raw_data = {}

        if "facultades" in modules:
            scraper = FacultadesScraper(self.http_client)
            raw_data["facultades"] = scraper.run()

        if "carreras" in modules:
            scraper = CarrerasScraper(self.http_client)
            raw_data["carreras"] = scraper.run()

        if "autoridades" in modules:
            scraper = AutoridadesScraper(self.http_client)
            raw_data["autoridades"] = scraper.run()

        if "institucional" in modules:
            scraper = InstitucionalScraper(self.http_client)
            raw_data["institucional"] = scraper.run()

        if "noticias" in modules:
            scraper = NoticiasScraper(self.http_client)
            raw_data["noticias"] = scraper.run()

        return raw_data

    def load_interim_from_disk(self) -> Dict[str, list]:
        """Carga datos de la etapa intermedia desde disco si la extraccion ya se ejecuto.

        Returns:
            Dict[str, list]: Diccionarios recuperados de data/interim/.
        """
        import json
        raw_data = {}
        for mod in ["facultades", "carreras", "autoridades", "institucional", "noticias"]:
            path = settings.data_interim_dir / f"{mod}scraper.json"
            if path.exists():
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        raw_data[mod] = json.load(f)
                except Exception as exc:
                    logger.warning(f"Error al leer interim para {mod}: {exc}")
        return raw_data

    def transform(self, raw_data: Dict[str, list]) -> Dict[str, pd.DataFrame]:
        """Ejecuta las reglas de limpieza, normalizacion y perfilamiento dimensional.

        Args:
            raw_data (Dict[str, list]): Colecciones parseadas en bruto.

        Returns:
            Dict[str, pd.DataFrame]: Conjunto de dimensiones y tablas de hechos estructuradas.
        """
        logger.info("Iniciando fase de transformacion y modelado dimensional...")
        tables: Dict[str, pd.DataFrame] = {}

        # 1. Dimension Tiempo
        df_dim_tiempo = self.cleaner.build_dim_tiempo(2023, 2027)
        tables["dim_tiempo"] = df_dim_tiempo
        self.validator.profile_dataframe(df_dim_tiempo, "dim_tiempo", "tiempo_key", ["tiempo_key", "fecha", "anio"])

        # 2. Dimension Facultades
        raw_fac = raw_data.get("facultades", [])
        df_dim_facultad = self.cleaner.clean_facultades(raw_fac)
        tables["dim_facultad"] = df_dim_facultad
        self.validator.profile_dataframe(df_dim_facultad, "dim_facultad", "facultad_key", ["facultad_key", "nombre", "sigla"])

        # 3. Carreras, Niveles, Modalidad y Hechos Oferta Academica
        raw_car = raw_data.get("carreras", [])
        df_dim_car, df_dim_niv, df_dim_mod, df_fact_ofe = self.cleaner.clean_carreras(raw_car, df_dim_facultad)
        tables["dim_carrera"] = df_dim_car
        tables["dim_nivel_formacion"] = df_dim_niv
        tables["dim_modalidad"] = df_dim_mod
        tables["fact_oferta_academica"] = df_fact_ofe

        self.validator.profile_dataframe(df_dim_car, "dim_carrera", "carrera_key", ["carrera_key", "nombre_carrera"])
        self.validator.profile_dataframe(df_dim_niv, "dim_nivel_formacion", "nivel_key", ["nivel_key", "nombre_nivel"])
        self.validator.profile_dataframe(df_dim_mod, "dim_modalidad", "modalidad_key", ["modalidad_key", "nombre_modalidad"])
        self.validator.profile_dataframe(df_fact_ofe, "fact_oferta_academica", "oferta_key", ["oferta_key", "carrera_key", "facultad_key"])

        # 4. Autoridades, Cargos y Hechos Autoridades
        raw_aut = raw_data.get("autoridades", [])
        df_dim_aut, df_dim_car_cargo, df_fact_aut = self.cleaner.clean_autoridades(raw_aut, df_dim_facultad)
        tables["dim_autoridad"] = df_dim_aut
        tables["dim_cargo"] = df_dim_car_cargo
        tables["fact_designacion_autoridades"] = df_fact_aut

        self.validator.profile_dataframe(df_dim_aut, "dim_autoridad", "autoridad_key", ["autoridad_key", "nombre_completo"])
        self.validator.profile_dataframe(df_dim_car_cargo, "dim_cargo", "cargo_key", ["cargo_key", "nombre_cargo"])
        self.validator.profile_dataframe(df_fact_aut, "fact_designacion_autoridades", "designacion_key", ["designacion_key", "autoridad_key", "cargo_key"])

        # 5. Noticias y Hechos Comunicacion
        raw_not = raw_data.get("noticias", [])
        df_dim_cat, df_fact_not = self.cleaner.clean_noticias(raw_not)
        tables["dim_categoria_noticia"] = df_dim_cat
        tables["fact_comunicacion_institucional"] = df_fact_not

        self.validator.profile_dataframe(df_dim_cat, "dim_categoria_noticia", "categoria_key", ["categoria_key", "nombre_categoria"])
        self.validator.profile_dataframe(df_fact_not, "fact_comunicacion_institucional", "noticia_key", ["noticia_key", "categoria_key"])

        # 6. Informacion Institucional General (Tabla complementaria)
        raw_inst = raw_data.get("institucional", [])
        if raw_inst:
            df_inst = pd.DataFrame(raw_inst)
            tables["dim_informacion_institucional"] = df_inst

        # Generar reporte de calidad
        report_md = self.validator.generate_markdown_report()
        report_path = settings.logs_dir / "reporte_calidad_datos.md"
        report_path.write_text(report_md, encoding="utf-8")
        logger.info(f"Reporte de calidad y perfilamiento persistido en: {report_path.name}")

        return tables

    def load_data(self, tables: Dict[str, pd.DataFrame], to_csv: bool = True, to_db: bool = True) -> None:
        """Carga las tablas en archivos CSV procesados y base de datos relacional.

        Args:
            tables (Dict[str, pd.DataFrame]): Tablas dimensionales y de hechos.
            to_csv (bool): Si se debe exportar a data/processed/.
            to_db (bool): Si se debe insertar en la base de datos SQL.
        """
        if to_csv:
            logger.info("Exportando entidades procesadas a formato CSV...")
            self.csv_loader.load_all(tables)

        if to_db:
            logger.info("Insertando entidades procesadas en la base de datos SQL del Data Warehouse...")
            counts = self.db_loader.load_all(tables)
            for tbl, cnt in counts.items():
                logger.info(f"Base de datos -> Tabla '{tbl}': {cnt} registros cargados.")

    def run_all(self) -> None:
        """Ejecuta el ciclo de vida completo de extremo a extremo (E -> T -> L)."""
        logger.info("=== INICIANDO PIPELINE COMPLETO ETL EPN ===")
        all_modules = ["facultades", "carreras", "autoridades", "institucional", "noticias"]
        raw = self.run_scrapers(all_modules)
        tables = self.transform(raw)
        self.load_data(tables, to_csv=True, to_db=True)
        logger.info("=== PIPELINE ETL EPN FINALIZADO EXITOSAMENTE ===")


def main() -> None:
    """Punto de entrada de linea de comandos para el orquestador."""
    parser = argparse.ArgumentParser(
        description="Orquestador ETL para extraccion, transformacion y carga de datos de la Escuela Politecnica Nacional.",
        epilog="Proyecto academico de Business Intelligence - Ingenieria de Datos."
    )

    parser.add_argument("--all", action="store_true", help="Ejecutar el pipeline ETL completo de extremo a extremo.")
    parser.add_argument("--facultades", action="store_true", help="Ejecutar unicamente el extractor de facultades.")
    parser.add_argument("--carreras", action="store_true", help="Ejecutar unicamente el extractor de carreras.")
    parser.add_argument("--autoridades", action="store_true", help="Ejecutar unicamente el extractor de autoridades.")
    parser.add_argument("--institucional", action="store_true", help="Ejecutar unicamente el extractor institucional.")
    parser.add_argument("--noticias", action="store_true", help="Ejecutar unicamente el extractor de noticias.")
    parser.add_argument("--transform", action="store_true", help="Ejecutar fase de transformacion y validacion sobre datos interim.")
    parser.add_argument("--load-csv", action="store_true", help="Cargar datos procesados unicamente a archivos CSV.")
    parser.add_argument("--load-db", action="store_true", help="Cargar datos procesados a la base de datos SQL.")
    parser.add_argument("--no-cache", action="store_true", help="Desactivar uso de cache local (forzar solicitudes de red).")
    parser.add_argument("--force-refresh", action="store_true", help="Reescribir archivos en cache local con nuevas descargas.")

    args = parser.parse_args()

    pipeline = ETLPipeline(use_cache=not args.no_cache, force_refresh=args.force_refresh)

    # Si no se pasan argumentos o se pasa --all, ejecutar todo el pipeline
    if args.all or not any([
        args.facultades, args.carreras, args.autoridades,
        args.institucional, args.noticias, args.transform,
        args.load_csv, args.load_db
    ]):
        pipeline.run_all()
        return

    # Ejecucion modular de scrapers
    selected_modules = []
    if args.facultades:
        selected_modules.append("facultades")
    if args.carreras:
        selected_modules.append("carreras")
    if args.autoridades:
        selected_modules.append("autoridades")
    if args.institucional:
        selected_modules.append("institucional")
    if args.noticias:
        selected_modules.append("noticias")

    raw_data = {}
    if selected_modules:
        raw_data = pipeline.run_scrapers(selected_modules)
    else:
        raw_data = pipeline.load_interim_from_disk()

    # Si se solicito transformacion o carga
    if args.transform or args.load_csv or args.load_db:
        if not raw_data:
            raw_data = pipeline.load_interim_from_disk()
        tables = pipeline.transform(raw_data)

        if args.load_csv or args.load_db:
            pipeline.load_data(tables, to_csv=args.load_csv or not args.load_db, to_db=args.load_db)


if __name__ == "__main__":
    main()
