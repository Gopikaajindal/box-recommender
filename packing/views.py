import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from packing.models import Box, Order, OrderItem, Product
from packing.services.recommender import recommend_box_for_order, recommend_box_for_lines


def _box_payload(box: Box | None):
    if box is None:
        return None
    return {
        "id": box.id,
        "code": box.code,
        "name": box.name,
        "length_cm": str(box.length_cm),
        "width_cm": str(box.width_cm),
        "height_cm": str(box.height_cm),
        "max_weight_kg": str(box.max_weight_kg),
        "cost": str(box.cost),
    }


def _result_payload(result):
    return {
        "box": _box_payload(result.box),
        "reason": result.reason,
        "candidates_checked": result.candidates_checked,
        "total_weight_kg": str(result.total_weight_kg),
        "total_volume_cm3": str(result.total_volume_cm3),
    }


@require_http_methods(["GET"])
def recommend_for_order(request, order_id: int):
    order = get_object_or_404(Order.objects.prefetch_related("items__product"), pk=order_id)
    result = recommend_box_for_order(order, persist=True)
    status = 200 if result.box else 422
    return JsonResponse(_result_payload(result), status=status)


@csrf_exempt
@require_http_methods(["POST"])
def recommend_from_payload(request):
    """
    Body JSON either:
      {"order_id": 1}
    or
      {"items": [{"sku": "SKU1", "quantity": 2}, ...]}
    """
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    if "order_id" in body:
        order = get_object_or_404(Order, pk=body["order_id"])
        result = recommend_box_for_order(order, persist=True)
        status = 200 if result.box else 422
        return JsonResponse(_result_payload(result), status=status)

    items = body.get("items")
    if not isinstance(items, list) or not items:
        return JsonResponse(
            {"error": "Provide order_id or a non-empty items list."},
            status=400,
        )

    lines = []
    for row in items:
        sku = row.get("sku")
        qty = row.get("quantity", 1)
        try:
            qty = int(qty)
        except (TypeError, ValueError):
            return JsonResponse({"error": f"Bad quantity for sku={sku}."}, status=400)
        if not sku or qty < 1:
            return JsonResponse({"error": "Each item needs sku and quantity >= 1."}, status=400)
        try:
            product = Product.objects.get(sku=sku)
        except Product.DoesNotExist:
            return JsonResponse({"error": f"Unknown sku: {sku}"}, status=404)
        lines.append((product, qty))

    result = recommend_box_for_lines(lines)
    status = 200 if result.box else 422
    return JsonResponse(_result_payload(result), status=status)


@csrf_exempt
@require_http_methods(["POST"])
@transaction.atomic
def create_order(request):
    """
    Create an order + items, then recommend a box.
    {"reference": "ORD-100", "items": [{"sku": "...", "quantity": 1}]}
    """
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    reference = (body.get("reference") or "").strip()
    items = body.get("items")
    if not reference or not isinstance(items, list) or not items:
        return JsonResponse(
            {"error": "reference and non-empty items are required."},
            status=400,
        )

    if Order.objects.filter(reference=reference).exists():
        return JsonResponse({"error": "reference already exists."}, status=409)

    order = Order.objects.create(reference=reference)
    for row in items:
        sku = row.get("sku")
        qty = int(row.get("quantity", 1))
        product = get_object_or_404(Product, sku=sku)
        OrderItem.objects.create(order=order, product=product, quantity=qty)

    result = recommend_box_for_order(order, persist=True)
    payload = _result_payload(result)
    payload["order_id"] = order.id
    payload["reference"] = order.reference
    status = 201 if result.box else 422
    return JsonResponse(payload, status=status)


@require_http_methods(["GET"])
def list_boxes(request):
    boxes = Box.objects.filter(is_active=True)
    return JsonResponse({"boxes": [_box_payload(b) for b in boxes]})
