import csv
import io
from typing import Dict, Any

def handle_csv_stats(payload: Dict[str, Any]) -> Dict[str, Any]:
    csv_text = payload.get("csv_text")
    if csv_text is None:
        raise ValueError("Missing 'csv_text' in payload")

    f = io.StringIO(csv_text)
    reader = csv.reader(f)
    
    try:
        headers = next(reader)
    except StopIteration:
        return {"rows": 0, "columns": 0, "headers": []}

    row_count = 0
    for row in reader:
        row_count += 1
        
    return {
        "rows": row_count,
        "columns": len(headers),
        "headers": headers
    }
