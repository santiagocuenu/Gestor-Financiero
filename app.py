from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from gestor_financiero.domain.exceptions import PersistenciaError
from gestor_financiero.domain.transaction import Transaccion
from gestor_financiero.services.finance_service import FinanceService

TEMA = {
    "principal":    "#7B2CBF",
    "secundario":   "#C77DFF",
    "ingreso":      "#06D6A0",
    "gasto":        "#EF476F",
    "fondo":        "#1A0E2E",
    "fondo_entry":  "#2A1A4E",
    "texto":        "#FFFFFF",
    "texto_oscuro": "#000000",
}


class AppFinanzas:
    """Capa de presentación. Solo construye la UI y delega al FinanceService."""

    def __init__(self, root: tk.Tk, service: FinanceService) -> None:
        self._service = service
        self._root = root
        self._root.title("Gestor Financiero")
        self._root.geometry("600x750")
        self._root.configure(bg=TEMA["principal"])
        self._root.resizable(False, False)

        self._construir_header()
        self._construir_formulario()
        self._construir_botones()
        self._construir_pantalla()

    def _construir_header(self) -> None:
        frame = tk.Frame(self._root, bg=TEMA["principal"])
        frame.pack(fill="x", pady=(0, 10))
        tk.Label(
            frame, text="GESTOR FINANCIERO",
            font=("Segoe UI", 24, "bold"),
            bg=TEMA["principal"], fg=TEMA["texto"],
        ).pack(pady=15)
        tk.Label(
            frame, text="Tu historial financiero, guardado y organizado",
            font=("Verdana", 10),
            bg=TEMA["principal"], fg=TEMA["secundario"],
        ).pack()

    def _construir_formulario(self) -> None:
        frame = tk.Frame(self._root, bg=TEMA["principal"])
        frame.pack(fill="x", padx=20)

        tk.Label(frame, text="1. Seleccione el tipo:",
                 font=("Segoe UI", 11, "bold"),
                 bg=TEMA["principal"], fg=TEMA["texto"]).pack(anchor="w", pady=(10, 4))
        self._combo_tipo = ttk.Combobox(
            frame, values=["Ingreso", "Gasto"],
            state="readonly", width=30, font=("Segoe UI", 10),
        )
        self._combo_tipo.pack(anchor="w", fill="x", pady=(0, 12))

        tk.Label(frame, text="2. Ingrese el monto:",
                 font=("Segoe UI", 11, "bold"),
                 bg=TEMA["principal"], fg=TEMA["texto"]).pack(anchor="w", pady=(0, 4))
        self._entry_monto = tk.Entry(
            frame, font=("Calibri", 11), width=30,
            bg=TEMA["fondo_entry"], fg=TEMA["texto"],
            insertbackground=TEMA["secundario"],
        )
        self._entry_monto.pack(anchor="w", fill="x", pady=(0, 12))

        tk.Label(frame, text="3. Ingrese la categoría:",
                 font=("Segoe UI", 11, "bold"),
                 bg=TEMA["principal"], fg=TEMA["texto"]).pack(anchor="w", pady=(0, 4))
        self._entry_categoria = tk.Entry(
            frame, font=("Calibri", 11), width=30,
            bg=TEMA["fondo_entry"], fg=TEMA["texto"],
            insertbackground=TEMA["secundario"],
        )
        self._entry_categoria.pack(anchor="w", fill="x", pady=(0, 16))

    def _construir_botones(self) -> None:
        frame = tk.Frame(self._root, bg=TEMA["principal"])
        frame.pack(fill="x", padx=20)

        botones = [
            ("Registrar transacción",  TEMA["secundario"], TEMA["texto_oscuro"], self._registrar),
            ("Ver historial",           TEMA["ingreso"],    TEMA["texto_oscuro"], self._ver_historial),
            ("Ver resumen y balance",   TEMA["gasto"],      TEMA["texto"],        self._ver_resumen),
            ("Gráfico por categoría",   "#9D4EDD",          TEMA["texto"],        self._ver_grafico),
            ("Exportar a CSV",          "#3A86FF",          TEMA["texto"],        self._exportar_csv),
        ]

        for texto, bg, fg, comando in botones:
            tk.Button(
                frame, text=texto, bg=bg, fg=fg,
                font=("Segoe UI", 10, "bold"),
                command=comando, relief="flat", padx=10, pady=8,
            ).pack(fill="x", pady=3)

    def _construir_pantalla(self) -> None:
        frame = tk.Frame(self._root, bg=TEMA["principal"])
        frame.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        tk.Label(frame, text="Resultados:",
                 font=("Segoe UI", 11, "bold"),
                 bg=TEMA["principal"], fg=TEMA["texto"]).pack(anchor="w", pady=(0, 5))
        self._pantalla = tk.Text(
            frame, height=10, width=50, state="disabled",
            bg=TEMA["fondo"], fg=TEMA["texto"],
            font=("Consolas", 9), relief="flat", padx=10, pady=10,
        )
        self._pantalla.pack(fill="both", expand=True)

    def _registrar(self) -> None:
        tipo = self._combo_tipo.get()
        monto_str = self._entry_monto.get().strip()
        categoria = self._entry_categoria.get().strip()

        if not tipo:
            messagebox.showerror("Error", "Seleccione el tipo: Ingreso o Gasto.")
            return
        try:
            monto = float(monto_str)
        except ValueError:
            messagebox.showerror("Error", "El monto debe ser un número. Ej: 150000")
            return
        try:
            transaccion = Transaccion(tipo=tipo, monto=monto, categoria=categoria)
            self._service.registrar_transaccion(transaccion)
        except ValueError as e:
            messagebox.showerror("Error de validación", str(e))
            return
        except PersistenciaError as e:
            messagebox.showerror("Error de guardado", str(e))
            return

        messagebox.showinfo("Éxito", "¡Transacción registrada y guardada!")
        self._limpiar_formulario()

    def _ver_historial(self) -> None:
        historial = self._service.historial
        if not historial:
            self._mostrar("Aún no hay transacciones registradas.")
            return
        lineas = ["  Historial de movimientos\n" + "─" * 45]
        for t in historial:
            lineas.append(str(t))
        self._mostrar("\n".join(lineas))

    def _ver_resumen(self) -> None:
        if not self._service.historial:
            self._mostrar("Registre al menos una transacción para ver el resumen.")
            return
        estado = self._service.evaluar_estado()
        texto = (
            "  Resumen Financiero\n"
            + "─" * 35 + "\n"
            + f"Total ingresos:  ${self._service.total_ingresos:>12.2f}\n"
            + f"Total gastos:    ${self._service.total_gastos:>12.2f}\n"
            + f"Balance general: ${self._service.balance:>12.2f}\n"
            + "─" * 35 + "\n"
            + f"Estado: {estado.upper()}"
        )
        self._mostrar(texto)

    def _ver_grafico(self) -> None:
        gastos = self._service.gastos_por_categoria()
        ingresos = self._service.ingresos_por_categoria()

        if not gastos and not ingresos:
            self._mostrar("Registre transacciones para ver el gráfico.")
            return

        ventana = tk.Toplevel(self._root)
        ventana.title("Análisis por Categoría")
        ventana.configure(bg=TEMA["fondo"])

        n = (1 if gastos else 0) + (1 if ingresos else 0)
        fig, axes = plt.subplots(1, n, figsize=(6 * n, 5))
        fig.patch.set_facecolor(TEMA["fondo"])
        if n == 1:
            axes = [axes]

        idx = 0
        for datos, titulo, colores in [
            (gastos, "Gastos por categoría", plt.cm.Set2.colors),
            (ingresos, "Ingresos por categoría", plt.cm.Set3.colors),
        ]:
            if not datos:
                continue
            ax = axes[idx]
            ax.set_facecolor(TEMA["fondo"])
            _, texts, autotexts = ax.pie(
                datos.values(), labels=datos.keys(),
                autopct="%1.1f%%", colors=colores, startangle=90,
            )
            for t in texts + autotexts:
                t.set_color(TEMA["texto"])
            ax.set_title(titulo, color=TEMA["texto"], fontsize=13, pad=15)
            idx += 1

        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=ventana)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _exportar_csv(self) -> None:
        if not self._service.historial:
            self._mostrar("No hay transacciones para exportar.")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv")],
            title="Guardar historial como CSV",
            initialfile="historial_financiero.csv",
        )
        if not ruta:
            return
        try:
            self._service.exportar_csv(Path(ruta))
            messagebox.showinfo("Éxito", f"Historial exportado:\n{ruta}")
        except PersistenciaError as e:
            messagebox.showerror("Error al exportar", str(e))

    def _mostrar(self, texto: str) -> None:
        self._pantalla.config(state="normal")
        self._pantalla.delete("1.0", tk.END)
        self._pantalla.insert(tk.END, texto + "\n")
        self._pantalla.config(state="disabled")

    def _limpiar_formulario(self) -> None:
        self._entry_monto.delete(0, tk.END)
        self._entry_categoria.delete(0, tk.END)
        self._combo_tipo.set("")
