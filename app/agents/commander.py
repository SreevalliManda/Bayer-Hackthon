from app.agents.metrics_agent import analyze_metrics
from app.agents.logs_agent import analyze_logs
from app.agents.deploy_agent import analyze_deploy

def run_investigation():
    metrics = analyze_metrics()
    logs = analyze_logs()
    deploy = analyze_deploy()

    return {
        "metrics": metrics,
        "logs": logs,
        "deploy": deploy
    }