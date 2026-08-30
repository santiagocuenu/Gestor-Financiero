import tkinter as tk
from pathlib import Path

from gestor_financiero.services.finance_service import FinanceService
from gestor_financiero.services.repository import TransactionRepository
from gestor_financiero.ui.app import AppFinanzas


def main() -> None:
    ruta_datos = Path(__file__).parent / "gestor_financiero" / "data" / "historial.json"
    repository = TransactionRepository(ruta_datos)
    service = FinanceService(repository)
    root = tk.Tk()
    AppFinanzas(root, service)
    root.mainloop()


if __name__ == "__main__":
    main()
