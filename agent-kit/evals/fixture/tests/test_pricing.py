import unittest

from shop.pricing import apply_coupon, subtotal


class PricingTests(unittest.TestCase):
    def test_subtotal(self):
        self.assertEqual(subtotal([{"price": 10.0, "qty": 2}, {"price": 5.5, "qty": 1}]), 25.5)

    def test_coupon_desc10(self):
        self.assertEqual(apply_coupon(100.0, "DESC10"), 90.0)

    def test_no_coupon(self):
        self.assertEqual(apply_coupon(100.0, None), 100.0)

    def test_invalid_coupon(self):
        with self.assertRaises(ValueError):
            apply_coupon(100.0, "NAOEXISTE")


if __name__ == "__main__":
    unittest.main()
