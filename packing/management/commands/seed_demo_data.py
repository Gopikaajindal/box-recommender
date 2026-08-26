from django.core.management.base import BaseCommand
from decimal import Decimal

from packing.models import Box, Product


class Command(BaseCommand):
    help = "Load a small demo catalog of products and boxes."

    def handle(self, *args, **options):
        products = [
            ("MUG-01", "Ceramic Mug", "10", "8", "10", "0.350"),
            ("BOOK-01", "Paperback Book", "20", "13", "3", "0.400"),
            ("TSHIRT-01", "T-Shirt (folded)", "25", "20", "3", "0.200"),
            ("LAMP-01", "Desk Lamp", "35", "20", "20", "1.800"),
            ("CHAIR-01", "Folding Chair", "80", "45", "15", "6.500"),
        ]
        for sku, name, l, w, h, wt in products:
            Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "length_cm": Decimal(l),
                    "width_cm": Decimal(w),
                    "height_cm": Decimal(h),
                    "weight_kg": Decimal(wt),
                },
            )

        boxes = [
            ("S", "Small mailer", "30", "20", "10", "2.000", "2.50"),
            ("M", "Medium carton", "40", "30", "25", "10.000", "4.00"),
            ("L", "Large carton", "60", "40", "40", "20.000", "7.50"),
            ("XL", "XL carton", "100", "60", "50", "30.000", "12.00"),
        ]
        for code, name, l, w, h, mw, cost in boxes:
            Box.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "length_cm": Decimal(l),
                    "width_cm": Decimal(w),
                    "height_cm": Decimal(h),
                    "max_weight_kg": Decimal(mw),
                    "cost": Decimal(cost),
                    "is_active": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("Demo products and boxes loaded."))
