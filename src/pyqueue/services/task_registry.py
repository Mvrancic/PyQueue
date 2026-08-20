from typing import Callable, Dict, Any
from pyqueue.domain.models import JobType
from pyqueue.workers.handlers.sleep import handle_sleep
from pyqueue.workers.handlers.csv_stats import handle_csv_stats
from pyqueue.workers.handlers.fail import handle_fail

HandlerFunc = Callable[[Dict[str, Any]], Dict[str, Any]]

TASK_REGISTRY: Dict[str, HandlerFunc] = {
    JobType.SLEEP.value: handle_sleep,
    JobType.CSV_STATS.value: handle_csv_stats,
    JobType.FAIL.value: handle_fail,
}

def get_handler(job_type: str) -> HandlerFunc:
    return TASK_REGISTRY.get(job_type)
