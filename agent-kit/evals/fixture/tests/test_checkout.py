import unittest

from shop.checkout import checkout_total


class CheckoutTests(unittest.TestCase):
    def test_with_shipping(self):
        self.assertEqual(checkout_total([{"price": 50.0, "qty": 2}], "SE"), 120.0)

    def test_free_shipping_threshold(self):
        self.assertEqual(checkout_total([{"price": 100.0, "qty": 2}], "N"), 200.0)

    def test_coupon_before_shipping(self):
        self.assertEqual(checkout_total([{"price": 100.0, "qty": 2}], "S", "DESC10"), 205.0)


if __name__ == "__main__":
    unittest.main()
