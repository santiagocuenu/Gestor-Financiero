from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from finance_service import FinanceService
from transaction import Transaccion


TEMA = {
    "fondo":        "#0F172A",   # fondo general
    "sidebar":      "#111827",
    "tarjeta":      "#1E293B",
    "tarjeta_alt":  "#273449",
    "borde":        "#334155",
    "acento":       "#6366F1",
    "acento_hover": "#818CF8",
    "ingreso":      "#22C55E",
    "gasto":        "#F43F5E",
    "neutral":      "#F59E0B",
    "texto":        "#F1F5F9",
    "texto_suave":  "#94A3B8",
    "texto_tenue":  "#64748B",
}

PALETA_GRAFICOS = ["#6366F1", "#22C55E", "#F59E0B", "#F43F5E", "#06B6D4",
                   "#A855F7", "#EC4899", "#84CC16", "#14B8A6", "#F97316"]

FUENTE = "Segoe UI"


def fuente(tam: int = 10, peso: str = "normal") -> tuple:
    return (FUENTE, tam, peso)


def monto_corto(monto: float) -> str:
    """Formato compacto para tarjetas: $2.000.000"""
    return "$" + f"{monto:,.0f}".replace(",", ".")


# ──────────────────────────────────────────────────────────────────────
#  Componentes reutilizables
# ──────────────────────────────────────────────────────────────────────
class Boton(tk.Label):
    """Botón plano con efecto hover (tk.Button no permite estilos modernos en Windows)."""

    def __init__(self, master, texto: str, comando, bg: str = TEMA["acento"],
                 bg_hover: str = TEMA["acento_hover"], fg: str = TEMA["texto"],
                 tam: int = 10, padx: int = 18, pady: int = 10, anchor: str = "center") -> None:
        super().__init__(master, text=texto, bg=bg, fg=fg, font=fuente(tam, "bold"),
                         padx=padx, pady=pady, cursor="hand2", anchor=anchor)
        self._bg, self._bg_hover, self._comando = bg, bg_hover, comando
        self.bind("<Enter>", lambda _: self.config(bg=self._bg_hover))
        self.bind("<Leave>", lambda _: self.config(bg=self._bg))
        self.bind("<Button-1>", lambda _: self._comando())

    def set_colores(self, bg: str, bg_hover: str, fg: str | None = None) -> None:
        self._bg, self._bg_hover = bg, bg_hover
        self.config(bg=bg, fg=fg or self.cget("fg"))


class Tarjeta(tk.Frame):
    """Contenedor con fondo elevado y borde sutil."""

    def __init__(self, master, padding: int = 20, **kw) -> None:
        super().__init__(master, bg=TEMA["tarjeta"], highlightthickness=1,
                         highlightbackground=TEMA["borde"], **kw)
        self.cuerpo = tk.Frame(self, bg=TEMA["tarjeta"])
        self.cuerpo.pack(fill="both", expand=True, padx=padding, pady=padding)


class CampoTexto(tk.Frame):
    """Entry con borde que se ilumina al recibir foco."""

    def __init__(self, master, placeholder: str = "") -> None:
        super().__init__(master, bg=TEMA["borde"], padx=1, pady=1)
        self._placeholder = placeholder
        self.entry = tk.Entry(self, font=fuente(11), bg=TEMA["fondo"], fg=TEMA["texto"],
                              insertbackground=TEMA["texto"], relief="flat", bd=0)
        self.entry.pack(fill="x", ipady=8, ipadx=10)
        self.entry.bind("<FocusIn>", self._al_enfocar)
        self.entry.bind("<FocusOut>", self._al_desenfocar)
        self._mostrar_placeholder()

    def _mostrar_placeholder(self) -> None:
        if not self.entry.get():
            self.entry.insert(0, self._placeholder)
            self.entry.config(fg=TEMA["texto_tenue"])

    def _al_enfocar(self, _=None) -> None:
        self.config(bg=TEMA["acento"])
        if self.entry.cget("fg") == TEMA["texto_tenue"]:
            self.entry.delete(0, tk.END)
            self.entry.config(fg=TEMA["texto"])

    def _al_desenfocar(self, _=None) -> None:
        self.config(bg=TEMA["borde"])
        self._mostrar_placeholder()

    def get(self) -> str:
        if self.entry.cget("fg") == TEMA["texto_tenue"]:
            return ""
        return self.entry.get().strip()

    def limpiar(self) -> None:
        self.entry.delete(0, tk.END)
        self._mostrar_placeholder()


class Toast:
    """Notificación flotante que desaparece sola (reemplaza a los messagebox)."""

    def __init__(self, root: tk.Tk) -> None:
        self._root = root
        self._actual: tk.Frame | None = None
        self._id_after: str | None = None

    def mostrar(self, mensaje: str, tipo: str = "ok") -> None:
        if self._actual is not None:
            self._actual.destroy()
            if self._id_after:
                self._root.after_cancel(self._id_after)
        color = {"ok": TEMA["ingreso"], "error": TEMA["gasto"]}.get(tipo, TEMA["acento"])
        icono = "✓" if tipo == "ok" else "!"
        marco = tk.Frame(self._root, bg=TEMA["tarjeta_alt"], highlightthickness=1,
                         highlightbackground=color)
        tk.Label(marco, text=icono, bg=color, fg=TEMA["fondo"], font=fuente(12, "bold"),
                 width=3).pack(side="left", fill="y")
        tk.Label(marco, text=mensaje, bg=TEMA["tarjeta_alt"], fg=TEMA["texto"],
                 font=fuente(10), padx=14, pady=12, justify="left",
                 wraplength=320).pack(side="left")
        marco.place(relx=1.0, rely=1.0, x=-24, y=-24, anchor="se")
        self._actual = marco
        self._id_after = self._root.after(3200, marco.destroy)


# ──────────────────────────────────────────────────────────────────────
#  Aplicación
# ──────────────────────────────────────────────────────────────────────
class AppFinanzas:
    """Capa de presentación. Delega toda la lógica a FinanceService."""

    def __init__(self, root: tk.Tk, service: FinanceService) -> None:
        self._service = service
        self._root = root
        self._root.title("Gestor Financiero")
        self._root.geometry("1180x740")
        self._root.minsize(1000, 640)
        self._root.configure(bg=TEMA["fondo"])

        self._tipo = tk.StringVar(value="Gasto")
        self._filtro = tk.StringVar(value="Todos")
        self._pagina_actual = "panel"
        self._toast = Toast(root)
        self._configurar_estilos()

        self._construir_sidebar()
        self._contenedor = tk.Frame(root, bg=TEMA["fondo"])
        self._contenedor.pack(side="left", fill="both", expand=True)

        self._paginas = {
            "panel":     self._crear_pagina_panel(),
            "historial": self._crear_pagina_historial(),
            "analisis":  self._crear_pagina_analisis(),
        }
        self._ir_a("panel")

    # ── Estilos ttk ───────────────────────────────────────────────────
    def _configurar_estilos(self) -> None:
        estilo = ttk.Style(self._root)
        estilo.theme_use("clam")
        estilo.configure("Treeview", background=TEMA["tarjeta"], fieldbackground=TEMA["tarjeta"],
                         foreground=TEMA["texto"], rowheight=34, borderwidth=0, font=fuente(10))
        estilo.configure("Treeview.Heading", background=TEMA["tarjeta_alt"],
                         foreground=TEMA["texto_suave"], relief="flat", font=fuente(9, "bold"),
                         padding=(10, 8))
        estilo.map("Treeview.Heading", background=[("active", TEMA["borde"])])
        estilo.map("Treeview", background=[("selected", TEMA["acento"])],
                   foreground=[("selected", TEMA["texto"])])
        estilo.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        estilo.configure("Vertical.TScrollbar", background=TEMA["borde"], troughcolor=TEMA["tarjeta"],
                         bordercolor=TEMA["tarjeta"], lightcolor=TEMA["borde"],
                         darkcolor=TEMA["borde"], arrowcolor=TEMA["texto_suave"], relief="flat")
        estilo.map("Vertical.TScrollbar", background=[("active", TEMA["texto_tenue"])])
        estilo.configure("TCombobox", fieldbackground=TEMA["fondo"], background=TEMA["tarjeta_alt"],
                         foreground=TEMA["texto"], arrowcolor=TEMA["texto_suave"],
                         bordercolor=TEMA["borde"], lightcolor=TEMA["borde"],
                         darkcolor=TEMA["borde"], padding=8, selectbackground=TEMA["fondo"],
                         selectforeground=TEMA["texto"])
        estilo.map("TCombobox", fieldbackground=[("readonly", TEMA["fondo"])],
                   bordercolor=[("focus", TEMA["acento"])])
        self._root.option_add("*TCombobox*Listbox.background", TEMA["tarjeta_alt"])
        self._root.option_add("*TCombobox*Listbox.foreground", TEMA["texto"])
        self._root.option_add("*TCombobox*Listbox.selectBackground", TEMA["acento"])
        self._root.option_add("*TCombobox*Listbox.font", fuente(10))

    # ── Navegación lateral ────────────────────────────────────────────
    def _construir_sidebar(self) -> None:
        barra = tk.Frame(self._root, bg=TEMA["sidebar"], width=230)
        barra.pack(side="left", fill="y")
        barra.pack_propagate(False)

        logo = tk.Frame(barra, bg=TEMA["sidebar"])
        logo.pack(fill="x", padx=22, pady=(28, 36))
        tk.Label(logo, text="◆", bg=TEMA["sidebar"], fg=TEMA["acento"],
                 font=fuente(20, "bold")).pack(side="left")
        textos = tk.Frame(logo, bg=TEMA["sidebar"])
        textos.pack(side="left", padx=10)
        tk.Label(textos, text="Gestor", bg=TEMA["sidebar"], fg=TEMA["texto"],
                 font=fuente(14, "bold")).pack(anchor="w")
        tk.Label(textos, text="Financiero", bg=TEMA["sidebar"], fg=TEMA["texto_suave"],
                 font=fuente(9)).pack(anchor="w")

        tk.Label(barra, text="MENÚ", bg=TEMA["sidebar"], fg=TEMA["texto_tenue"],
                 font=fuente(8, "bold")).pack(anchor="w", padx=24, pady=(0, 8))

        self._nav: dict[str, Boton] = {}
        for clave, texto in [("panel", "▦   Panel"), ("historial", "☰   Historial"),
                             ("analisis", "◔   Análisis")]:
            b = Boton(barra, texto, lambda c=clave: self._ir_a(c), bg=TEMA["sidebar"],
                      bg_hover=TEMA["tarjeta"], fg=TEMA["texto_suave"], tam=10,
                      anchor="w", padx=16, pady=11)
            b.pack(fill="x", padx=12, pady=2)
            self._nav[clave] = b

        pie = tk.Frame(barra, bg=TEMA["sidebar"])
        pie.pack(side="bottom", fill="x", padx=12, pady=20)
        Boton(pie, "⤓  Exportar CSV", self._exportar_csv, bg=TEMA["tarjeta"],
              bg_hover=TEMA["borde"], fg=TEMA["texto"], tam=10).pack(fill="x")

    def _ir_a(self, clave: str) -> None:
        for nombre, pagina in self._paginas.items():
            pagina.pack_forget()
            activo = nombre == clave
            self._nav[nombre].set_colores(
                TEMA["acento"] if activo else TEMA["sidebar"],
                TEMA["acento"] if activo else TEMA["tarjeta"],
                TEMA["texto"] if activo else TEMA["texto_suave"],
            )
        self._pagina_actual = clave
        self._paginas[clave].pack(fill="both", expand=True, padx=32, pady=28)
        self._refrescar()

    def _encabezado(self, padre: tk.Frame, titulo: str, subtitulo: str) -> tk.Frame:
        fila = tk.Frame(padre, bg=TEMA["fondo"])
        fila.pack(fill="x", pady=(0, 22))
        izq = tk.Frame(fila, bg=TEMA["fondo"])
        izq.pack(side="left")
        tk.Label(izq, text=titulo, bg=TEMA["fondo"], fg=TEMA["texto"],
                 font=fuente(20, "bold")).pack(anchor="w")
        tk.Label(izq, text=subtitulo, bg=TEMA["fondo"], fg=TEMA["texto_suave"],
                 font=fuente(10)).pack(anchor="w", pady=(2, 0))
        return fila

    # ── Página: Panel ─────────────────────────────────────────────────
    def _crear_pagina_panel(self) -> tk.Frame:
        pagina = tk.Frame(self._contenedor, bg=TEMA["fondo"])
        fila = self._encabezado(pagina, "Panel general", "Resumen de tus finanzas")
        tk.Label(fila, text=datetime.now().strftime("%d/%m/%Y"), bg=TEMA["fondo"],
                 fg=TEMA["texto_suave"], font=fuente(10)).pack(side="right", anchor="n")

        # Tarjetas de métricas
        kpis = tk.Frame(pagina, bg=TEMA["fondo"])
        kpis.pack(fill="x")
        self._kpi = {}
        for i, (clave, titulo, color) in enumerate([
            ("ingresos", "Ingresos totales", TEMA["ingreso"]),
            ("gastos", "Gastos totales", TEMA["gasto"]),
            ("balance", "Balance", TEMA["acento"]),
        ]):
            kpis.columnconfigure(i, weight=1, uniform="kpi")
            t = Tarjeta(kpis)
            t.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 8, 0 if i == 2 else 8))
            tk.Frame(t, bg=color, height=3).place(relx=0, rely=0, relwidth=1)
            tk.Label(t.cuerpo, text=titulo.upper(), bg=TEMA["tarjeta"], fg=TEMA["texto_suave"],
                     font=fuente(8, "bold")).pack(anchor="w")
            valor = tk.Label(t.cuerpo, text="$0", bg=TEMA["tarjeta"], fg=TEMA["texto"],
                             font=fuente(22, "bold"))
            valor.pack(anchor="w", pady=(6, 4))
            detalle = tk.Label(t.cuerpo, text="", bg=TEMA["tarjeta"], fg=color, font=fuente(9))
            detalle.pack(anchor="w")
            self._kpi[clave] = (valor, detalle)

        # Formulario + movimientos recientes
        abajo = tk.Frame(pagina, bg=TEMA["fondo"])
        abajo.pack(fill="both", expand=True, pady=(18, 0))
        abajo.columnconfigure(0, weight=2, uniform="abajo")
        abajo.columnconfigure(1, weight=3, uniform="abajo")
        abajo.rowconfigure(0, weight=1)

        form = Tarjeta(abajo, padding=24)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self._construir_formulario(form.cuerpo)

        recientes = Tarjeta(abajo, padding=24)
        recientes.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        cab = tk.Frame(recientes.cuerpo, bg=TEMA["tarjeta"])
        cab.pack(fill="x", pady=(0, 12))
        tk.Label(cab, text="Movimientos recientes", bg=TEMA["tarjeta"], fg=TEMA["texto"],
                 font=fuente(13, "bold")).pack(side="left")
        ver = tk.Label(cab, text="Ver todo →", bg=TEMA["tarjeta"], fg=TEMA["acento_hover"],
                       font=fuente(9, "bold"), cursor="hand2")
        ver.pack(side="right")
        ver.bind("<Button-1>", lambda _: self._ir_a("historial"))
        self._lista_recientes = tk.Frame(recientes.cuerpo, bg=TEMA["tarjeta"])
        self._lista_recientes.pack(fill="both", expand=True)
        return pagina

    def _construir_formulario(self, padre: tk.Frame) -> None:
        tk.Label(padre, text="Nueva transacción", bg=TEMA["tarjeta"], fg=TEMA["texto"],
                 font=fuente(13, "bold")).pack(anchor="w")
        tk.Label(padre, text="Registra un ingreso o un gasto", bg=TEMA["tarjeta"],
                 fg=TEMA["texto_suave"], font=fuente(9)).pack(anchor="w", pady=(2, 18))

        # Selector segmentado Ingreso / Gasto
        self._etiqueta(padre, "Tipo")
        seg = tk.Frame(padre, bg=TEMA["fondo"], padx=4, pady=4)
        seg.pack(fill="x", pady=(0, 14))
        self._seg_botones: dict[str, Boton] = {}
        for tipo in ("Ingreso", "Gasto"):
            b = Boton(seg, tipo, lambda t=tipo: self._seleccionar_tipo(t), tam=10, pady=8)
            b.pack(side="left", fill="x", expand=True, padx=2)
            self._seg_botones[tipo] = b
        self._seleccionar_tipo(self._tipo.get())

        self._etiqueta(padre, "Monto")
        self._campo_monto = CampoTexto(padre, "Ej: 150000")
        self._campo_monto.pack(fill="x", pady=(0, 14))

        self._etiqueta(padre, "Categoría")
        self._combo_categoria = ttk.Combobox(padre, font=fuente(11))
        self._combo_categoria.pack(fill="x", pady=(0, 6))

        self._error = tk.Label(padre, text="", bg=TEMA["tarjeta"], fg=TEMA["gasto"],
                               font=fuente(9), anchor="w", justify="left", wraplength=320)
        self._error.pack(fill="x", pady=(0, 10))

        Boton(padre, "Registrar transacción", self._registrar, tam=11, pady=12).pack(fill="x")
        self._root.bind("<Return>", lambda _: self._registrar())

    def _etiqueta(self, padre: tk.Frame, texto: str) -> None:
        tk.Label(padre, text=texto, bg=TEMA["tarjeta"], fg=TEMA["texto_suave"],
                 font=fuente(9, "bold")).pack(anchor="w", pady=(0, 6))

    def _seleccionar_tipo(self, tipo: str) -> None:
        self._tipo.set(tipo)
        for nombre, b in self._seg_botones.items():
            if nombre == tipo:
                color = TEMA["ingreso"] if tipo == "Ingreso" else TEMA["gasto"]
                b.set_colores(color, color, TEMA["fondo"])
            else:
                b.set_colores(TEMA["fondo"], TEMA["tarjeta_alt"], TEMA["texto_suave"])

    def _fila_movimiento(self, padre: tk.Frame, t: Transaccion) -> None:
        es_ingreso = t.tipo == "Ingreso"
        color = TEMA["ingreso"] if es_ingreso else TEMA["gasto"]
        fila = tk.Frame(padre, bg=TEMA["tarjeta"])
        fila.pack(fill="x", pady=5)
        tk.Label(fila, text="↑" if es_ingreso else "↓", bg=TEMA["tarjeta_alt"], fg=color,
                 font=fuente(13, "bold"), width=3, pady=4).pack(side="left")
        info = tk.Frame(fila, bg=TEMA["tarjeta"])
        info.pack(side="left", padx=12)
        tk.Label(info, text=t.categoria.capitalize(), bg=TEMA["tarjeta"], fg=TEMA["texto"],
                 font=fuente(10, "bold")).pack(anchor="w")
        tk.Label(info, text=t.fecha.strftime("%d %b %Y · %H:%M"), bg=TEMA["tarjeta"],
                 fg=TEMA["texto_tenue"], font=fuente(8)).pack(anchor="w")
        signo = "+" if es_ingreso else "−"
        tk.Label(fila, text=f"{signo}{monto_corto(t.monto)}", bg=TEMA["tarjeta"], fg=color,
                 font=fuente(11, "bold")).pack(side="right")

    # ── Página: Historial ─────────────────────────────────────────────
    def _crear_pagina_historial(self) -> tk.Frame:
        pagina = tk.Frame(self._contenedor, bg=TEMA["fondo"])
        fila = self._encabezado(pagina, "Historial", "Todos tus movimientos registrados")

        filtros = tk.Frame(fila, bg=TEMA["tarjeta"], padx=4, pady=4)
        filtros.pack(side="right", anchor="n")
        self._botones_filtro: dict[str, Boton] = {}
        for f in ("Todos", "Ingresos", "Gastos"):
            b = Boton(filtros, f, lambda v=f: self._aplicar_filtro(v), tam=9, padx=14, pady=6)
            b.pack(side="left", padx=2)
            self._botones_filtro[f] = b

        tarjeta = Tarjeta(pagina, padding=0)
        tarjeta.pack(fill="both", expand=True)
        columnas = ("fecha", "tipo", "categoria", "monto")
        self._tabla = ttk.Treeview(tarjeta.cuerpo, columns=columnas, show="headings")
        for col, titulo, ancho, ancla in [
            ("fecha", "FECHA", 170, "w"), ("tipo", "TIPO", 120, "w"),
            ("categoria", "CATEGORÍA", 260, "w"), ("monto", "MONTO", 180, "e"),
        ]:
            self._tabla.heading(col, text=titulo, anchor=ancla)
            self._tabla.column(col, width=ancho, anchor=ancla)
        self._tabla.tag_configure("ingreso", foreground=TEMA["ingreso"])
        self._tabla.tag_configure("gasto", foreground=TEMA["gasto"])
        self._tabla.tag_configure("par", background=TEMA["tarjeta_alt"])
        barra = ttk.Scrollbar(tarjeta.cuerpo, orient="vertical", command=self._tabla.yview)
        self._tabla.configure(yscrollcommand=barra.set)
        barra.pack(side="right", fill="y")
        self._tabla.pack(fill="both", expand=True)

        self._vacio_historial = tk.Label(tarjeta.cuerpo, text="Aún no hay transacciones registradas.",
                                         bg=TEMA["tarjeta"], fg=TEMA["texto_suave"], font=fuente(11))
        return pagina

    def _aplicar_filtro(self, filtro: str) -> None:
        self._filtro.set(filtro)
        self._refrescar_historial()

    # ── Página: Análisis ──────────────────────────────────────────────
    def _crear_pagina_analisis(self) -> tk.Frame:
        pagina = tk.Frame(self._contenedor, bg=TEMA["fondo"])
        self._encabezado(pagina, "Análisis", "Distribución de tus ingresos y gastos por categoría")
        self._tarjeta_grafico = Tarjeta(pagina, padding=16)
        self._tarjeta_grafico.pack(fill="both", expand=True)
        self._canvas_grafico: FigureCanvasTkAgg | None = None
        return pagina

    def _dibujar_graficos(self) -> None:
        cuerpo = self._tarjeta_grafico.cuerpo
        for w in cuerpo.winfo_children():
            w.destroy()
        if self._canvas_grafico is not None:
            self._canvas_grafico.figure.clear()
            self._canvas_grafico = None

        gastos = self._service.gastos_por_categoria()
        ingresos = self._service.ingresos_por_categoria()
        conjuntos = [(d, t) for d, t in [(gastos, "Gastos"), (ingresos, "Ingresos")] if d]
        if not conjuntos:
            tk.Label(cuerpo, text="Registra transacciones para ver el análisis.",
                     bg=TEMA["tarjeta"], fg=TEMA["texto_suave"], font=fuente(11)).pack(expand=True)
            return

        fig = Figure(figsize=(6 * len(conjuntos), 5), dpi=100, facecolor=TEMA["tarjeta"])
        for i, (datos, titulo) in enumerate(conjuntos, start=1):
            ax = fig.add_subplot(1, len(conjuntos), i)
            ax.set_facecolor(TEMA["tarjeta"])
            colores = PALETA_GRAFICOS[: len(datos)] if len(datos) <= len(PALETA_GRAFICOS) \
                else (PALETA_GRAFICOS * (len(datos) // len(PALETA_GRAFICOS) + 1))[: len(datos)]
            cunas, _, autotextos = ax.pie(
                list(datos.values()), colors=colores, startangle=90, counterclock=False,
                autopct=lambda p: f"{p:.0f}%" if p >= 5 else "", pctdistance=0.8,
                wedgeprops={"width": 0.38, "edgecolor": TEMA["tarjeta"], "linewidth": 3},
            )
            for at in autotextos:
                at.set_color(TEMA["texto"])
                at.set_fontsize(9)
                at.set_fontweight("bold")
            total = sum(datos.values())
            ax.text(0, 0.08, monto_corto(total), ha="center", va="center", color=TEMA["texto"],
                    fontsize=14, fontweight="bold")
            ax.text(0, -0.14, f"Total {titulo.lower()}", ha="center", va="center",
                    color=TEMA["texto_suave"], fontsize=9)
            ax.set_title(titulo, color=TEMA["texto"], fontsize=13, fontweight="bold", pad=12)
            leyenda = ax.legend(cunas, [c.capitalize() for c in datos], loc="upper center",
                                bbox_to_anchor=(0.5, -0.02), ncol=min(3, len(datos)),
                                frameon=False, fontsize=9)
            for texto in leyenda.get_texts():
                texto.set_color(TEMA["texto_suave"])
            ax.axis("equal")
        fig.tight_layout()

        self._canvas_grafico = FigureCanvasTkAgg(fig, master=cuerpo)
        self._canvas_grafico.draw()
        self._canvas_grafico.get_tk_widget().configure(bg=TEMA["tarjeta"], highlightthickness=0)
        self._canvas_grafico.get_tk_widget().pack(fill="both", expand=True)

    # ── Refresco de datos ─────────────────────────────────────────────
    def _refrescar(self) -> None:
        s = self._service
        historial = s.historial
        n_ing = sum(1 for t in historial if t.tipo == "Ingreso")
        n_gas = len(historial) - n_ing

        self._kpi["ingresos"][0].config(text=monto_corto(s.total_ingresos))
        self._kpi["ingresos"][1].config(text=f"{n_ing} movimiento(s)")
        self._kpi["gastos"][0].config(text=monto_corto(s.total_gastos))
        self._kpi["gastos"][1].config(text=f"{n_gas} movimiento(s)")

        estado = s.evaluar_estado()
        color = {"Superávit": TEMA["ingreso"], "Déficit": TEMA["gasto"]}.get(estado, TEMA["neutral"])
        signo = "−" if s.balance < 0 else ""
        self._kpi["balance"][0].config(text=signo + monto_corto(abs(s.balance)), fg=color)
        self._kpi["balance"][1].config(text=f"● {estado}", fg=color)

        categorias = sorted({t.categoria for t in historial})
        self._combo_categoria.configure(values=categorias)

        for w in self._lista_recientes.winfo_children():
            w.destroy()
        if not historial:
            tk.Label(self._lista_recientes, text="Aún no hay movimientos.\nRegistra el primero ←",
                     bg=TEMA["tarjeta"], fg=TEMA["texto_suave"], font=fuente(10)).pack(expand=True)
        else:
            for t in sorted(historial, key=lambda x: x.fecha, reverse=True)[:6]:
                self._fila_movimiento(self._lista_recientes, t)

        self._refrescar_historial()
        if self._pagina_actual == "analisis":
            self._dibujar_graficos()

    def _refrescar_historial(self) -> None:
        filtro = self._filtro.get()
        for nombre, b in self._botones_filtro.items():
            if nombre == filtro:
                b.set_colores(TEMA["acento"], TEMA["acento"], TEMA["texto"])
            else:
                b.set_colores(TEMA["tarjeta"], TEMA["tarjeta_alt"], TEMA["texto_suave"])

        self._tabla.delete(*self._tabla.get_children())
        movimientos = sorted(self._service.historial, key=lambda x: x.fecha, reverse=True)
        if filtro != "Todos":
            tipo = "Ingreso" if filtro == "Ingresos" else "Gasto"
            movimientos = [t for t in movimientos if t.tipo == tipo]

        if not movimientos:
            self._vacio_historial.place(relx=0.5, rely=0.5, anchor="center")
        else:
            self._vacio_historial.place_forget()
        for i, t in enumerate(movimientos):
            tag_tipo = "ingreso" if t.tipo == "Ingreso" else "gasto"
            tags = (tag_tipo, "par") if i % 2 else (tag_tipo,)
            signo = "+" if t.tipo == "Ingreso" else "−"
            self._tabla.insert("", tk.END, tags=tags, values=(
                "   " + t.fecha.strftime("%d/%m/%Y  %H:%M"),
                t.tipo, t.categoria.capitalize(), f"{signo} {monto_corto(t.monto)} COP   ",
            ))

    # ── Acciones ──────────────────────────────────────────────────────
    def _registrar(self) -> None:
        if self._pagina_actual != "panel":
            return
        tipo = self._tipo.get()
        categoria = self._combo_categoria.get().strip()
        monto = self._leer_monto(self._campo_monto.get())
        if monto is None:
            self._error.config(text="El monto debe ser un número. Ej: 150000")
            return
        try:
            self._service.registrar_transaccion(
                Transaccion(tipo=tipo, monto=monto, categoria=categoria))
        except ValueError as e:
            self._error.config(text=str(e))
            return
        except RuntimeError as e:
            self._toast.mostrar(str(e), "error")
            return

        self._error.config(text="")
        self._campo_monto.limpiar()
        self._combo_categoria.set("")
        self._root.focus_set()
        self._refrescar()
        self._toast.mostrar(f"{tipo} de {monto_corto(monto)} registrado correctamente")

    @staticmethod
    def _leer_monto(texto: str) -> float | None:
        """Acepta '150000', '150000.5' y también el formato colombiano '1.500.000,50'."""
        texto = texto.replace("$", "").replace(" ", "")
        for candidato in (texto, texto.replace(".", "").replace(",", ".")):
            try:
                return float(candidato)
            except ValueError:
                continue
        return None

    def _exportar_csv(self) -> None:
        if not self._service.historial:
            self._toast.mostrar("No hay transacciones para exportar.", "error")
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
            self._toast.mostrar(f"Historial exportado a\n{Path(ruta).name}")
        except RuntimeError as e:
            self._toast.mostrar(str(e), "error")
