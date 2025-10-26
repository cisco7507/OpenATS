import multiprocessing
import sys
import uvicorn

def run_api():
    """Target function to run the Uvicorn server."""
    from ats_oss.api.server import app
    print("API process started.")
    uvicorn.run(app, host="127.0.0.1", port=8650)

def run_gui():
    """Target function to run the PyQt6 GUI."""
    from ats_oss.gui.app import run_gui as run_gui_app
    print("GUI process started.")
    run_gui_app()

if __name__ == "__main__":
    # Set start method for multiprocessing to ensure compatibility, especially on macOS
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
