import requests
import json

API_URL = "http://127.0.0.1:8650/workflows"


def submit_workflow(template_name, input_uri):
    try:
        response = requests.post(
            f"{API_URL}/submitWorkflow",
            params={"template_name": template_name, "input_uri": input_uri},
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        print("Workflow submitted successfully:")
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error submitting workflow: {e}")
        if e.response:
            print("Response content:")
            print(e.response.text)


if __name__ == "__main__":
    submit_workflow("normalize_and_qc", "path/to/your/audio.wav")
