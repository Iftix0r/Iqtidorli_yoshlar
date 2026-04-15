import sys
import os

# Virtual environment Python interpreter
INTERP = os.path.expanduser('~/virtualenv/yoshiqtidorlar/3.11/bin/python3')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Loyiha root papkasini path ga qo'shish
sys.path.insert(0, os.path.dirname(__file__))

# Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'iqtidorli_yoshlar.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
