def correlate(data):
    """Correlate findings from all agents to identify common causes"""
    metrics = data.get("metrics", {})
    logs = data.get("logs", {})
    deploy = data.get("deploy", {})

    correlations = []

    # Check for metrics anomalies and log errors
    has_anomalies = len(metrics.get("anomalies", [])) > 0
    has_errors = logs.get("total_errors", 0) > 0

    if has_anomalies and has_errors:
        correlations.append("Metrics anomalies coincide with log errors")

    # Check for deployment correlations
    deploy_correlations = deploy.get("deployment_error_correlations", [])
    if deploy_correlations:
        correlations.append("Recent deployments correlate with error patterns")

    # Check for repeated errors
    repeated_errors = logs.get("repeated_errors", {})
    if repeated_errors:
        correlations.append("Repeated error patterns detected in logs")

    return {
        "correlated": len(correlations) > 0,
        "insights": correlations
    }