import time
from typing import Dict, Any

def handle_sleep(payload: Dict[str, Any]) -> Dict[str, Any]:
    seconds = payload.get("seconds", 1)
    time.sleep(seconds)
    return {"slept": seconds}
