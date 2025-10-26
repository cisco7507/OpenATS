import uvicorn
from ats_oss.api.server import app
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="127.0.0.1", port=8650)
    except Exception as e:
        logging.error("Failed to start server", exc_info=True)
        print(f"Failed to start server: {e}")
