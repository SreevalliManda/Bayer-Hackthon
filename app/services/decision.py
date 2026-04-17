def decide(data, correlation):
    """Make decisions based on findings and correlations"""
    if correlation.get("correlated"):
        deploy = data.get("deploy", {})
        deploy_correlations = deploy.get("deployment_error_correlations", [])

        if deploy_correlations:
            # Find the most recent correlated deployment
            recent_correlation = deploy_correlations[-1]  # Last one is most recent
            return {
                "root_cause": f"Deployment issue: {recent_correlation['deployment']['change']}",
                "action": "Rollback deployment or investigate deployment changes",
                "confidence": "85%"
            }

        # Check for repeated log errors
        logs = data.get("logs", {})
        repeated_errors = logs.get("repeated_errors", {})
        if repeated_errors:
            error_types = list(repeated_errors.keys())
            return {
                "root_cause": f"Persistent errors: {', '.join(error_types)}",
                "action": "Investigate and fix repeated error patterns",
                "confidence": "80%"
            }

        # Check for metrics anomalies
        metrics = data.get("metrics", {})
        anomalies = metrics.get("anomalies", [])
        if anomalies:
            anomaly_types = set(a["type"] for a in anomalies)
            if "latency_spike" in anomaly_types:
                return {
                    "root_cause": "Performance degradation - latency spikes",
                    "action": "Check database connections, caching, and resource utilization",
                    "confidence": "75%"
                }

    return {
        "root_cause": "Multiple potential causes - requires further investigation",
        "action": "Continue monitoring and gather more data",
        "confidence": "50%"
    }