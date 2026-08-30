from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from gestor_financiero.domain.transaction import Transaccion
from gestor_financiero.services.repository import TransactionRepository


class FinanceService:
    """Lógica de negocio: calcula métricas y delega persistencia al repositorio."""

    def __init__(self, repository: TransactionRepository) -> None:
        self._repo = repository
        self._historial: list[Transaccion] = self._repo.cargar()
        self._total_ingresos: float = 0.0
        self._total_gastos: float = 0.0
        self._balance: float = 0.0
        self._recalcular()

    @property
    def historial(self) -> list[Transaccion]:
        return list(self._historial)

    @property
    def total_ingresos(self) -> float:
        return self._total_ingresos

    @property
    def total_gastos(self) -> float:
        return self._total_gastos

    @property
    def balance(self) -> float:
        return self._balance

    def registrar_transaccion(self, transaccion: Transaccion) -> None:
        self._historial.append(transaccion)
        self._actualizar_incrementalmente(transaccion)
        self._repo.guardar(self._historial)

    def evaluar_estado(self) -> str:
        if self._balance < 0:
            return "Déficit"
        if self._balance > 0:
            return "Superávit"
        return "Neutral"

    def gastos_por_categoria(self) -> dict[str, float]:
        totales: dict[str, float] = defaultdict(float)
        for t in self._historial:
            if t.tipo == "Gasto":
                totales[t.categoria] += t.monto
        return dict(sorted(totales.items(), key=lambda x: x[1], reverse=True))

    def ingresos_por_categoria(self) -> dict[str, float]:
        totales: dict[str, float] = defaultdict(float)
        for t in self._historial:
            if t.tipo == "Ingreso":
                totales[t.categoria] += t.monto
        return dict(sorted(totales.items(), key=lambda x: x[1], reverse=True))

    def exportar_csv(self, ruta: Path) -> None:
        campos = ["fecha", "tipo", "categoria", "monto"]
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            for t in self._historial:
                writer.writerow({
                    "fecha": t.fecha.strftime("%Y-%m-%d %H:%M"),
                    "tipo": t.tipo,
                    "categoria": t.categoria,
                    "monto": f"{t.monto:.2f}",
                })

    def _recalcular(self) -> None:
        """Recalcula totales al iniciar (carga desde JSON)."""
        self._total_ingresos = 0.0
        self._total_gastos = 0.0
        for t in self._historial:
            self._actualizar_incrementalmente(t)

    def _actualizar_incrementalmente(self, transaccion: Transaccion) -> None:
        """Actualiza acumulados en O(1) sin recorrer el historial."""
        if transaccion.tipo == "Ingreso":
            self._total_ingresos += transaccion.monto
        else:
            self._total_gastos += transaccion.monto
        self._balance = self._total_ingresos - self._total_gastos
