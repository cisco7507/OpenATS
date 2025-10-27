import json
from pathlib import Path
import uuid
from datetime import datetime

class CustomJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder to handle non-serializable types like UUID and datetime.
    """
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            # Convert UUID to its string representation
            return str(obj)
        if isinstance(obj, datetime):
            # Convert datetime to ISO 8601 format string
            return obj.isoformat()
        if isinstance(obj, Path):
            # Convert Path objects to their string representation
            return str(obj)
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)

def save_json_report(report_data: dict, output_dir: Path, filename: str = "report.json"):
    """
    Saves a dictionary as a JSON file in the specified directory using a custom encoder.
    """
    output_path = output_dir / filename

    try:
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2, cls=CustomJSONEncoder)
        print(f"JSON report saved to: {output_path}")
        return str(output_path)
    except TypeError as e:
        # This can happen if the data contains non-serializable types
        raise TypeError(f"Failed to serialize report data to JSON: {e}")
    except Exception as e:
        raise IOError(f"Failed to write JSON report to {output_path}: {e}")
