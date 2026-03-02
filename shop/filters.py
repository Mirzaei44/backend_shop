import django_filters
from .models import Order


# Filter class for Order list endpoint
# Allows clients to filter orders by total price range and creation date range
class OrderFilter(django_filters.FilterSet):

    # Minimum total price (greater than or equal)
    min_total = django_filters.NumberFilter(
        field_name="total_price",
        lookup_expr="gte"
    )

    # Maximum total price (less than or equal)
    max_total = django_filters.NumberFilter(
        field_name="total_price",
        lookup_expr="lte"
    )

    # Orders created after this datetime
    created_after = django_filters.IsoDateTimeFilter(
        field_name="created_at",
        lookup_expr="gte"
    )

    # Orders created before this datetime
    created_before = django_filters.IsoDateTimeFilter(
        field_name="created_at",
        lookup_expr="lte"
    )

    class Meta:
        # Connect filter to Order model
        model = Order

        # Expose these query parameters in the API
        fields = ["min_total", "max_total", "created_after", "created_before"]