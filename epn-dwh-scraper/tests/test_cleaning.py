"""
Pruebas unitarias para el modulo de limpieza y transformacion dimensional (cleaning.py).
"""

import pytest
import pandas as pd
from src.transform.cleaning import DataCleaner
from src.utils.helpers import clean_text, extract_email, extract_duration_periods, extract_degree_level, extract_modality, generate_surrogate_key


class TestHelpers:
    """Pruebas de funciones auxiliares de normalizacion y extraccion."""

    def test_clean_text_basic(self):
        raw = "   Facultad de   Ingenieria \n\n de Sistemas \xa0 "
        expected = "Facultad de Ingenieria de Sistemas"
        assert clean_text(raw) == expected

    def test_clean_text_html_entities(self):
        raw = "Oferta laboral &#8211; Docente &amp; Investigador"
        expected = "Oferta laboral – Docente & Investigador"
        assert clean_text(raw) == expected

    def test_extract_email_valid(self):
        text = "Para mayor informacion contactar a decanato.sistemas@epn.edu.ec o en campus."
        assert extract_email(text) == "decanato.sistemas@epn.edu.ec"

    def test_extract_email_none(self):
        text = "No se dispone de direccion electronica visible."
        assert extract_email(text) is None

    def test_extract_duration_periods(self):
        assert extract_duration_periods("Nueve (9) periodos academicos") == 9
        assert extract_duration_periods("Duracion: 10 semestres") == 10
        assert extract_duration_periods("4 periodos") == 4
        assert extract_duration_periods("Sin dato explicito") is None

    def test_extract_degree_level(self):
        assert extract_degree_level("Ingenieria en Software") == "Grado"
        assert extract_degree_level("Tecnologia Superior en Desarrollo de Software") == "Tecnologia"
        assert extract_degree_level("Maestria en Inteligencia Artificial") == "Maestria"
        assert extract_degree_level("Doctorado en Ingenieria Electrica") == "Doctorado"

    def test_extract_modality(self):
        assert extract_modality("Modalidad Presencial") == "Presencial"
        assert extract_modality("Modalidad Dual con practicas") == "Dual"
        assert extract_modality("En linea / virtual") == "En Linea"

    def test_generate_surrogate_key_idempotence(self):
        k1 = generate_surrogate_key("facultad", "FIS")
        k2 = generate_surrogate_key("facultad", "FIS")
        k3 = generate_surrogate_key("facultad", "FIEE")
        assert k1 == k2
        assert k1 != k3
        assert isinstance(k1, int)
        assert k1 > 0


class TestDataCleaner:
    """Pruebas unitarias para DataCleaner y construccion de esquemas."""

    @pytest.fixture
    def cleaner(self):
        return DataCleaner()

    def test_build_dim_tiempo(self, cleaner):
        df_tiempo = cleaner.build_dim_tiempo(2024, 2024)
        assert len(df_tiempo) == 366  # 2024 es anio bisiesto
        assert "tiempo_key" in df_tiempo.columns
        assert "anio" in df_tiempo.columns
        assert "semestre" in df_tiempo.columns
        assert df_tiempo["tiempo_key"].is_monotonic_increasing

    def test_clean_facultades(self, cleaner):
        raw_facultades = [
            {
                "nombre": "Facultad de Ingenieria de Sistemas",
                "sigla": "FIS",
                "decano": "Dra. Rosa Navarrete",
                "subdecano": "Dr. Denys Flores",
                "descripcion": "Unidad academica rectora.",
                "mision": "Formar ingenieros.",
                "vision": "Liderazgo regional.",
                "url": "https://www.epn.edu.ec/facultad-ingenieria-de-sistemas/",
                "departamentos_adscritos": "DICC",
                "contacto_correo": "fis@epn.edu.ec",
                "contacto_telefono": "(+593) 2 2976 300",
                "ubicacion_campus": "Campus Politecnico",
            },
            {
                "nombre": "Facultad de Ingenieria de Sistemas",  # Duplicado intencional
                "sigla": "FIS",
                "decano": "Dra. Rosa Navarrete",
                "subdecano": "Dr. Denys Flores",
                "descripcion": "Unidad academica rectora.",
                "mision": "Formar ingenieros.",
                "vision": "Liderazgo regional.",
                "url": "https://www.epn.edu.ec/facultad-ingenieria-de-sistemas/",
                "departamentos_adscritos": "DICC",
                "contacto_correo": "fis@epn.edu.ec",
                "contacto_telefono": "(+593) 2 2976 300",
                "ubicacion_campus": "Campus Politecnico",
            }
        ]
        df_fac = cleaner.clean_facultades(raw_facultades)
        assert len(df_fac) == 1
        assert "facultad_key" in df_fac.columns
        assert df_fac.iloc[0]["sigla"] == "FIS"

    def test_clean_carreras(self, cleaner):
        raw_facultades = [
            {
                "nombre": "Facultad de Ingenieria de Sistemas",
                "sigla": "FIS",
                "decano": "Dra. Rosa Navarrete",
                "subdecano": "Dr. Denys Flores",
                "descripcion": "",
                "mision": "",
                "vision": "",
                "url": "https://www.epn.edu.ec/facultad-ingenieria-de-sistemas/",
                "departamentos_adscritos": "",
                "contacto_correo": "",
                "contacto_telefono": "",
                "ubicacion_campus": "",
            }
        ]
        df_fac = cleaner.clean_facultades(raw_facultades)

        raw_carreras = [
            {
                "nombre": "Ingenieria en Software",
                "facultad_nombre": "Facultad de Ingenieria de Sistemas",
                "nivel": "Grado",
                "modalidad": "Presencial",
                "duracion_periodos": 9,
                "duracion_anios": 4.5,
                "creditos": 120,
                "titulo_otorga": "Ingeniera/o en Software",
                "codigo_resolucion": "RPC-SO-33-No.639-2016",
                "perfil_ingreso": "Bases matematicas",
                "perfil_egreso": "Desarrollo de software",
                "campo_ocupacional": "Tecnologia",
                "malla_curricular_url": "https://www.epn.edu.ec/malla.pdf",
                "url": "https://www.epn.edu.ec/ingenieria-en-software/",
            }
        ]

        df_carr, df_niv, df_mod, df_fact = cleaner.clean_carreras(raw_carreras, df_fac)
        assert len(df_carr) == 1
        assert len(df_niv) == 1
        assert len(df_mod) == 1
        assert len(df_fact) == 1
        assert df_fact.iloc[0]["duracion_periodos"] == 9
        assert df_fact.iloc[0]["facultad_key"] == df_fac.iloc[0]["facultad_key"]
