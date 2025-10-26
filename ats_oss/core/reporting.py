import json
from pathlib import Path

def save_json_report(report_data: dict, output_dir: Path, filename: str = "report.json"):
    """
    Saves a dictionary as a JSON file in the specified directory.
    """
    output_path = output_dir / filename

    try:
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"JSON report saved to: {output_path}")
        return str(output_path)
    except TypeError as e:
        # This can happen if the data contains non-serializable types
        raise TypeError(f"Failed to serialize report data to JSON: {e}")
    except Exception as e:
        raise IOError(f"Failed to write JSON report to {output_path}: {e}")
