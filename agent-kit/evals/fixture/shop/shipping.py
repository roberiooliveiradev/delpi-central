"""Frete por região."""

RATES = {"SE": 20.0, "S": 25.0, "NE": 35.0, "N": 45.0, "CO": 30.0}
FREE_SHIPPING_FROM = 200.0


def shipping_cost(total, region):
    """Frete grátis a partir de R$ 200; abaixo disso, tabela por região."""
    if region not in RATES:
        raise ValueError(f"região desconhecida: {region}")
    if total >= FREE_SHIPPING_FROM:
        return 0.0
    return RATES[region]
