from decimal import Decimal, InvalidOperation

def money(value):
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result < 0:
            raise InvalidOperation
        return result.quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError('El precio debe ser un número válido mayor o igual a cero.')
