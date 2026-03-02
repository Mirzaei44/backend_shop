from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderSerializer
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .filters import OrderFilter


# Read-only viewset for listing and retrieving user orders
# Only authenticated users can access this endpoint
class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    # Enable filtering and ordering support
    filter_backends = [DjangoFilterBackend, OrderingFilter]

    # Allow ordering by these fields
    ordering_fields = ["created_at", "total_price", "id"]

    # Default ordering: newest first
    ordering = ["-created_at"]

    # Connect custom filter class
    filterset_class = OrderFilter

    def get_queryset(self):
        # Return only orders belonging to the current user
        # select_related + prefetch_related reduce DB queries
        return (
            Order.objects
            .filter(user=self.request.user)
            .select_related("user")
            .prefetch_related("items__product")
        )
        

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import BuySerializer
from django.core.cache import cache
from rest_framework.exceptions import ValidationError


# Buy endpoint
# Creates an order for a product (if stock is available)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def buy_api(request):
    serializer = BuySerializer(data=request.data, context={"request": request})

    try:
        # Validate request data
        serializer.is_valid(raise_exception=True)

        # Perform the purchase logic (handled inside serializer)
        result = serializer.save()

        # Clear cached first page of orders after successful purchase
        cache.delete("orders_page_1_50")

        return Response(result, status=status.HTTP_201_CREATED)

    except ValidationError as e:
        # Special handling for out-of-stock case
        if "OUT_OF_STOCK" in str(e.detail):
            return Response(
                {"error": "OUT_OF_STOCK"},
                status=status.HTTP_409_CONFLICT
            )

        # Generic validation error
        return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .tasks import export_orders_csv


# Starts a background task to export user's orders as CSV
# Returns a task_id so client can poll status later
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def export_orders(request):
    task = export_orders_csv.delay(request.user.id)
    return Response({"task_id": task.id})


from celery.result import AsyncResult
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


# Checks status of a Celery export task
# Client must pass task_id as query parameter
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_orders_status(request):
    task_id = request.query_params.get("task_id")

    # task_id is required
    if not task_id:
        return Response({"error": "task_id required"}, status=400)

    result = AsyncResult(task_id)

    # Basic task information
    data = {
        "task_id": task_id,
        "status": result.status,   # PENDING / STARTED / SUCCESS / FAILURE
        "ready": result.ready(),
    }

    # If task finished successfully, include result payload
    if result.successful():
        data["result"] = result.result

    # If task failed, include error message
    if result.failed():
        data["error"] = str(result.result)

    return Response(data)