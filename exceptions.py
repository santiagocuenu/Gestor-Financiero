class GestorFinanzasError(Exception):
    """Base para errores del dominio."""

class TransaccionInvalidaError(GestorFinanzasError):
    """Datos de transacción inválidos."""

class PersistenciaError(GestorFinanzasError):
    """Fallo en lectura o escritura de datos."""
