"""
Pruebas unitarias para la capa de extraccion (scrapers) y comportamiento de red.
"""

from unittest.mock import MagicMock
import pytest
from src.scrapers.autoridades_scraper import AutoridadesScraper
from src.scrapers.facultades_scraper import FacultadesScraper
from src.scrapers.institucional_scraper import InstitucionalScraper
from src.utils.http_client import HttpClient


class TestScrapers:
    """Pruebas de inicializacion y parseo sintetico de extractores."""

    @pytest.fixture
    def mock_http_client(self):
        client = MagicMock(spec=HttpClient)
        client.is_allowed.return_value = True
        return client

    def test_facultades_scraper_parse_page(self, mock_http_client):
        sample_html = """
        <html>
            <head><title>Facultad de Ingenieria de Sistemas - EPN</title></head>
            <body>
                <h1>Facultad de Ingenieria de Sistemas</h1>
                <p>Decana: Dra. Rosa Navarrete</p>
                <p>Subdecano: Dr. Denys Flores</p>
                <p>La Facultad de Ingenieria de Sistemas es el referente en ciencias computacionales.</p>
                <h2>DEPARTAMENTO DE INFORMATICA (DICC)</h2>
                <p>Contacto: fis@epn.edu.ec</p>
            </body>
        </html>
        """
        mock_http_client.get.return_value = sample_html

        scraper = FacultadesScraper(mock_http_client)
        data = scraper._parse_faculty_page("https://www.epn.edu.ec/facultad-ingenieria-de-sistemas/")

        assert data["nombre"] == "Facultad de Ingenieria de Sistemas"
        assert data["sigla"] == "FIS"
        assert "Rosa Navarrete" in data["decano"]
        assert "Denys Flores" in data["subdecano"]
        assert data["contacto_correo"] == "fis@epn.edu.ec"

    def test_autoridades_scraper_build_record(self, mock_http_client):
        scraper = AutoridadesScraper(mock_http_client)
        rec = scraper._build_record(
            name="Dr. Tarquino Sanchez Almeida",
            cargo="Rector",
            unidad="Rectorado",
            bio="Doctor en Investigacion Educativa.",
            url="https://www.epn.edu.ec/autoridades/"
        )

        assert rec["nombre_completo"] == "Dr. Tarquino Sanchez Almeida"
        assert rec["titulo_academico"] == "Dr."
        assert rec["cargo"] == "Rector"
        assert rec["tipo_cargo"] == "Alta Direccion"
        assert rec["es_titular"] == 1
        # El correo no se infiere: sin dato en la fuente queda NULL
        assert rec["correo_contacto"] is None

    def test_institucional_scraper_extract(self, mock_http_client):
        mock_http_client.get.return_value = """
        <html>
            <body>
                <h2>NuestrosPrincipios</h2>
                <h3>MISION</h3>
                <p>Formar cientificos y profesionales de excelencia para el desarrollo del pais.</p>
                <h3>VISION</h3>
                <p>Ser una institucion lider en educacion superior y generacion tecnologica.</p>
            </body>
        </html>
        """
        scraper = InstitucionalScraper(mock_http_client)
        records = scraper.extract()
        assert len(records) >= 2
        assert any(r["clave"] == "Mision" for r in records)
        assert any(r["clave"] == "Vision" for r in records)
