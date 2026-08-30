# Gestor Financiero Personal

Aplicación de escritorio para registrar y analizar transacciones financieras personales. Desarrollada en Python con arquitectura en capas, persistencia en JSON y visualización de datos con Matplotlib.

---

## Características

- Registro de ingresos y gastos con categoría y fecha automática
- Balance en tiempo real con clasificación de estado (Superávit / Déficit / Neutral)
- Historial persistente: los datos se conservan al cerrar la aplicación
- Gráficos de distribución por categoría (ingresos y gastos)
- Exportación del historial completo a CSV

---

## Requisitos

- Python 3.10 o superior
- matplotlib

```bash
pip install matplotlib
```

---

## Ejecución

```bash
python main.py
```

---

## Estructura del proyecto

```
## Estructura del proyecto


├── transaction.py       # Modelo de datos (dataclass inmutable)
├── repository.py        # Persistencia JSON
├── finance_service.py   # Lógica de negocio y métricas
├── app.py               # Interfaz gráfica (tkinter)
├── main.py              # Entry point
├── requirements.txt
└── .gitignore

```

---

## Arquitectura

**Domain** — Modelos de datos y validación. `Transaccion` es un `@dataclass(frozen=True)` que valida en `__post_init__`. Sin dependencias externas.

**Services** — `FinanceService` calcula métricas con actualización incremental O(1). `TransactionRepository` gestiona la lectura y escritura del JSON.

**UI** — `AppFinanzas` construye la interfaz y delega toda la lógica al servicio.

---

## Tecnologías

- `tkinter` — UI de escritorio (stdlib)
- `matplotlib` — Gráficos de distribución
- `json`, `csv`, `dataclasses`, `pathlib` — stdlib
