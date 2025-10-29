import requests
import json
import uuid
import numpy as np
import soundfile as sf

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
    # Create a dummy silent WAV file for testing
    samplerate = 48000
    duration = 1.0

    # 2-channel
    data_2ch = np.zeros((int(samplerate * duration), 2))
    sf.write("test_audio_2ch.wav", data_2ch, samplerate)

    # 6-channel
    data_6ch = np.zeros((int(samplerate * duration), 6))
    sf.write("test_audio_6ch.wav", data_6ch, samplerate)

    submitted_workflow_2ch = submit_workflow("Conditional_Transcode_Flow", "test_audio_2ch.wav")
    submitted_workflow_6ch = submit_workflow("Conditional_Transcode_Flow", "test_audio_6ch.wav")

    import time
    time.sleep(5) # Wait for workflows to complete

    if submitted_workflow_2ch and submitted_workflow_2ch.get("id"):
        print("\nFinal Workflow status for 2ch:")
        get_workflow_status(submitted_workflow_2ch["id"])

    if submitted_workflow_6ch and submitted_workflow_6ch.get("id"):
        print("\nFinal Workflow status for 6ch:")
        get_workflow_status(submitted_workflow_6ch["id"])
