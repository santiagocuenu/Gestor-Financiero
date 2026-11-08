from pathlib import Path

from formato import formatear_monto
from repository import TransactionRepository
from finance_service import FinanceService


def generar_resumen(ruta_datos):
    """Devuelve el resumen del historial como un solo texto."""
    repositorio = TransactionRepository(ruta_datos)
    servicio = FinanceService(repositorio)

    lineas = [
        "Resumen financiero",
        f"Ingresos: {formatear_monto(servicio.total_ingresos)}",
        f"Gastos: {formatear_monto(servicio.total_gastos)}",
        f"Balance: {formatear_monto(servicio.balance)}",
        f"Estado: {servicio.evaluar_estado()}",
    ]

    gastos = servicio.gastos_por_categoria()
    if gastos:
        lineas.append("Gastos por categoría:")
        for categoria, total in gastos.items():
            lineas.append(f"  {categoria}: {formatear_monto(total)}")
    else:
        lineas.append("Sin gastos registrados")

    return "\n".join(lineas)


def main():
    ruta_datos = Path(__file__).parent / "data" / "historial.json"
    try:
        print(generar_resumen(ruta_datos))
    except RuntimeError as e:
        print(f"No se pudo generar el resumen: {e}")


if __name__ == "__main__":
    main()