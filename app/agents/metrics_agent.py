import json

def analyze_metrics():
    with open("app/data/metrics.json") as f:
        data = json.load(f)

    if data["latency_ms"] > 1000:
        return {"anomaly": True, "reason": "High latency"}
    
    return {"anomaly": False}