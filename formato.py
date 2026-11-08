def formatear_monto(monto, moneda="COP"):
    """Devuelve el monto como texto con separador de miles y dos decimales."""
    return f"${monto:,.2f} {moneda}"