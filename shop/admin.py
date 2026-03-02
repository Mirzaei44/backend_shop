from django.contrib import admin
from .models import Product, Order, OrderItem


# ---------------------------
# Product admin configuration
# Controls how Product appears in Django admin panel
# ---------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Columns visible in the list view
    list_display = ("id", "name", "price", "stock")

    # Enable search by product name
    search_fields = ("name",)

    # Add sidebar filter by price
    list_filter = ("price",)

    # Show newest products first
    ordering = ("-id",)


# ---------------------------
# Inline items inside Order admin page
# Allows editing OrderItems directly within an Order
# ---------------------------
class OrderItemInline(admin.TabularInline):
    model = OrderItem

    # Do not show extra empty rows by default
    extra = 0


# ---------------------------
# Order admin configuration
# Controls how orders are displayed in admin
# ---------------------------
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Show basic order info in list view
    list_display = ("id", "user", "total_price", "created_at")

    # Filter orders by creation date
    list_filter = ("created_at",)

    # Allow searching orders by username
    search_fields = ("user__username",)

    # Show latest orders first
    ordering = ("-created_at",)

    # Show related order items inline
    inlines = [OrderItemInline]


# ---------------------------
# Optional separate admin view for OrderItem
# Useful if you want to inspect items independently
# ---------------------------
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity")