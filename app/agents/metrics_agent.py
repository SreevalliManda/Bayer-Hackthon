import json
import statistics

def analyze_metrics():
    """Metrics Agent: Telemetry Analyst - Monitors performance counters for anomalies"""
    with open("app/data/metrics.json") as f:
        metrics = json.load(f)
    
    if not metrics:
        return {"anomalies": [], "summary": "No metrics data available"}
    
    # Extract performance counters
    latencies = [m["latency_ms"] for m in metrics]
    cpus = [m["cpu"] for m in metrics]
    memories = [m["memory"] for m in metrics]
    requests = [m["requests_per_sec"] for m in metrics]
    
    # Calculate baselines (using first 10 readings as baseline)
    baseline_size = min(10, len(metrics))
    baseline_latencies = latencies[:baseline_size]
    baseline_cpus = cpus[:baseline_size]
    baseline_memories = memories[:baseline_size]
    baseline_requests = requests[:baseline_size]
    
    # Calculate statistics
    try:
        latency_mean = statistics.mean(baseline_latencies)
        latency_stdev = statistics.stdev(baseline_latencies) if len(baseline_latencies) > 1 else 0
        cpu_mean = statistics.mean(baseline_cpus)
        memory_mean = statistics.mean(baseline_memories)
        requests_mean = statistics.mean(baseline_requests)
    except statistics.StatisticsError:
        return {"anomalies": [], "summary": "Insufficient data for analysis"}
    
    # Detect anomalies (using 2-sigma rule for simplicity)
    anomalies = []
    
    for i, metric in enumerate(metrics[baseline_size:], start=baseline_size):
        timestamp = metric["timestamp"]
        
        # Latency anomaly (p99 equivalent - high latency)
        if metric["latency_ms"] > latency_mean + 2 * latency_stdev:
            anomalies.append({
                "type": "latency_spike",
                "timestamp": timestamp,
                "value": metric["latency_ms"],
                "baseline": latency_mean,
                "severity": "high" if metric["latency_ms"] > latency_mean + 3 * latency_stdev else "medium"
            })
        
        # CPU anomaly
        if metric["cpu"] > cpu_mean + 15:  # Arbitrary threshold for high CPU
            anomalies.append({
                "type": "high_cpu",
                "timestamp": timestamp,
                "value": metric["cpu"],
                "baseline": cpu_mean,
                "severity": "medium"
            })
        
        # Memory leak pattern (gradual increase)
        if i > baseline_size + 5:
            recent_memories = memories[i-5:i+1]
            if len(recent_memories) >= 3 and all(recent_memories[j] <= recent_memories[j+1] for j in range(len(recent_memories)-1)):
                anomalies.append({
                    "type": "memory_leak_pattern",
                    "timestamp": timestamp,
                    "value": metric["memory"],
                    "trend": "increasing",
                    "severity": "medium"
                })
        
        # Requests drop
        if metric["requests_per_sec"] < requests_mean * 0.7:  # 30% drop
            anomalies.append({
                "type": "requests_drop",
                "timestamp": timestamp,
                "value": metric["requests_per_sec"],
                "baseline": requests_mean,
                "severity": "medium"
            })
    
    # Summary
    summary = f"Analyzed {len(metrics)} metrics points. Found {len(anomalies)} anomalies."
    if anomalies:
        summary += f" Types: {', '.join(set(a['type'] for a in anomalies))}"
    
    return {
        "anomalies": anomalies,
        "summary": summary,
        "baseline_stats": {
            "latency_mean": latency_mean,
            "cpu_mean": cpu_mean,
            "memory_mean": memory_mean,
            "requests_mean": requests_mean
        }
    }