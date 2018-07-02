"""
WSGI config for zohoinvoice project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "zohoinvoice.settings")

DEV_ENV = os.environ.get("ENV")
if DEV_ENV == "HEROKU":
    os.system('echo "from django.contrib.auth.models import User; User.objects.create_superuser(\'admin\', \'admin@example.com\', \'pass\')" | python manage.py shell')

application = get_wsgi_application()
