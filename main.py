import tkinter as tk
from pathlib import Path

from repository import TransactionRepository
from finance_service import FinanceService
from app import AppFinanzas


def main() -> None:
    ruta_datos = Path(__file__).parent / "data" / "historial.json"
    repository = TransactionRepository(ruta_datos)
    service = FinanceService(repository)
    root = tk.Tk()
    AppFinanzas(root, service)
    root.mainloop()


if __name__ == "__main__":
    main()
