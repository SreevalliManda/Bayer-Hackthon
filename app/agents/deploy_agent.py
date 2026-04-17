import json
from datetime import datetime

def analyze_deploy():
    """Deploy Intelligence Agent: Historian - Maps errors against deployment timeline"""
    with open("app/data/deploy.json") as f:
        deployments = json.load(f)
    
    with open("app/data/alerts.json") as f:
        alerts = json.load(f)
    
    with open("app/data/logs.json") as f:
        logs = json.load(f)
    
    # Sort deployments by time
    sorted_deploys = sorted(deployments, key=lambda x: x["deployment_time"])
    
    # Find recent deployments (last few)
    recent_deploys = sorted_deploys[-5:]  # Last 5 deployments
    
    # Map errors against deployment timeline
    error_events = []
    
    # Add alerts as error events
    for alert in alerts:
        if alert["severity"] in ["high", "critical"]:
            error_events.append({
                "timestamp": alert["timestamp"],
                "type": "alert",
                "description": alert["description"],
                "severity": alert["severity"]
            })
    
    # Add error logs
    for log in logs:
        if log["level"] in ["ERROR", "CRITICAL"]:
            error_events.append({
                "timestamp": log["timestamp"],
                "type": "log_error",
                "description": log["message"],
                "severity": "high" if log["level"] == "CRITICAL" else "medium"
            })
    
    # Sort error events by timestamp
    error_events.sort(key=lambda x: x["timestamp"])
    
    # Correlate errors with deployments
    correlations = []
    
    for deploy in sorted_deploys:
        deploy_time = deploy["deployment_time"]
        deploy_service = deploy["service"]
        
        # Find errors that occurred after this deployment
        post_deploy_errors = [
            error for error in error_events 
            if error["timestamp"] > deploy_time
        ]
        
        # Check if errors are related to the deployed service
        related_errors = [
            error for error in post_deploy_errors
            if deploy_service.lower() in error["description"].lower() or 
               any(keyword in error["description"].lower() for keyword in deploy["change"].lower().split())
        ]
        
        if related_errors:
            correlations.append({
                "deployment": deploy,
                "related_errors": related_errors,
                "time_gap": f"Errors started {min(e['timestamp'] for e in related_errors)} after deployment at {deploy_time}",
                "potential_cause": f"Deployment '{deploy['change']}' may have introduced issues"
            })
    
    # Identify recent changes that could be causing current issues
    latest_deploy = sorted_deploys[-1] if sorted_deploys else None
    recent_changes = []
    
    if latest_deploy:
        # Check if there are errors after the latest deployment
        latest_errors = [e for e in error_events if e["timestamp"] > latest_deploy["deployment_time"]]
        if latest_errors:
            recent_changes.append({
                "change": latest_deploy["change"],
                "time": latest_deploy["deployment_time"],
                "potential_impact": "Recent deployment may be causing current errors",
                "errors_after": len(latest_errors)
            })
    
    return {
        "recent_deployments": recent_deploys,
        "deployment_error_correlations": correlations,
        "recent_changes": recent_changes,
        "timeline_summary": f"Analyzed {len(sorted_deploys)} deployments against {len(error_events)} error events"
    }