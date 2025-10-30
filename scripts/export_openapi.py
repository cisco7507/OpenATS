from ats_oss.api.server import app
import json

with open("docs/openapi.json", "w") as f:
    json.dump(app.openapi(), f, indent=2)
