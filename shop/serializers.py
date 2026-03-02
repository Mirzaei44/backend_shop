from rest_framework import serializers
from .models import Product, Order, OrderItem


# Serializer for Product model
# Used inside OrderItemSerializer to show product details
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "price", "stock"]


# Serializer for individual items inside an order
# Includes nested product information (read-only)
class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity"]


# Serializer for Order model
# Returns order info along with related items
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "total_price", "created_at", "items"]
        

from rest_framework import serializers
from django.db import transaction
from .models import Product, Order, OrderItem


# Serializer used for purchasing a product
# Handles validation and transactional order creation
class BuySerializer(serializers.Serializer):
    product_id = serializers.IntegerField()

    # Validate that product exists before proceeding
    def validate_product_id(self, value):
        if not Product.objects.filter(id=value).exists():
            raise serializers.ValidationError("PRODUCT_NOT_FOUND")
        return value

    # Perform purchase logic inside a DB transaction
    def save(self, **kwargs):
        request = self.context["request"]
        user = request.user
        product_id = self.validated_data["product_id"]

        # Atomic transaction ensures stock consistency
        # select_for_update() locks the row to prevent race conditions
        with transaction.atomic():
            product = Product.objects.select_for_update().get(id=product_id)

            # Prevent purchase if stock is empty
            if product.stock <= 0:
                raise serializers.ValidationError("OUT_OF_STOCK")

            # Decrease stock
            product.stock -= 1
            product.save()

            # Create order and related item
            order = Order.objects.create(user=user, total_price=product.price)
            OrderItem.objects.create(order=order, product=product, quantity=1)

        # Return lightweight response payload
        return {"order_id": order.id, "remaining_stock": product.stock}