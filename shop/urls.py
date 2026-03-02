from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .api import buy_api
from .views import orders_slow, orders_fast, buy_product
from .api import OrderViewSet
from .api import export_orders, export_orders_status
from .views import demo_dashboard


# DRF router for ViewSets
# Automatically generates list/retrieve routes for orders
router = DefaultRouter()
router.register("api/orders", OrderViewSet, basename="orders")


urlpatterns = [

    # -------------------------
    # Celery export endpoints
    # -------------------------

    # Check export task status
    path("api/reports/orders/export/status/", export_orders_status),

    # Start export task
    path("api/reports/orders/export/", export_orders),


    # -------------------------
    # Legacy / experimental endpoints
    # -------------------------

    path("orders/slow/", orders_slow),
    path("orders/fast/", orders_fast),
    path("orders/buy/", buy_product),

    # New buy endpoint (DRF-based)
    path("api/buy/", buy_api),


    # -------------------------
    # JWT authentication endpoints
    # -------------------------

    # Obtain access + refresh token
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),

    # Refresh access token
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),


    # -------------------------
    # DRF router-generated routes
    # -------------------------

    path("", include(router.urls)),


    # -------------------------
    # Demo dashboard UI
    # -------------------------

    path("dashboard/demo/", demo_dashboard),
]