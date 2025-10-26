from PIL import ImageGrab

def take_screenshot(filename="verification.png"):
    """Captures the entire screen and saves it to a file."""
    try:
        # Grab the entire screen
        screenshot = ImageGrab.grab()
        # Save the screenshot
        screenshot.save(filename, "PNG")
        print(f"Screenshot saved to {filename}")
    except Exception as e:
        print(f"Failed to take screenshot: {e}")

if __name__ == "__main__":
    take_screenshot()
