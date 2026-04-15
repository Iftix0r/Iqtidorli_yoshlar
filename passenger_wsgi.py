import sys
import os

sys.path.insert(0, '/home/host7905/yoshiqtidorlar')

os.environ['DJANGO_SETTINGS_MODULE'] = 'iqtidorli_yoshlar.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
