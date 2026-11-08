from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


TIPOS_VALIDOS = {"Ingreso", "Gasto"}


@dataclass(frozen=True)
class Transaccion:
    tipo: str
    monto: float
    categoria: str
    fecha: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS_VALIDOS:
            raise ValueError(f"Tipo inválido '{self.tipo}'. Debe ser: {TIPOS_VALIDOS}")
        if self.monto <= 0:
            raise ValueError(f"El monto debe ser mayor a cero. Recibido: {self.monto}")
        if not self.categoria.strip():
            raise ValueError("La categoría no puede estar vacía.")

    def __str__(self) -> str:
        fecha_str = self.fecha.strftime("%Y-%m-%d %H:%M")
        return (
            f"[{fecha_str}] {self.tipo} | "
            f"Categoría: {self.categoria} | "
            f"Monto: ${self.monto:.2f}"
        )

    def to_dict(self) -> dict:
        return {
            "tipo": self.tipo,
            "monto": self.monto,
            "categoria": self.categoria,
            "fecha": self.fecha.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Transaccion:
        return cls(
            tipo=data["tipo"],
            monto=data["monto"],
            categoria=data["categoria"],
            fecha=datetime.fromisoformat(data["fecha"]),
        )
