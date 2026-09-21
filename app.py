import sys
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.join(ROOT_DIR, 'app_webgis')

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

os.chdir(APP_DIR)

import app_webgis.app as _webgis_module
app = _webgis_module.app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
