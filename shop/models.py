# core/models.py
from django.db import models
from django.conf import settings


# Product model
# Represents items that users can purchase
class Product(models.Model):
    # Product name
    name = models.CharField(max_length=255)

    # Product price (up to 10 digits, 2 decimal places)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Available stock quantity
    stock = models.IntegerField(default=0)

    # Timestamp when product was created
    created_at = models.DateTimeField(auto_now_add=True)


# Order model
# Represents a purchase made by a user
class Order(models.Model):
    # Link to the user who placed the order
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders"
    )

    # Cached total price of the order
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    # Creation timestamp (indexed for faster sorting/filtering)
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )


# OrderItem model
# Represents individual products inside an order
class OrderItem(models.Model):
    # Parent order
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items"
    )

    # Purchased product
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    # Quantity of this product in the order
    quantity = models.IntegerField()