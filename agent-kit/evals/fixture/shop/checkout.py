"""Total do pedido: subtotal, cupom e frete."""

from shop.pricing import apply_coupon, subtotal
from shop.shipping import shipping_cost


def checkout_total(items, region, coupon=None):
    discounted = apply_coupon(subtotal(items), coupon)
    return round(discounted + shipping_cost(discounted, region), 2)
