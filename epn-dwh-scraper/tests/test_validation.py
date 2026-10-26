"""
Pruebas unitarias para el modulo de aseguramiento de calidad (validation.py).
"""

import pytest
import pandas as pd
from src.transform.validation import DataValidator


class TestDataValidator:
    """Pruebas de reglas de negocio y perfilamiento de calidad."""

    @pytest.fixture
    def validator(self):
        return DataValidator()

    def test_profile_empty_dataframe(self, validator):
        df_empty = pd.DataFrame()
        res = validator.profile_dataframe(df_empty, "tabla_vacia", "id_key", ["col1"])
        assert res["total_registros"] == 0
        assert "vacia" in res["estado_calidad"].lower()

    def test_profile_valid_dataframe(self, validator):
        df = pd.DataFrame([
            {"facultad_key": 101, "nombre": "FIS", "correo": "fis@epn.edu.ec"},
            {"facultad_key": 102, "nombre": "FIEE", "correo": "fiee@epn.edu.ec"},
        ])
        res = validator.profile_dataframe(df, "dim_test", "facultad_key", ["facultad_key", "nombre"])
        assert res["total_registros"] == 2
        assert res["duplicados_clave"] == 0
        assert res["estado_calidad"] == "CONFORME"

    def test_profile_duplicated_keys(self, validator):
        df = pd.DataFrame([
            {"carrera_key": 501, "nombre": "Software"},
            {"carrera_key": 501, "nombre": "Computacion"},  # Clave duplicada
        ])
        res = validator.profile_dataframe(df, "dim_duplicada", "carrera_key", ["nombre"])
        assert res["duplicados_clave"] == 1
        assert res["estado_calidad"] == "OBSERVACIONES DETECTADAS"

    def test_profile_outliers_duracion(self, validator):
        df = pd.DataFrame([
            {"oferta_key": 1, "duracion_periodos": 9, "creditos_totales": 120},
            {"oferta_key": 2, "duracion_periodos": 25, "creditos_totales": 120},  # Outlier
        ])
        res = validator.profile_dataframe(df, "fact_oferta", "oferta_key", ["oferta_key"])
        assert any("duracion de periodos" in obs for obs in res["observaciones"])

    def test_markdown_report_generation(self, validator):
        df = pd.DataFrame([{"key": 1, "nombre": "Test"}])
        validator.profile_dataframe(df, "tbl_report", "key", ["nombre"])
        report = validator.generate_markdown_report()
        assert "# Reporte de Calidad" in report
        assert "tbl_report" in report
        assert "CONFORME" in report
