from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    """A sellable item with outer dimensions (cm) and weight (kg)."""

    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    length_cm = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    width_cm = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    height_cm = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    weight_kg = models.DecimalField(
        max_digits=8, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))]
    )

    class Meta:
        ordering = ["sku"]

    def __str__(self):
        return f"{self.sku} — {self.name}"

    @property
    def volume_cm3(self) -> Decimal:
        return self.length_cm * self.width_cm * self.height_cm


class Box(models.Model):
    """Shipping carton: inner size, weight limit, and cost."""

    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    length_cm = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    width_cm = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    height_cm = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    max_weight_kg = models.DecimalField(
        max_digits=8, decimal_places=3, validators=[MinValueValidator(Decimal("0.001"))]
    )
    cost = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["cost", "code"]
        verbose_name_plural = "boxes"

    def __str__(self):
        return f"{self.code} — {self.name}"

    @property
    def volume_cm3(self) -> Decimal:
        return self.length_cm * self.width_cm * self.height_cm


class Order(models.Model):
    reference = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Cached after recommendation so warehouse can see what was chosen.
    recommended_box = models.ForeignKey(
        Box,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = ("order", "product")

    def __str__(self):
        return f"{self.order.reference}: {self.product.sku} x{self.quantity}"
