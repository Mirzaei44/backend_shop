import os
from celery import Celery

# Tell Celery which Django settings module to use (so it can read Django config).
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Create the Celery app instance for this project.
app = Celery("core")

# Load Celery settings from Django settings.py (only keys starting with CELERY_).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py from installed Django apps.
app.autodiscover_tasks()