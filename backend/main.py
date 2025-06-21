from flask import Flask
from flask_cors import CORS
from compare_invbal import register_routes
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow all origins for now; you can restrict this later

# Register route(s) from other modules
register_routes(app)
logger.info("✅ Routes registered from compare_invbal.py")

@app.route('/')
def health_check():
    return {'status': 'Python backend is running!'}

if __name__ == '__main__':
    # Run on Railway’s exposed port
    app.run(host='0.0.0.0', port=8000)
