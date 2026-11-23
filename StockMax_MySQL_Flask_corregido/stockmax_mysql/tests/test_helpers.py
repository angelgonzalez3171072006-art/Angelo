from decimal import Decimal
import sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Pruebas pequeñas de validación monetaria sin necesitar una instancia de MySQL.
# Ejecutar desde la carpeta del proyecto: pytest -q
from stockmax_utils import money

@pytest.mark.parametrize(('value','expected'), [('0', Decimal('0.00')), ('12', Decimal('12.00')), ('12.345', Decimal('12.34'))])
def test_money_valid(value, expected):
    assert money(value) == expected

@pytest.mark.parametrize('value', ['-1', 'abc', None, 'NaN', 'Infinity'])
def test_money_rejects_invalid(value):
    with pytest.raises(ValueError):
        money(value)
