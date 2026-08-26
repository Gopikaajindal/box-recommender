from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse

from packing.models import Box, Order, OrderItem, Product
from packing.services.recommender import (
    product_fits_in_box,
    recommend_box_for_lines,
    recommend_box_for_order,
)


class RecommenderHelpersTest(TestCase):
    def setUp(self):
        self.small_box = Box.objects.create(
            code="S",
            name="Small",
            length_cm=Decimal("30"),
            width_cm=Decimal("20"),
            height_cm=Decimal("10"),
            max_weight_kg=Decimal("2"),
            cost=Decimal("2.50"),
        )
        self.medium_box = Box.objects.create(
            code="M",
            name="Medium",
            length_cm=Decimal("40"),
            width_cm=Decimal("30"),
            height_cm=Decimal("25"),
            max_weight_kg=Decimal("10"),
            cost=Decimal("4.00"),
        )
        self.large_box = Box.objects.create(
            code="L",
            name="Large",
            length_cm=Decimal("60"),
            width_cm=Decimal("40"),
            height_cm=Decimal("40"),
            max_weight_kg=Decimal("20"),
            cost=Decimal("7.50"),
        )
        self.mug = Product.objects.create(
            sku="MUG-01",
            name="Mug",
            length_cm=Decimal("10"),
            width_cm=Decimal("8"),
            height_cm=Decimal("10"),
            weight_kg=Decimal("0.350"),
        )
        self.lamp = Product.objects.create(
            sku="LAMP-01",
            name="Lamp",
            length_cm=Decimal("35"),
            width_cm=Decimal("20"),
            height_cm=Decimal("20"),
            weight_kg=Decimal("1.800"),
        )
        self.chair = Product.objects.create(
            sku="CHAIR-01",
            name="Chair",
            length_cm=Decimal("80"),
            width_cm=Decimal("45"),
            height_cm=Decimal("15"),
            weight_kg=Decimal("6.500"),
        )

    def test_product_fits_with_rotation(self):
        # 35x20x20 does not fit in 30x20x10 even rotated
        self.assertFalse(product_fits_in_box(self.lamp, self.small_box))
        # but fits in medium
        self.assertTrue(product_fits_in_box(self.lamp, self.medium_box))

    def test_cheapest_suitable_box_is_chosen(self):
        result = recommend_box_for_lines([(self.mug, 1)])
        self.assertIsNotNone(result.box)
        self.assertEqual(result.box.code, "S")

    def test_skips_box_when_item_too_large(self):
        result = recommend_box_for_lines([(self.lamp, 1)])
        self.assertEqual(result.box.code, "M")

    def test_weight_limit_blocks_small_box(self):
        # many mugs: volume might still fit small with fill factor, but weight won't
        # small max weight 2kg; 6 mugs = 2.1kg
        result = recommend_box_for_lines([(self.mug, 6)])
        self.assertIsNotNone(result.box)
        self.assertNotEqual(result.box.code, "S")

    def test_oversized_item_returns_no_box(self):
        result = recommend_box_for_lines([(self.chair, 1)])
        # chair 80cm longest edge — only XL would work; we didn't create XL here
        self.assertIsNone(result.box)
        self.assertIn("No active box", result.reason)

    def test_empty_order(self):
        result = recommend_box_for_lines([])
        self.assertIsNone(result.box)
        self.assertIn("no items", result.reason.lower())

    def test_cost_tie_prefers_smaller_volume(self):
        # same cost as medium, but smaller volume
        Box.objects.create(
            code="M2",
            name="Medium twin",
            length_cm=Decimal("35"),
            width_cm=Decimal("30"),
            height_cm=Decimal("25"),
            max_weight_kg=Decimal("10"),
            cost=Decimal("4.00"),
        )
        result = recommend_box_for_lines([(self.lamp, 1)])
        self.assertEqual(result.box.code, "M2")

    def test_inactive_box_ignored(self):
        self.small_box.is_active = False
        self.small_box.save()
        result = recommend_box_for_lines([(self.mug, 1)])
        self.assertEqual(result.box.code, "M")

    def test_persist_on_order(self):
        order = Order.objects.create(reference="ORD-1")
        OrderItem.objects.create(order=order, product=self.mug, quantity=1)
        result = recommend_box_for_order(order, persist=True)
        order.refresh_from_db()
        self.assertEqual(order.recommended_box_id, result.box.id)


class ApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.box = Box.objects.create(
            code="S",
            name="Small",
            length_cm=Decimal("30"),
            width_cm=Decimal("20"),
            height_cm=Decimal("10"),
            max_weight_kg=Decimal("2"),
            cost=Decimal("2.50"),
        )
        self.product = Product.objects.create(
            sku="MUG-01",
            name="Mug",
            length_cm=Decimal("10"),
            width_cm=Decimal("8"),
            height_cm=Decimal("10"),
            weight_kg=Decimal("0.350"),
        )

    def test_recommend_by_sku_payload(self):
        resp = self.client.post(
            reverse("recommend"),
            data='{"items": [{"sku": "MUG-01", "quantity": 1}]}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["box"]["code"], "S")

    def test_create_order_and_recommend(self):
        resp = self.client.post(
            reverse("create-order"),
            data='{"reference": "ORD-99", "items": [{"sku": "MUG-01", "quantity": 2}]}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertEqual(data["reference"], "ORD-99")
        self.assertEqual(data["box"]["code"], "S")

    def test_unknown_sku(self):
        resp = self.client.post(
            reverse("recommend"),
            data='{"items": [{"sku": "NOPE", "quantity": 1}]}',
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 404)

    def test_list_boxes(self):
        resp = self.client.get(reverse("list-boxes"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()["boxes"]), 1)
