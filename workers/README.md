"""Root workers package — run Celery from backend directory.

  cd backend
  celery -A app.workers.celery_app worker -l info
  celery -A app.workers.celery_app beat -l info
"""
