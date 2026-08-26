"""
Box recommendation for an order.

Approach (kept intentionally simple for warehouse ops):
1. Total weight must fit under the box max weight.
2. Every product must fit inside the box in at least one orientation
   (we try all 6 dimension permutations — boxes don't care which way is "up").
3. Combined item volume must leave a little slack. Real packing is never
   100% dense, so we use a fill factor (default 0.85).
4. Among boxes that pass, pick the cheapest. If cost ties, pick the
   smallest volume so we don't ship air when prices match.

Not using full 3D bin packing — overkill for this catalog size and harder
to explain to the warehouse team.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from itertools import permutations
from typing import Iterable, Sequence

from packing.models import Box, Order, Product

# How tightly we assume items can pack into a carton.
DEFAULT_FILL_FACTOR = Decimal("0.85")


@dataclass(frozen=True)
class RecommendationResult:
    box: Box | None
    reason: str
    candidates_checked: int
    total_weight_kg: Decimal
    total_volume_cm3: Decimal


def _dims(obj) -> tuple[Decimal, Decimal, Decimal]:
    return (obj.length_cm, obj.width_cm, obj.height_cm)


def product_fits_in_box(product: Product, box: Box) -> bool:
    """True if the product fits in the box under any rotation."""
    box_sorted = tuple(sorted(_dims(box)))
    for orient in set(permutations(_dims(product))):
        item_sorted = tuple(sorted(orient))
        # After sorting both, each item edge must be <= matching box edge.
        if all(i <= b for i, b in zip(item_sorted, box_sorted)):
            return True
    return False


def order_line_stats(items: Iterable) -> tuple[Decimal, Decimal, list[tuple[Product, int]]]:
    """Return total weight, total volume, and (product, qty) pairs."""
    total_weight = Decimal("0")
    total_volume = Decimal("0")
    lines: list[tuple[Product, int]] = []
    for item in items:
        product = item.product if hasattr(item, "product") else item[0]
        qty = item.quantity if hasattr(item, "quantity") else item[1]
        if qty < 1:
            continue
        lines.append((product, qty))
        total_weight += product.weight_kg * qty
        total_volume += product.volume_cm3 * qty
    return total_weight, total_volume, lines


def box_can_hold(
    box: Box,
    lines: Sequence[tuple[Product, int]],
    total_weight: Decimal,
    total_volume: Decimal,
    fill_factor: Decimal = DEFAULT_FILL_FACTOR,
) -> tuple[bool, str]:
    if total_weight > box.max_weight_kg:
        return False, f"weight {total_weight}kg exceeds max {box.max_weight_kg}kg"

    usable_volume = box.volume_cm3 * fill_factor
    if total_volume > usable_volume:
        return (
            False,
            f"volume {total_volume}cm³ exceeds usable {usable_volume}cm³ "
            f"(fill factor {fill_factor})",
        )

    for product, _qty in lines:
        if not product_fits_in_box(product, box):
            return False, f"product {product.sku} does not fit in box {box.code}"

    return True, "ok"


def recommend_box_for_lines(
    lines: Sequence[tuple[Product, int]],
    boxes: Sequence[Box] | None = None,
    fill_factor: Decimal = DEFAULT_FILL_FACTOR,
) -> RecommendationResult:
    total_weight, total_volume, cleaned = order_line_stats(lines)

    if not cleaned:
        return RecommendationResult(
            box=None,
            reason="Order has no items.",
            candidates_checked=0,
            total_weight_kg=total_weight,
            total_volume_cm3=total_volume,
        )

    if boxes is None:
        box_qs = Box.objects.filter(is_active=True).order_by("cost", "length_cm", "width_cm", "height_cm")
        boxes = list(box_qs)

    suitable: list[Box] = []
    for box in boxes:
        ok, _why = box_can_hold(box, cleaned, total_weight, total_volume, fill_factor)
        if ok:
            suitable.append(box)

    if not suitable:
        return RecommendationResult(
            box=None,
            reason="No active box can hold this order (weight, volume, or item size).",
            candidates_checked=len(boxes),
            total_weight_kg=total_weight,
            total_volume_cm3=total_volume,
        )

    # Cheapest first; then smallest volume.
    suitable.sort(key=lambda b: (b.cost, b.volume_cm3, b.code))
    chosen = suitable[0]
    return RecommendationResult(
        box=chosen,
        reason=(
            f"Selected {chosen.code}: cheapest feasible box "
            f"(cost={chosen.cost}, volume={chosen.volume_cm3}cm³)."
        ),
        candidates_checked=len(boxes),
        total_weight_kg=total_weight,
        total_volume_cm3=total_volume,
    )


def recommend_box_for_order(
    order: Order,
    *,
    persist: bool = True,
    fill_factor: Decimal = DEFAULT_FILL_FACTOR,
) -> RecommendationResult:
    items = order.items.select_related("product").all()
    lines = [(item.product, item.quantity) for item in items]
    result = recommend_box_for_lines(lines, fill_factor=fill_factor)
    if persist:
        order.recommended_box = result.box
        order.save(update_fields=["recommended_box"])
    return result
