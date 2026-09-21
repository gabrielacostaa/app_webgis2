import sys
import os

# Add app_webgis directory to sys.path so templates, static, and modules are found properly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app_webgis'))

# Change working directory to app_webgis so relative paths to static/uploads and database work seamlessly
os.chdir(os.path.join(os.path.dirname(__file__), 'app_webgis'))

from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
