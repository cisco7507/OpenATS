#!/usr/bin/env python3
import argparse
import os
import requests
import json
from pathlib import Path

# --- Configuration ---
# A list of common audio file extensions to look for.
# Add or remove extensions as needed.
SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".flac", ".aiff", ".aif"}

def submit_file(api_url: str, workflow: str, file_path: Path):
    """
    Submits a single audio file to the ATS-OSS API.

    Args:
        api_url (str): The base URL of the API server.
        workflow (str): The name of the workflow template to use.
        file_path (Path): The absolute path to the audio file.
    """
    submit_url = f"{api_url}/workflows/submitWorkflow"

    payload = {
        "template_name": workflow,
        "input_uri": str(file_path.resolve()),  # Use the absolute path
        "params": {}
    }

    headers = {"Content-Type": "application/json"}

    print(f"Submitting '{file_path.name}' with workflow '{workflow}'...")

    try:
        response = requests.post(submit_url, json=payload, headers=headers)

        if response.status_code == 200:
            workflow_id = response.json().get("id")
            print(f"  \u2713 Success! Workflow ID: {workflow_id}")
        else:
            print(f"  \u2717 Error! Status Code: {response.status_code}")
            print(f"     Response: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"  \u2717 Connection Error! Could not connect to the server at {api_url}.")
        print(f"     Details: {e}")

def main():
    """
    Main function to parse arguments and process the directory.
    """
    parser = argparse.ArgumentParser(
        description="Bulk submit audio files to the ATS-OSS API.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "-d", "--directory",
        required=True,
        help="Path to the directory containing audio files to process."
    )
    parser.add_argument(
        "-w", "--workflow",
        required=True,
        help="Name of the workflow template to use (e.g., 'normalize_and_qc')."
    )
    parser.add_argument(
        "-u", "--url",
        default="http://127.0.0.1:8650",
        help="Base URL of the ATS-OSS API server (default: http://127.0.0.1:8650)."
    )

    args = parser.parse_args()

    input_dir = Path(args.directory)

    if not input_dir.is_dir():
        print(f"Error: The specified directory does not exist: {input_dir}")
        return

    print(f"Scanning '{input_dir}' for audio files...")

    # Find all files with supported extensions
    files_to_process = [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files_to_process:
        print("No supported audio files found to process.")
        return

    print(f"Found {len(files_to_process)} file(s) to submit.\n")

    for file_path in files_to_process:
        submit_file(args.url, args.workflow, file_path)
        print("-" * 20)

if __name__ == "__main__":
    main()
