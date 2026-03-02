import json
import logging

from django.http import JsonResponse
from django.db import connection, transaction
from django.db.utils import OperationalError
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from rest_framework import serializers

from shop.models import Order, OrderItem, Product


logger = logging.getLogger("app")


# --------------------------------------------------
# 1) Slow endpoint (intentionally shows N+1)
# --------------------------------------------------
def orders_slow(request):
    # This is intentionally unoptimized for demo purposes.
    # Each "o.items.count()" triggers an extra query per order (N+1).
    orders = Order.objects.all()
    data = []

    for o in orders:
        items_count = o.items.count()
        data.append({
            "id": o.id,
            "user_id": o.user_id,
            "items_count": items_count,
        })

    # Prints how many DB queries were executed for this request.
    print("Total queries (slow):", len(connection.queries))
    return JsonResponse(data, safe=False)


# --------------------------------------------------
# 2) Fast endpoint (rate limit + pagination + cache)
# --------------------------------------------------
def orders_fast(request):
    # Basic IP-based rate limit (good for a demo, not production-grade).
    ip = request.META.get("REMOTE_ADDR", "unknown")
    window = 60
    limit_req = 30

    rate_key = f"rl:{ip}:orders_fast"
    current = cache.get(rate_key, 0)

    if current >= limit_req:
        return JsonResponse({"error": "RATE_LIMITED"}, status=429)

    if current == 0:
        cache.set(rate_key, 1, timeout=window)
    else:
        cache.incr(rate_key)

    # Simple page/limit pagination.
    page = int(request.GET.get("page", 1))
    limit = int(request.GET.get("limit", 50))

    if page < 1:
        page = 1
    if limit < 1:
        limit = 50
    if limit > 200:
        limit = 200

    offset = (page - 1) * limit

    # Cache per (page, limit) so repeated requests are fast.
    cache_key = f"orders_page_{page}_{limit}"
    cached = cache.get(cache_key)

    if cached:
        print("FROM CACHE")
        return JsonResponse(cached)

    # Optimized query:
    # - select_related("user") avoids an extra query when accessing user
    # - prefetch_related("items") reduces per-order item queries
    orders = (
        Order.objects
        .select_related("user")
        .prefetch_related("items")
        .order_by("-created_at")
    )[offset: offset + limit]

    results = []
    for o in orders:
        # Because of prefetch_related("items"), this doesn't do extra queries.
        results.append({
            "id": o.id,
            "user_id": o.user_id,
            "items_count": len(o.items.all()),
        })

    response_data = {
        "page": page,
        "limit": limit,
        "count": len(results),
        "results": results,
    }

    cache.set(cache_key, response_data, timeout=30)
    return JsonResponse(response_data)


# --------------------------------------------------
# 3) Buy endpoint (transaction + row lock + cache invalidation)
# --------------------------------------------------
@csrf_exempt
@login_required
def buy_product(request):
    # This endpoint expects POST JSON: {"product_id": ...}
    if request.method != "POST":
        return JsonResponse(
            {"error": "Method not allowed", "request_id": getattr(request, "request_id", None)},
            status=405
        )

    body = json.loads(request.body or "{}")
    product_id = body.get("product_id")

    if not product_id:
        return JsonResponse(
            {"error": "product_id required", "request_id": getattr(request, "request_id", None)},
            status=400
        )

    # Uses session-authenticated user (not JWT).
    user = request.user

    try:
        # Atomic block ensures order creation + stock update happen together.
        with transaction.atomic():
            # Row-level lock prevents race conditions on stock.
            product = Product.objects.select_for_update().get(id=product_id)

            if product.stock <= 0:
                return JsonResponse(
                    {"error": "OUT_OF_STOCK", "request_id": getattr(request, "request_id", None)},
                    status=409
                )

            product.stock -= 1
            product.save()

            order = Order.objects.create(user=user, total_price=product.price)
            OrderItem.objects.create(order=order, product=product, quantity=1)

            # Invalidate one known cached page (demo choice).
            cache.delete("orders_page_1_50")

            return JsonResponse(
                {"order_id": order.id, "remaining_stock": product.stock, "request_id": getattr(request, "request_id", None)},
                status=201
            )

    except Product.DoesNotExist:
        return JsonResponse(
            {"error": "PRODUCT_NOT_FOUND", "request_id": getattr(request, "request_id", None)},
            status=404
        )

    except OperationalError:
        # OperationalError can happen under heavy contention / lock timeouts.
        logger.exception(
            "db_locked request_id=%s product_id=%s user=%s",
            getattr(request, "request_id", "n/a"),
            product_id,
            getattr(user, "id", None),
        )
        return JsonResponse(
            {"error": "DB_LOCKED_TRY_AGAIN", "request_id": getattr(request, "request_id", None)},
            status=503
        )


# --------------------------------------------------
# DRF serializers (used by the DRF endpoints / ViewSets)
# --------------------------------------------------
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "price", "stock"]


class OrderItemSerializer(serializers.ModelSerializer):
    # Nested product info for nicer API responses.
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity"]


class OrderSerializer(serializers.ModelSerializer):
    # Nested items so the order response is self-contained.
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "total_price", "created_at", "items"]


# --------------------------------------------------
# Demo dashboard page (HTML file)
# --------------------------------------------------
@login_required
def demo_dashboard(request):
    # NOTE: This is an absolute path. It works locally but is not portable.
    # In production you'd normally use "shop/demo.html" and rely on template loaders.
    return render(request, "shop/demo.html")