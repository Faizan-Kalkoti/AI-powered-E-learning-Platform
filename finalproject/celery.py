from __future__ import absolute_import, unicode_literals
import os

from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finalproject.settings')

# Initialize Celery
app = Celery('finalproject')

# Configure Celery to use Django settings and set timezone
app.conf.enable_utc = False
app.conf.update(timezone='Asia/Kolkata')


# Load configuration from Django settings with a 'CELERY' namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks from all registered Django app configs
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')