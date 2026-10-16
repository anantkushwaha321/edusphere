"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# Ensure database migrations are automatically verified and applied on startup
# This guarantees PostgreSQL tables exist regardless of whether Render uses Procfile, render.yaml, or dashboard command.
try:
    import logging
    from django.core.management import call_command
    logger = logging.getLogger('django')
    logger.info("Verifying and executing pending database migrations on startup...")
    call_command('migrate', interactive=False)
    logger.info("Startup database migration check completed successfully.")
except Exception as e:
    import logging
    logging.getLogger('django').error("Startup migration execution error: %s", e, exc_info=True)

