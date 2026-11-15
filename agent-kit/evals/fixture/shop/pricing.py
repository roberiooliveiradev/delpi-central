"""Preço dos itens e cupons de desconto."""

COUPONS = {"DESC10": 0.10}


def subtotal(items):
    """Soma preço x quantidade de cada item."""
    return round(sum(item["price"] * item["qty"] for item in items), 2)


def apply_coupon(total, coupon):
    """Aplica um cupom de desconto. Cupom desconhecido é erro."""
    if coupon is None:
        return total
    if coupon not in COUPONS:
        raise ValueError(f"cupom inválido: {coupon}")
    return round(total * (1 - COUPONS[coupon]), 2)
