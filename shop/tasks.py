import csv
import io
from celery import shared_task
from .models import Order


# Celery task that exports a user's orders to CSV format
# Returns CSV content as a string (simple MVP approach)
@shared_task
def export_orders_csv(user_id: int) -> str:

    # Use in-memory string buffer instead of writing to file
    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV header row
    writer.writerow(["id", "total_price", "created_at"])

    # Fetch latest 5000 orders for the given user
    # Limit prevents excessive memory usage
    qs = Order.objects.filter(user_id=user_id).order_by("-created_at")[:5000]

    # Write each order as a CSV row
    for o in qs:
        writer.writerow([
            o.id,
            str(o.total_price),
            o.created_at.isoformat()
        ])

    # Return CSV content as string
    return output.getvalue()