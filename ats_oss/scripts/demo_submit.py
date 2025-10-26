import requests
import json
import uuid

API_URL = "http://127.0.0.1:8650/workflows"


def submit_workflow(template_name, input_uri):
    payload = {"template_name": template_name, "input_uri": input_uri}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            f"{API_URL}/submitWorkflow",
            data=json.dumps(payload),
            headers=headers,
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        workflow = response.json()
        print("Workflow submitted successfully:")
        print(json.dumps(workflow, indent=2))
        return workflow
    except requests.exceptions.RequestException as e:
        print(f"Error submitting workflow: {e}")
        if e.response:
            print("Response content:")
            print(e.response.text)
        return None


def get_workflow_status(wfuuid: str):
    try:
        response = requests.get(f"{API_URL}/getWorkflowStatus?wfuuid={wfuuid}")
        response.raise_for_status()
        status = response.json()
        print("\nWorkflow status:")
        print(json.dumps(status, indent=2))
        return status
    except requests.exceptions.RequestException as e:
        print(f"Error getting workflow status: {e}")
        if e.response:
            print("Response content:")
            print(e.response.text)
        return None


if __name__ == "__main__":
    submitted_workflow = submit_workflow("normalize_and_qc", "path/to/your/audio.wav")
    if submitted_workflow and submitted_workflow.get("id"):
        get_workflow_status(submitted_workflow["id"])
