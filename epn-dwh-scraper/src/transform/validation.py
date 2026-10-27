"""
Modulo de validacion y aseguramiento de calidad de datos (Data Quality Profiling).

Ejecuta reglas automaticas sobre integridad referencial, unicidad de claves sustitutas,
campos mandatorios, rangos razonables de metricas (outliers) y formato de correos electronicos,
generando reportes formales de perfilamiento de datos.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger("validation")


class DataValidator:
    """Validador y perfilador de calidad para DataFrames dimensionales."""

    def __init__(self) -> None:
        """Inicializa el contenedor de hallazgos y metricas de calidad."""
        self.validation_results: List[Dict[str, Any]] = []

    def profile_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        key_column: str,
        required_columns: List[str],
        foreign_keys: Optional[Dict[str, Tuple[pd.DataFrame, str]]] = None,
    ) -> Dict[str, Any]:
        """Realiza el perfilamiento cuantitativo y validacion estructural de una tabla.

        Args:
            df (pd.DataFrame): DataFrame a auditar.
            table_name (str): Nombre logico de la tabla.
            key_column (str): Nombre de la clave primaria o sustituta.
            required_columns (List[str]): Lista de columnas obligatorias sin nulos ni vacios.
            foreign_keys (Optional[Dict]): {columna_fk: (dataframe_referenciado, columna_pk)} para verificar
                integridad referencial; una FK nula o sin padre se reporta como huerfana.

        Returns:
            Dict[str, Any]: Metricas de perfilamiento y estado de cumplimiento.
        """
        total_rows = len(df)
        if total_rows == 0:
            profile = {
                "tabla": table_name,
                "total_registros": 0,
                "duplicados_clave": 0,
                "nulos_totales": 0,
                "estado_calidad": "ALERTA: Tabla vacia",
                "detalles": []
            }
            self.validation_results.append(profile)
            logger.warning(f"Tabla {table_name} sin registros para validar.")
            return profile

        # 1. Unicidad de clave sustituta / primaria
        duplicates_key = df.duplicated(subset=[key_column]).sum()

        # 2. Conteo de nulos
        null_counts = df.isnull().sum().to_dict()
        total_nulls = sum(null_counts.values())

        # 3. Validacion de columnas requeridas (no vacias ni nulas)
        empty_issues = []
        for col in required_columns:
            if col in df.columns:
                empty_count = (df[col].astype(str).str.strip() == "").sum() + df[col].isnull().sum()
                if empty_count > 0:
                    empty_issues.append(f"Columna {col} tiene {empty_count} valores vacios.")
            else:
                empty_issues.append(f"Columna obligatoria {col} ausente.")

        # 3b. Integridad referencial: FK nula o sin registro padre
        for fk_col, (ref_df, ref_col) in (foreign_keys or {}).items():
            if fk_col not in df.columns:
                continue
            valid = set(ref_df[ref_col].dropna()) if ref_df is not None and not ref_df.empty else set()
            orphans = int((~df[fk_col].isin(valid)).sum())
            if orphans > 0:
                empty_issues.append(f"{orphans} registros con {fk_col} nula o sin registro en la dimension referenciada.")

        # 3c. Columnas con datos faltantes (informativo: no cambia el estado, pero queda visible)
        info = []
        for col, n in null_counts.items():
            if n > 0 and col not in required_columns:
                info.append(f"Info: {col} sin dato en {n} de {total_rows} registros ({n / total_rows:.0%}).")

        # 4. Deteccion de valores atipicos (outliers) en metricas conocidas
        outliers = []
        if "duracion_periodos" in df.columns:
            periodos = pd.to_numeric(df["duracion_periodos"], errors="coerce").astype("float64")
            anormales = df[(periodos < 2) | (periodos > 16)]
            if len(anormales) > 0:
                outliers.append(f"{len(anormales)} registros con duracion de periodos fuera de rango academico (2 a 16).")

        if "creditos_totales" in df.columns:
            creditos = pd.to_numeric(df["creditos_totales"], errors="coerce").astype("float64")
            cred_atipicos = df[(creditos < 30) | (creditos > 400)]
            if len(cred_atipicos) > 0:
                outliers.append(f"{len(cred_atipicos)} registros con creditos fuera de rango (30 a 400).")

        # 5. Validacion de formato de correo electronico
        email_cols = [c for c in df.columns if "correo" in c or "email" in c]
        for ec in email_cols:
            invalid_emails = 0
            for val in df[ec].dropna():
                if val and val != "No especificado":
                    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", str(val)):
                        invalid_emails += 1
            if invalid_emails > 0:
                empty_issues.append(f"{invalid_emails} correos con formato no estandar en {ec}.")

        # Evaluacion general de calidad
        aprobado = (duplicates_key == 0) and (len(empty_issues) == 0) and (len(outliers) == 0)
        estado = "CONFORME" if aprobado else "OBSERVACIONES DETECTADAS"

        profile = {
            "tabla": table_name,
            "total_registros": total_rows,
            "duplicados_clave": int(duplicates_key),
            "nulos_totales": int(total_nulls),
            "estado_calidad": estado,
            "observaciones": empty_issues + outliers + info,
        }

        self.validation_results.append(profile)
        logger.info(f"Perfilamiento de {table_name}: {total_rows} filas | Clave unica: {duplicates_key == 0} | Estado: {estado}")
        return profile

    def generate_markdown_report(self) -> str:
        """Genera un reporte academico en formato Markdown con el perfil de calidad.

        Returns:
            str: Documento Markdown estructurado con tablas de diagnostico.
        """
        lines = [
            "# Reporte de Calidad y Perfilamiento de Datos",
            "",
            "## Resumen Ejecutivo de Auditoria",
            "El presente reporte consolida los controles aplicados sobre el conjunto de dimensiones y tablas de hechos del Data Warehouse institucional de la EPN.",
            "",
            "| Tabla | Registros | Claves Duplicadas | Nulos Totales | Estado |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]

        for res in self.validation_results:
            lines.append(
                f"| {res['tabla']} | {res['total_registros']} | {res['duplicados_clave']} | {res['nulos_totales']} | {res['estado_calidad']} |"
            )

        lines.append("")
        lines.append("## Detalle de Observaciones y Reglas Evaluadas")

        for res in self.validation_results:
            lines.append(f"### {res['tabla']}")
            obs = res.get("observaciones", [])
            if obs:
                for o in obs:
                    lines.append(f"- {o}")
            else:
                lines.append("- Todos los controles de integridad, tipo de dato y unicidad resultaron conformes.")
            lines.append("")

        return "\n".join(lines)
