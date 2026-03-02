from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from shop.models import Product


class BuyTestCase(TestCase):

    def setUp(self):
        # Create a user for authenticated requests
        self.user = User.objects.create_user(username="test", password="1234")

        # Create a product with initial stock
        self.product = Product.objects.create(
            name="Test Product",
            price=100,
            stock=5
        )

        # DRF test client + force authentication for this user
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_buy_success(self):
        # Buy one unit of the product
        response = self.client.post("/api/buy/", {"product_id": self.product.id})

        # Expect successful creation
        self.assertEqual(response.status_code, 201)

        # Stock should decrement by 1
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 4)

    def test_buy_out_of_stock(self):
        # Set stock to 0 to simulate out-of-stock scenario
        self.product.stock = 0
        self.product.save()

        # Try buying the product
        response = self.client.post("/api/buy/", {"product_id": self.product.id})

        # Expect conflict response for OUT_OF_STOCK
        self.assertEqual(response.status_code, 409)


from shop.models import Order


class OrdersPermissionTestCase(TestCase):
    def setUp(self):
        # Create two different users
        self.u1 = User.objects.create_user(username="u1", password="1234")
        self.u2 = User.objects.create_user(username="u2", password="1234")

        # برای هر کدوم یک سفارش
        Order.objects.create(user=self.u1, total_price=100)
        Order.objects.create(user=self.u2, total_price=200)

        # DRF test client (no auth by default)
        self.client = APIClient()

    def test_user_sees_only_own_orders(self):
        # Authenticate as u1
        self.client.force_authenticate(user=self.u1)

        # Request orders list
        res = self.client.get("/api/orders/")

        # Must be allowed and return results
        self.assertEqual(res.status_code, 200)
        ids = [o["id"] for o in res.data["results"]]

        # باید سفارش user1 داخلش باشه
        self.assertTrue(any(ids))

        # Ensure we do not see u2's order (simple check via total_price value)
        for order in res.data["results"]:
            self.assertNotEqual(order["total_price"], "200.00")