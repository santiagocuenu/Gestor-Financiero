from __future__ import annotations

import json
from pathlib import Path

from gestor_financiero.domain.exceptions import PersistenciaError
from gestor_financiero.domain.transaction import Transaccion


class TransactionRepository:
    """Gestiona la persistencia del historial en un archivo JSON."""

    def __init__(self, ruta_archivo: Path) -> None:
        self._ruta = ruta_archivo
        self._ruta.parent.mkdir(parents=True, exist_ok=True)

    def cargar(self) -> list[Transaccion]:
        if not self._ruta.exists():
            return []
        try:
            with open(self._ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
            return [Transaccion.from_dict(d) for d in datos]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise PersistenciaError(f"Error al leer el historial: {e}") from e

    def guardar(self, transacciones: list[Transaccion]) -> None:
        try:
            with open(self._ruta, "w", encoding="utf-8") as f:
                json.dump(
                    [t.to_dict() for t in transacciones],
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except OSError as e:
            raise PersistenciaError(f"Error al guardar el historial: {e}") from e
