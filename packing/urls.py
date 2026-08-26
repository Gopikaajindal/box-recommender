from django.urls import path

from . import views

urlpatterns = [
    path("boxes/", views.list_boxes, name="list-boxes"),
    path("orders/", views.create_order, name="create-order"),
    path("recommend/", views.recommend_from_payload, name="recommend"),
    path("orders/<int:order_id>/recommend/", views.recommend_for_order, name="recommend-order"),
]
