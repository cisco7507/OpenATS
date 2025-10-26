from concurrent.futures import ThreadPoolExecutor
import yaml
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "ats_oss", "config", "config.yaml")

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

MAX_WORKERS = config["workers"]["threads"]

executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)


def submit_job(func, *args, **kwargs):
    return executor.submit(func, *args, **kwargs)


def shutdown():
    executor.shutdown()
