import json
from collections import defaultdict

def analyze_logs():
    """Logs Agent: Forensic Expert - Deep-scans logs for stack traces and error correlations"""
    with open("app/data/logs.json") as f:
        logs = json.load(f)
    
    # Deep-scan for error patterns and correlations
    error_logs = [log for log in logs if log["level"] in ["ERROR", "CRITICAL"]]
    warning_logs = [log for log in logs if log["level"] == "WARN"]
    
    # Find stack traces (assuming messages contain stack info)
    stack_traces = [log for log in error_logs if "stack" in log["message"].lower() or "traceback" in log["message"].lower()]
    
    # Correlate errors by type
    error_types = defaultdict(list)
    for log in error_logs:
        if "timeout" in log["message"].lower():
            error_types["db_timeout"].append(log)
        elif "cache" in log["message"].lower():
            error_types["cache_failure"].append(log)
        elif "unresponsive" in log["message"].lower():
            error_types["service_down"].append(log)
        else:
            error_types["other"].append(log)
    
    # Analyze error progression and patterns
    timestamps = [log["timestamp"] for log in logs]
    error_timeline = sorted(error_logs, key=lambda x: x["timestamp"])
    
    # Look for repeated errors or escalating issues
    repeated_errors = {}
    for error_type, logs_list in error_types.items():
        if len(logs_list) > 1:
            repeated_errors[error_type] = {
                "count": len(logs_list),
                "timestamps": [log["timestamp"] for log in logs_list],
                "messages": [log["message"] for log in logs_list]
            }
    
    return {
        "total_errors": len(error_logs),
        "error_types": dict(error_types),
        "stack_traces_found": len(stack_traces),
        "repeated_errors": repeated_errors,
        "error_timeline": [log["timestamp"] + ": " + log["message"] for log in error_timeline[:5]],  # Most recent 5
        "warnings_count": len(warning_logs)
    }