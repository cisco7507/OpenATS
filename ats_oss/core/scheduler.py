from concurrent.futures import ThreadPoolExecutor
from ats_oss.config import settings

MAX_WORKERS = settings.max_workers

executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)


def submit_job(func, *args, **kwargs):
    return executor.submit(func, *args, **kwargs)


def shutdown():
    executor.shutdown()
