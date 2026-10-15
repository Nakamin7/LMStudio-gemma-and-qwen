import pytest
from src.tools import calculate

def test_calculate_basic():
    assert calculate('123*456') == '56088'

def test_calculate_rejects_code():
    with pytest.raises((ValueError, SyntaxError)):
        calculate('__import__("os").system("whoami")')

def test_calculate_rejects_huge_power():
    with pytest.raises(ValueError):
        calculate('9999999**999')
