from celery import Celery

def make_celery():
    """
    Create and configure the Celery app.
    """
    celery = Celery(
        'server_func',
        backend='redis://redis:6379/0',
        broker='redis://redis:6379/0'
    )
    celery.autodiscover_tasks(['server_func', 'demo_server'])
    return celery

celery = make_celery()