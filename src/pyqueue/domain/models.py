from enum import Enum

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"

class JobType(str, Enum):
    SLEEP = "sleep"
    CSV_STATS = "csv_stats"
    FAIL = "fail"
