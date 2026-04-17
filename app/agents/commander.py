import json
from app.agents.metrics_agent import analyze_metrics
from app.agents.logs_agent import analyze_logs
from app.agents.deploy_agent import analyze_deploy
from app.services.correlation import correlate
from app.services.decision import decide

def evaluate_alerts(alerts):
    """Evaluate initial alerts to determine investigation priority"""
    critical_alerts = [a for a in alerts if a['severity'] == 'critical']
    high_alerts = [a for a in alerts if a['severity'] == 'high']
    medium_alerts = [a for a in alerts if a['severity'] == 'medium']
    
    investigation_plan = {
        "priority": "low",
        "focus_areas": [],
        "timeline": sorted(alerts, key=lambda x: x['timestamp'])
    }
    
    if critical_alerts:
        investigation_plan["priority"] = "critical"
        investigation_plan["focus_areas"] = ["all"]
    elif high_alerts:
        investigation_plan["priority"] = "high"
        alert_types = set(a['alert_type'] for a in high_alerts)
        if 'db_timeout' in alert_types or 'latency_spike' in alert_types:
            investigation_plan["focus_areas"] = ["logs", "metrics", "deploy"]
        else:
            investigation_plan["focus_areas"] = ["metrics", "logs"]
    elif medium_alerts:
        investigation_plan["priority"] = "medium"
        investigation_plan["focus_areas"] = ["metrics"]
    
    return investigation_plan

def correlate_findings(findings):
    """Correlate findings from all agents to identify relationships"""
    # Use the correlation service
    correlation_result = correlate(findings)
    
    # Enhanced correlation logic
    correlations = []
    
    # Check for deployment-related issues
    if findings.get("deploy", {}).get("deployment_error_correlations"):
        correlations.append("Recent deployments correlate with error spikes")
    
    # Check for metrics and logs alignment
    metrics_anomalies = findings.get("metrics", {}).get("anomalies", [])
    logs_errors = findings.get("logs", {}).get("error_types", {})
    
    if metrics_anomalies and logs_errors:
        # Look for timing alignment
        anomaly_timestamps = set(a["timestamp"] for a in metrics_anomalies)
        error_timestamps = set()
        for error_list in logs_errors.values():
            for error in error_list:
                error_timestamps.add(error["timestamp"])
        
        overlapping_times = anomaly_timestamps & error_timestamps
        if overlapping_times:
            correlations.append(f"Metrics anomalies and log errors coincide at: {sorted(overlapping_times)}")
    
    return {
        "basic_correlation": correlation_result,
        "advanced_insights": correlations
    }

def make_decision(findings, correlation):
    """Make final decisions and recommendations"""
    # Use the decision service
    decision_result = decide(findings, correlation["basic_correlation"])
    
    # Enhanced decision logic based on all findings
    recommendations = []
    
    # Check for deployment rollback scenarios
    deploy_correlations = findings.get("deploy", {}).get("deployment_error_correlations", [])
    if deploy_correlations:
        recommendations.append("Consider rolling back recent deployments that correlate with errors")
    
    # Check for repeated errors
    repeated_errors = findings.get("logs", {}).get("repeated_errors", {})
    if repeated_errors:
        recommendations.append("Address repeated error patterns in logs")
    
    # Check for performance anomalies
    anomalies = findings.get("metrics", {}).get("anomalies", [])
    if anomalies:
        anomaly_types = set(a["type"] for a in anomalies)
        if "latency_spike" in anomaly_types:
            recommendations.append("Investigate latency spikes - check database connections and caching")
        if "high_cpu" in anomaly_types:
            recommendations.append("Monitor CPU usage - consider scaling or optimization")
    
    return {
        "primary_decision": decision_result,
        "recommendations": recommendations
    }

def run_investigation():
    """Commander Agent: Orchestrates the complete investigation process"""
    # Load initial alerts
    with open("app/data/alerts.json") as f:
        alerts = json.load(f)
    
    # Evaluate alerts and develop investigation plan
    plan = evaluate_alerts(alerts)
    
    # Coordinate specialized investigators based on plan
    findings = {}
    
    if "metrics" in plan["focus_areas"] or plan["focus_areas"] == ["all"]:
        findings["metrics"] = analyze_metrics()
    
    if "logs" in plan["focus_areas"] or plan["focus_areas"] == ["all"]:
        findings["logs"] = analyze_logs()
    
    if "deploy" in plan["focus_areas"] or plan["focus_areas"] == ["all"]:
        findings["deploy"] = analyze_deploy()
    
    # Correlate findings across all agents
    correlation = correlate_findings(findings)
    
    # Make final decisions and recommendations
    decision = make_decision(findings, correlation)
    
    return {
        "investigation_plan": plan,
        "findings": findings,
        "correlation": correlation,
        "decision": decision
    }