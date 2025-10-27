import yaml
from pathlib import Path

class Config:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self):
        # Use pathlib for robust path handling
        # __file__ is ats_oss/config.py, so parent is ats_oss/
        self.project_root = Path(__file__).parent.resolve()
        self.config_path = self.project_root / "config" / "config.yaml"
        self.workflows_dir = self.project_root / "workflows"

        with open(self.config_path, "r") as f:
            self.config = yaml.safe_load(f)

    @property
    def database_url(self):
        return self.config["database"]["dsn"]

    @property
    def max_workers(self):
        return self.config["workers"]["threads"]

    @property
    def data_root(self):
        # Resolve the data_root relative to the project root
        return self.project_root / self.config["paths"]["data_root"]

    def get_workflow_dir(self, workflow_id):
        return self.data_root / "workflows" / str(workflow_id)

    def get_workflow_subdirs(self, workflow_id):
        base_dir = self.get_workflow_dir(workflow_id)
        return {
            "base": base_dir,
            "input": base_dir / "input",
            "normalized": base_dir / "normalized",
            "wav_output": base_dir / "wav_output",
            "mp3_output": base_dir / "mp3_output",
            "flac_archive": base_dir / "flac_archive",
            "reports": base_dir / "reports",
            "logs": base_dir / "logs",
        }

    @property
    def logging_level(self):
        return self.config["logging"]["level"].upper()

# Create a singleton instance
settings = Config()
