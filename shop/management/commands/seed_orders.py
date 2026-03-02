from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shop.models import Order, OrderItem, Product
import random

User = get_user_model()

class Command(BaseCommand):
    help = "Seed orders with fake data"

    def handle(self, *args, **kwargs):

        # Load all users and products into memory once.
        # This avoids hitting the database inside the loop.
        users = list(User.objects.all())
        products = list(Product.objects.all())

        # If there are no users or products, we cannot create orders.
        if not users or not products:
            self.stdout.write(self.style.ERROR("Users or Products missing!"))
            return

        # Create 5000 random orders for testing purposes.
        # Each order will belong to a random user.
        for i in range(5000):
            user = random.choice(users)

            # Create the order with total_price set to 0 for now.
            # (This script does not calculate totals.)
            order = Order.objects.create(
                user=user,
                total_price=0
            )

            # Add 3 random items to each order.
            # Products are selected randomly.
            for _ in range(3):
                product = random.choice(products)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=1
                )

        # Print a success message at the end.
        self.stdout.write(self.style.SUCCESS("Seeding done!"))