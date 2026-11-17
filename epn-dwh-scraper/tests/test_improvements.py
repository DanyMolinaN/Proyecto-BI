"""
Pruebas de las correcciones de calidad: sin datos inventados, fallo ante extraccion
insuficiente, cache con vencimiento, politica de robots.txt y SCD Tipo 2.
"""

import os
import time
from datetime import datetime
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.load.to_database import DatabaseLoader
from src.scrapers.base_scraper import BaseScraper, ExtractionError
from src.scrapers.carreras_scraper import CarrerasScraper
from src.scrapers.facultades_scraper import FacultadesScraper
from src.transform.cleaning import DataCleaner
from src.transform.scd2 import apply_scd2
from src.transform.validation import DataValidator
from src.utils.helpers import extract_modality, generate_surrogate_key
from src.utils.http_client import HttpClient


@pytest.fixture
def mock_http():
    client = MagicMock(spec=HttpClient)
    client.is_allowed.return_value = True
    return client


class TestSinDatosInventados:
    def test_facultades_sin_urls_no_usa_lista_canonica(self, mock_http):
        mock_http.get.return_value = None
        assert FacultadesScraper(mock_http).extract() == []

    def test_programa_sin_respuesta_se_omite(self, mock_http):
        mock_http.get.return_value = None
        assert CarrerasScraper(mock_http)._parse_program_page("https://x/y/", "Grado") == {}

    def test_ficha_sin_metricas_deja_null(self, mock_http):
        mock_http.get.return_value = "<html><body><h1>Ingenieria en Software</h1></body></html>"
        rec = CarrerasScraper(mock_http)._parse_program_page("https://x/ing/", "Grado")
        assert rec["duracion_periodos"] is None
        assert rec["creditos"] is None
        assert rec["perfil_ingreso"] is None
        assert rec["codigo_resolucion"] is None

    def test_modalidad_desconocida_es_none(self):
        assert extract_modality("texto sin dato") is None
        assert extract_modality("Semipresencial") == "Semipresencial"

    def test_limpieza_no_rellena_metricas_ni_correo(self):
        cleaner = DataCleaner()
        df_fac = cleaner.clean_facultades([{"nombre": "Facultad de Ciencias", "sigla": "FC", "contacto_correo": ""}])
        assert pd.isna(df_fac.iloc[0]["contacto_correo"])

        carreras = [{"nombre": "Carrera X", "facultad_nombre": "Desconocida", "nivel": "Grado",
                     "modalidad": None, "url": "https://x/"}]
        _, _, _, fact = cleaner.clean_carreras(carreras, df_fac)
        row = fact.iloc[0]
        assert pd.isna(row["duracion_periodos"]) and pd.isna(row["creditos_totales"])
        assert pd.isna(row["facultad_key"])  # no se asigna a la primera facultad
        assert pd.isna(row["es_acreditada"])


class TestMinimoDeRegistros:
    def test_run_falla_si_extrae_menos_del_minimo(self, mock_http, monkeypatch):
        class Vacio(BaseScraper):
            def extract(self):
                return [{"a": 1}]

        monkeypatch.setattr("src.scrapers.base_scraper.settings.min_records", {"vacio": 5})
        with pytest.raises(ExtractionError):
            Vacio(mock_http).run()


class TestCacheYRobots:
    def test_cache_vencida_no_es_fresca(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.utils.http_client.settings.cache_ttl_hours", 1)
        client = HttpClient.__new__(HttpClient)
        f = tmp_path / "c.html"
        f.write_text("x")
        assert client._cache_is_fresh(f)
        old = time.time() - 3 * 3600
        os.utime(f, (old, old))
        assert not client._cache_is_fresh(f)

    def test_robots_inalcanzable_bloquea_rastreo(self, monkeypatch):
        def boom(*a, **k):
            raise ConnectionError("sin red")

        monkeypatch.setattr("requests.Session.get", boom)
        assert HttpClient().is_allowed("https://www.epn.edu.ec/facultades/") is False


def _dim(nombre, bio="bio", correo=None, key=None):
    return {"autoridad_key": key or generate_surrogate_key("autoridad", nombre), "nombre_completo": nombre,
            "titulo_academico": "Dr.", "correo_contacto": correo, "biografia": bio, "es_vigente": 1,
            "fecha_inicio_vigencia": "2026-01-01", "fecha_fin_vigencia": "9999-12-31"}


def _fact(dim_row, cargo="Decano"):
    ck = generate_surrogate_key("cargo", cargo)
    return {"designacion_key": generate_surrogate_key("designacion", dim_row["autoridad_key"], ck),
            "autoridad_key": dim_row["autoridad_key"], "cargo_key": ck, "facultad_key": None,
            "es_titular": 1, "tiempo_designacion_key": 20260101}


class TestScd2:
    today = datetime(2026, 10, 27)

    def test_sin_cambios_es_idempotente(self):
        d = _dim("Dr. Ana Perez")
        dim1, fact1 = apply_scd2(pd.DataFrame([d]), pd.DataFrame([_fact(d)]), None, None, self.today)
        dim2, fact2 = apply_scd2(pd.DataFrame([d]), pd.DataFrame([_fact(d)]), dim1, fact1, self.today)
        assert len(dim2) == 1 and len(fact2) == 1
        assert dim2.iloc[0]["es_vigente"] == 1

    def test_cambio_de_atributos_crea_nueva_version(self):
        d = _dim("Dr. Ana Perez", bio="v1")
        dim1, fact1 = apply_scd2(pd.DataFrame([d]), pd.DataFrame([_fact(d)]), None, None, self.today)
        d2 = _dim("Dr. Ana Perez", bio="v2")
        dim2, fact2 = apply_scd2(pd.DataFrame([d2]), pd.DataFrame([_fact(d2)]), dim1, fact1, self.today)
        assert len(dim2) == 2
        vigentes = dim2[dim2["es_vigente"] == 1]
        historicas = dim2[dim2["es_vigente"] == 0]
        assert len(vigentes) == 1 and len(historicas) == 1
        assert historicas.iloc[0]["fecha_fin_vigencia"] == "2026-10-27"
        assert vigentes.iloc[0]["biografia"] == "v2"
        assert vigentes.iloc[0]["autoridad_key"] != historicas.iloc[0]["autoridad_key"]
        assert len(fact2) == 2  # se conserva el hecho historico
        assert set(fact2["autoridad_key"]) == set(dim2["autoridad_key"])

    def test_autoridad_ausente_se_cierra(self):
        a, b = _dim("Dr. Ana Perez"), _dim("Dr. Luis Mora")
        dim1, fact1 = apply_scd2(pd.DataFrame([a, b]), pd.DataFrame([_fact(a), _fact(b)]), None, None, self.today)
        dim2, _ = apply_scd2(pd.DataFrame([a]), pd.DataFrame([_fact(a)]), dim1, fact1, self.today)
        luis = dim2[dim2["nombre_completo"] == "Dr. Luis Mora"].iloc[0]
        assert luis["es_vigente"] == 0 and luis["fecha_fin_vigencia"] == "2026-10-27"

    def test_round_trip_con_base_de_datos(self, tmp_path):
        loader = DatabaseLoader(f"sqlite:///{tmp_path/'t.db'}")
        d = _dim("Dr. Ana Perez", bio="v1")
        dim1, fact1 = apply_scd2(pd.DataFrame([d]), pd.DataFrame([_fact(d)]), None, None, self.today)
        loader.load_all({"dim_autoridad": dim1, "fact_designacion_autoridades": fact1})
        d2 = _dim("Dr. Ana Perez", bio="v2")
        dim2, fact2 = apply_scd2(pd.DataFrame([d2]), pd.DataFrame([_fact(d2)]),
                                 loader.read_table("dim_autoridad"), loader.read_table("fact_designacion_autoridades"), self.today)
        loader.load_all({"dim_autoridad": dim2, "fact_designacion_autoridades": fact2})
        assert loader.get_table_counts()["dim_autoridad"] == 2


class TestValidadorIntegridad:
    def test_fk_nula_se_reporta_como_huerfana(self):
        dim = pd.DataFrame([{"facultad_key": 1}])
        fact = pd.DataFrame([{"oferta_key": 1, "facultad_key": 1}, {"oferta_key": 2, "facultad_key": None}])
        res = DataValidator().profile_dataframe(fact, "f", "oferta_key", ["oferta_key"],
                                                foreign_keys={"facultad_key": (dim, "facultad_key")})
        assert res["estado_calidad"] == "OBSERVACIONES DETECTADAS"
        assert any("sin registro" in o for o in res["observaciones"])

    def test_nulos_aparecen_como_informacion(self):
        df = pd.DataFrame([{"k": 1, "x": None}, {"k": 2, "x": "a"}])
        res = DataValidator().profile_dataframe(df, "t", "k", ["k"])
        assert any(o.startswith("Info: x") for o in res["observaciones"])


class TestEmparejamientoFacultad:
    def test_ignora_tildes_y_variaciones_de_nombre(self):
        df_fac = DataCleaner().clean_facultades([
            {"nombre": "Facultad de Ingeniería Geología y Petróleos", "sigla": "FIGP"},
            {"nombre": "Escuelas de Formación de Tecnólogos", "sigla": "ESFOT"},
            {"nombre": "Facultad de Ciencias", "sigla": "FC"},
        ])
        carreras = [
            {"nombre": "A", "facultad_nombre": "Facultad de Geologia y Petroleos", "nivel": "Grado", "url": "u1"},
            {"nombre": "B", "facultad_nombre": "Escuela de Formacion de Tecnologos", "nivel": "Grado", "url": "u2"},
            {"nombre": "C", "facultad_nombre": "Facultad Inexistente de Magia", "nivel": "Grado", "url": "u3"},
        ]
        _, _, _, fact = DataCleaner().clean_carreras(carreras, df_fac)
        keys = dict(zip(["A", "B", "C"], fact["facultad_key"]))
        assert not pd.isna(keys["A"]) and not pd.isna(keys["B"])
        assert pd.isna(keys["C"])


class TestTextoPegado:
    def test_decano_y_subdecano_no_se_concatenan(self, mock_http):
        mock_http.get.return_value = (
            "<html><body><h1>Facultad de Ingenieria Civil</h1>"
            "<div><p>Decano: Dr. Jorge Toapaxi</p><p>Subdecano: Dr. Khaled Hamad</p>"
            "<span>decano.civil@epn.edu.ec</span><span>subdecano</span></div></body></html>"
        )
        data = FacultadesScraper(mock_http)._parse_faculty_page("https://www.epn.edu.ec/facultad-civil/")
        assert data["decano"] == "Dr. Jorge Toapaxi"
        assert data["subdecano"] == "Dr. Khaled Hamad"
        assert data["contacto_correo"] == "decano.civil@epn.edu.ec"


class TestPrecisionDeClaves:
    def test_claves_grandes_no_pierden_precision_con_nulos(self):
        cleaner = DataCleaner()
        df_fac = cleaner.clean_facultades([{"nombre": "Facultad de Ciencias", "sigla": "FC"}])
        carreras = [
            {"nombre": "A", "facultad_nombre": "Facultad de Ciencias", "nivel": "Grado", "url": "u1"},
            {"nombre": "B", "facultad_nombre": "Otra", "nivel": "Grado", "url": "u2"},
        ]
        _, _, _, fact = cleaner.clean_carreras(carreras, df_fac)
        assert fact.iloc[0]["facultad_key"] == df_fac.iloc[0]["facultad_key"]
        res = DataValidator().profile_dataframe(
            fact, "f", "oferta_key", ["oferta_key"], foreign_keys={"facultad_key": (df_fac, "facultad_key")})
        assert sum("sin registro" in o for o in res["observaciones"]) == 1
        assert "1 registros con facultad_key" in " ".join(res["observaciones"])


class TestFichaDeCarreraReal:
    """HTML con la estructura real del portal: etiqueta y valor en elementos consecutivos, sin dos puntos."""

    HTML_GRADO = """
    <html><body><h1>Ingeniería en Mecánica</h1>
    <nav><p>Facultad de Ingeniería Civil y Ambiental</p></nav>
    <p>Resolución de aprobación CES:</p><p>RPC-SO-24-No.476-2017</p>
    <h3>INFORMACIÓN DE POSTULACIÓN</h3>
    <h4>Unidad Académica</h4><p>Facultad de Ingeniería Mecánica</p>
    <h4>Título que otorga</h4><p>Ingeniera/o en Mecánica</p>
    <h4>Duración</h4><p>Nueve períodos académicos</p>
    <h4>Modalidad</h4><p>Presencial</p>
    </body></html>
    """

    def test_extrae_campos_publicados(self, mock_http):
        mock_http.get.return_value = self.HTML_GRADO
        rec = CarrerasScraper(mock_http)._parse_program_page("https://x/ingenieria-en-mecanica/", "Grado")
        assert rec["facultad_nombre"] == "Facultad de Ingeniería Mecánica"  # no la del menú
        assert rec["duracion_periodos"] == 9
        assert rec["duracion_anios"] == 4.5
        assert rec["modalidad"] == "Presencial"
        assert rec["titulo_otorga"] == "Ingeniera/o en Mecánica"
        assert rec["codigo_resolucion"] == "RPC-SO-24-No.476-2017"
        assert rec["creditos"] is None  # el portal no publica creditos totales
        assert not rec["campos_inferidos"]

    def test_numero_en_palabras_y_con_digitos(self):
        from src.utils.helpers import extract_duration_periods
        assert extract_duration_periods("Nueve períodos académicos") == 9
        assert extract_duration_periods("Nueve (9) períodos académicos") == 9
        assert extract_duration_periods("Cinco períodos") == 5

    def test_maestria_sin_ficha_infiere_facultad_y_lo_marca(self, mock_http):
        mock_http.get.return_value = "<html><body><h1>Maestría en Computación</h1><p>Perfil de ingreso</p></body></html>"
        rec = CarrerasScraper(mock_http)._parse_program_page("https://x/maestria-en-computacion/", "Maestria")
        assert rec["facultad_nombre"] == "Facultad de Ingenieria de Sistemas"
        assert rec["campos_inferidos"] == "facultad"
        assert rec["duracion_periodos"] is None


class TestPerfilesSinMenu:
    HTML = """
    <html><body><h1>Ingeniería en Software</h1>
    <ul><li>INTRANET</li><li>OFERTA ACADÉMICA</li><li>Nuestros Principios</li></ul>
    <p>Resolución de aprobación CES:</p><p>RPC-SO-33-No.639-2016</p>
    <ul><li>PERFIL DE INGRESO</li><li>OBJETIVOS</li><li>PERFIL DE EGRESO</li><li>MALLA</li><li>CONTACTO</li></ul>
    <p>Los aspirantes deben haber concluido el bachillerato y obtener el puntaje mínimo.</p>
    <p>Conocimientos: computación, matemática e inglés.</p>
    <h3>Objetivos de la Carrera</h3><p>Formar profesionales.</p>
    <h3>Resultados Generales</h3><p>RG1.</p><p>Identificar necesidades de los sectores estratégicos.</p>
    <p>RG2.</p><p>Demostrar hábitos de trabajo efectivos.</p>
    <h3>Resultados Específicos</h3><p>RE1.</p><p>Aplicar teorías.</p>
    </body></html>
    """

    def test_grado_toma_solo_el_contenido(self, mock_http):
        mock_http.get.return_value = self.HTML
        rec = CarrerasScraper(mock_http)._parse_program_page("https://x/ingenieria-en-software/", "Grado")
        assert rec["perfil_ingreso"].startswith("Los aspirantes deben haber concluido")
        assert "Conocimientos: computación" in rec["perfil_ingreso"]
        assert "Formar profesionales" not in rec["perfil_ingreso"]
        assert "INTRANET" not in rec["perfil_ingreso"] and "Resolución" not in rec["perfil_ingreso"]
        assert rec["perfil_egreso"] == "Identificar necesidades de los sectores estratégicos. Demostrar hábitos de trabajo efectivos."
        assert rec["campo_ocupacional"] is None

    def test_sin_pestanas_no_se_inventa_nada(self, mock_http):
        mock_http.get.return_value = "<html><body><h1>Maestría X</h1><p>Perfil de ingreso del menú y mucho texto aquí.</p></body></html>"
        rec = CarrerasScraper(mock_http)._parse_program_page("https://x/maestria-x/", "Maestria")
        assert rec["perfil_ingreso"] is None and rec["perfil_egreso"] is None


class TestBanderasDeCache:
    def test_force_refresh_ignora_cache_vigente(self, tmp_path, monkeypatch):
        monkeypatch.setattr("requests.Session.get", lambda *a, **k: type("R", (), {"status_code": 404, "text": ""})())
        monkeypatch.setattr("src.utils.http_client.settings.data_raw_dir", tmp_path)
        client = HttpClient(force_refresh=True)
        client.raw_dir = tmp_path
        url = "https://www.epn.edu.ec/x/"
        client._get_cache_path(url).write_text("cacheado")
        monkeypatch.setattr("requests.Session.get", lambda *a, **k: type("R", (), {"status_code": 200, "text": "nuevo"})())
        assert client.get(url) == "nuevo"
        assert HttpClient(force_refresh=False).__class__ is HttpClient  # sin bandera usaria la cache

    def test_no_cache_se_propaga(self, monkeypatch):
        monkeypatch.setattr("requests.Session.get", lambda *a, **k: type("R", (), {"status_code": 404, "text": ""})())
        assert HttpClient(use_cache=False).use_cache is False


class TestInstitucionalYNoticiasSinRespaldo:
    def test_noticias_sin_fuentes_devuelve_vacio(self, mock_http):
        from src.scrapers.noticias_scraper import NoticiasScraper
        mock_http.get.return_value = None
        mock_http.get_json.return_value = None
        assert NoticiasScraper(mock_http).extract() == []

    def test_institucional_sin_paginas_devuelve_vacio(self, mock_http):
        from src.scrapers.institucional_scraper import InstitucionalScraper
        mock_http.get.return_value = None
        assert InstitucionalScraper(mock_http).extract() == []

    def test_historia_lee_anio_real_y_no_usa_1869_por_defecto(self, mock_http):
        from src.scrapers.institucional_scraper import InstitucionalScraper
        mock_http.get.return_value = (
            "<html><body><h1>HISTORIA</h1><p>1935</p><p>28 de febrero</p><p>REAPERTURA</p>"
            "<p>El presidente decreta la reapertura de la institucion.</p>"
            "<p>1964</p><p>EPN CAMPUS GIRON</p><p>Se traslada al actual Campus Politecnico.</p>"
            "<p>Dirección: Av. Ladrón de Guevara</p></body></html>"
        )
        hitos = InstitucionalScraper(mock_http)._extract_historia()
        assert [h["anio"] for h in hitos] == [1935, 1964]
        assert hitos[0]["titulo"] == "REAPERTURA"

    def test_mision_y_vision_salen_del_encabezado_no_del_menu(self, mock_http):
        from src.scrapers.institucional_scraper import InstitucionalScraper
        mock_http.get.return_value = (
            "<html><body><nav><p>INICIO LA POLI Nuestros Principios Misión, Visión, Valores</p></nav>"
            "<h2>MISIÓN</h2><p>Somos una institución pública de educación superior.</p>"
            "<h2>VISIÓN</h2><p>Ser una universidad de excelencia.</p></body></html>"
        )
        n = InstitucionalScraper(mock_http)._extract_nosotros()
        assert n["mision"] == "Somos una institución pública de educación superior."
        assert n["vision"] == "Ser una universidad de excelencia."
        assert n["valores"] is None and n["principios"] is None
