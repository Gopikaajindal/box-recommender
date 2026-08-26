from django.core.management.base import BaseCommand, CommandError

from packing.models import Order
from packing.services.recommender import recommend_box_for_order


class Command(BaseCommand):
    help = "Recommend (and save) the best shipping box for an order reference."

    def add_arguments(self, parser):
        parser.add_argument("reference", type=str, help="Order reference, e.g. ORD-1001")

    def handle(self, *args, **options):
        reference = options["reference"]
        try:
            order = Order.objects.get(reference=reference)
        except Order.DoesNotExist as exc:
            raise CommandError(f"No order with reference={reference}") from exc

        result = recommend_box_for_order(order, persist=True)
        if result.box is None:
            self.stderr.write(self.style.ERROR(result.reason))
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"{reference} -> {result.box.code} "
                f"(cost={result.box.cost}, weight={result.total_weight_kg}kg)"
            )
        )
        self.stdout.write(result.reason)
