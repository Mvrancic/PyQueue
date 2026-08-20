from typing import Dict, Any

def handle_fail(payload: Dict[str, Any]) -> Dict[str, Any]:
    raise Exception("This job is destined to fail")
