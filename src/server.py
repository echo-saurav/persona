from src.app import create_app
from dotenv import load_dotenv
import os

load_dotenv()
PORT = os.getenv(key='PORT', default=3000)
configs_dir = os.getenv(key='CONFIGS_DIR', default="configs")
background_seconds = os.getenv(key='BACKGROUND_SECOND', default=200)

app = create_app(configs_dir)

if __name__ == "__main__":
    app.run(use_reloader=False, debug=True, host='0.0.0.0', port=PORT, threaded=True)
