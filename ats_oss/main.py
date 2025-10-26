import uvicorn
import multiprocessing
import sys
from ats_oss.api.server import app
from ats_oss.gui.app import run_gui

def run_api():
    """Target function to run the Uvicorn server."""
    uvicorn.run(app, host="127.0.0.1", port=8650)

if __name__ == "__main__":
    # Set start method for multiprocessing to ensure compatibility, especially on macOS
    # A known issue on macOS requires 'fork' for PyQt6 in a multiprocess setup.
    if sys.platform == "darwin":
        multiprocessing.set_start_method("fork")

    print("Starting API server process...")
    api_process = multiprocessing.Process(target=run_api)
    api_process.start()

    print("Starting GUI application process...")
    gui_process = multiprocessing.Process(target=run_gui)
    gui_process.start()

    try:
        # Wait for the processes to complete.
        api_process.join()
        gui_process.join()
    except KeyboardInterrupt:
        print("Shutting down processes...")
        api_process.terminate()
        gui_process.terminate()
        api_process.join()
        gui_process.join()
        print("Shutdown complete.")
