"""Celery worker entry point."""

from .tasks.processing import celery_app

if __name__ == '__main__':
    celery_app.start()