import pytest
from pyqueue.workers.handlers.csv_stats import handle_csv_stats
from pyqueue.workers.handlers.sleep import handle_sleep

def test_handle_csv_stats_success():
    payload = {"csv_text": "id,name\n1,alice\n2,bob\n"}
    result = handle_csv_stats(payload)
    assert result["rows"] == 2
    assert result["columns"] == 2
    assert result["headers"] == ["id", "name"]

def test_handle_csv_stats_empty():
    payload = {"csv_text": ""}
    result = handle_csv_stats(payload)
    assert result["rows"] == 0

def test_handle_csv_stats_missing_payload():
    with pytest.raises(ValueError):
        handle_csv_stats({})

def test_handle_sleep():
    # Only testing that it runs, mocking time.sleep would be better practically but overkill for MVP
    result = handle_sleep({"seconds": 0.1})
    assert result["slept"] == 0.1
