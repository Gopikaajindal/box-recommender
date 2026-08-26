from django.contrib import admin

from .models import Box, Order, OrderItem, Product


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "length_cm", "width_cm", "height_cm", "weight_kg")
    search_fields = ("sku", "name")


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "length_cm",
        "width_cm",
        "height_cm",
        "max_weight_kg",
        "cost",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("code", "name")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "created_at", "recommended_box")
    search_fields = ("reference",)
    inlines = [OrderItemInline]
    readonly_fields = ("recommended_box",)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity")
