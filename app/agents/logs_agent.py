import json

def analyze_logs():
    with open("app/data/logs.json") as f:
        logs = json.load(f)

    errors = [log for log in logs if "timeout" in log["error"]]

    return {"db_timeout": len(errors) > 0}