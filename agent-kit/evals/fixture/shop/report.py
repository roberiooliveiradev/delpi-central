"""Relatório diário de vendas (consumidor de pricing.apply_coupon)."""

from shop.pricing import apply_coupon


def projected_revenue(orders):
    """Receita projetada aplicando o cupom de cada pedido."""
    return round(sum(apply_coupon(o["total"], o.get("coupon")) for o in orders), 2)
