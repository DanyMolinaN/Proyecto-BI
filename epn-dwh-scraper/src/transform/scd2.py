"""
Aplicacion de Dimension de Cambio Lento Tipo 2 (SCD2) para dim_autoridad.

Compara las autoridades recien extraidas contra lo ya cargado en el Data Warehouse:
- Sin cambios: se conserva la fila vigente.
- Atributos cambiados: se cierra la fila vigente (fecha_fin, es_vigente = 0) y se abre una nueva version.
- Autoridad ausente en la fuente: se cierra la fila vigente (dejó el cargo).
- Autoridad nueva: se inserta como vigente.

La tabla de hechos se reconcilia igual: conserva el historial previo y agrega las
designaciones de las versiones vigentes, con claves recalculadas segun la version.
"""

from datetime import datetime
from typing import Optional, Tuple
import pandas as pd

from src.utils.helpers import generate_surrogate_key

TRACKED_COLUMNS = ["titulo_academico", "correo_contacto", "biografia"]
OPEN_END_DATE = "9999-12-31"


def _same(a, b) -> bool:
    """Compara dos valores tratando NULL/NaN/vacio como equivalentes."""
    a_null = a is None or (not isinstance(a, str) and pd.isna(a)) or a == ""
    b_null = b is None or (not isinstance(b, str) and pd.isna(b)) or b == ""
    if a_null and b_null:
        return True
    return a == b


def apply_scd2(
    new_dim: pd.DataFrame,
    new_fact: pd.DataFrame,
    existing_dim: Optional[pd.DataFrame],
    existing_fact: Optional[pd.DataFrame],
    today: Optional[datetime] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Fusiona la captura actual con el historial existente de autoridades.

    Args:
        new_dim (pd.DataFrame): dim_autoridad de la captura actual (una fila por autoridad).
        new_fact (pd.DataFrame): fact_designacion_autoridades de la captura actual.
        existing_dim (Optional[pd.DataFrame]): dim_autoridad ya cargada, o None en la primera corrida.
        existing_fact (Optional[pd.DataFrame]): hechos ya cargados, o None en la primera corrida.
        today (Optional[datetime]): Fecha de proceso (inyectable para pruebas).

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (dim_autoridad completa con historial, hechos completos).
    """
    if new_dim is None or new_dim.empty:
        return new_dim, new_fact

    today_str = (today or datetime.now()).strftime("%Y-%m-%d")
    today_key = int((today or datetime.now()).strftime("%Y%m%d"))

    if existing_dim is None or existing_dim.empty:
        return new_dim, new_fact

    existing_dim = existing_dim.copy()
    # Mapa autoridad_key (de la captura) -> autoridad_key resultante tras SCD2
    key_map = {}
    rows_to_add = []
    incoming_names = set(new_dim["nombre_completo"])

    for _, inc in new_dim.iterrows():
        name = inc["nombre_completo"]
        current_mask = (existing_dim["nombre_completo"] == name) & (existing_dim["es_vigente"] == 1)
        if not current_mask.any():
            rows_to_add.append(inc.to_dict())
            key_map[inc["autoridad_key"]] = inc["autoridad_key"]
            continue

        current = existing_dim[current_mask].iloc[0]
        changed = any(not _same(inc[c], current[c]) for c in TRACKED_COLUMNS)
        if not changed:
            key_map[inc["autoridad_key"]] = current["autoridad_key"]
            continue

        existing_dim.loc[current_mask, "es_vigente"] = 0
        existing_dim.loc[current_mask, "fecha_fin_vigencia"] = today_str
        new_row = inc.to_dict()
        new_row["autoridad_key"] = generate_surrogate_key("autoridad", name, today_str)
        new_row["fecha_inicio_vigencia"] = today_str
        new_row["fecha_fin_vigencia"] = OPEN_END_DATE
        new_row["es_vigente"] = 1
        rows_to_add.append(new_row)
        key_map[inc["autoridad_key"]] = new_row["autoridad_key"]

    # Autoridades que dejaron de aparecer en la fuente: se cierra su vigencia
    gone = (existing_dim["es_vigente"] == 1) & (~existing_dim["nombre_completo"].isin(incoming_names))
    existing_dim.loc[gone, "es_vigente"] = 0
    existing_dim.loc[gone, "fecha_fin_vigencia"] = today_str

    dim = pd.concat([existing_dim, pd.DataFrame(rows_to_add)], ignore_index=True) if rows_to_add else existing_dim

    # Hechos: reasignar claves a la version correspondiente y conservar el historial
    fact = new_fact.copy()
    fact["autoridad_key"] = fact["autoridad_key"].map(key_map)
    fact["designacion_key"] = fact.apply(
        lambda r: generate_surrogate_key("designacion", r["autoridad_key"], r["cargo_key"]), axis=1
    )
    if existing_fact is not None and not existing_fact.empty:
        fact = pd.concat([existing_fact, fact], ignore_index=True)
        fact = fact.drop_duplicates(subset=["designacion_key"], keep="last").reset_index(drop=True)

    return dim.reset_index(drop=True), fact
