import json
import os
from fastapi import FastAPI
from app.graph import incident_graph, IncidentState
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Incident AI - Advanced Multi-Agent System")

def load_data():
    """Load mock data from JSON files"""
    with open("app/data/metrics.json") as f:
        metrics_data = json.load(f)
    
    with open("app/data/logs.json") as f:
        logs_data = json.load(f)
    
    with open("app/data/deploy.json") as f:
        deploy_data = json.load(f)
    
    with open("app/data/alerts.json") as f:
        alerts_data = json.load(f)
    
    return metrics_data, logs_data, deploy_data, alerts_data

@app.get("/incident")
async def handle_incident():
    """Handle incident analysis using advanced LLM-powered multi-agent system"""
    try:
        # Load data
        metrics_data, logs_data, deploy_data, alerts_data = load_data()
        
        # Create initial state
        initial_state = IncidentState(
            metrics_data=metrics_data,
            logs_data=logs_data,
            deploy_data=deploy_data,
            alerts_data=alerts_data
        )
        
        # Run the incident analysis graph
        final_state = incident_graph.invoke(initial_state)
        
        # Return comprehensive results
        return {
            "status": "success",
            "investigation_plan": final_state.investigation_plan,
            "analysis": {
                "metrics_analysis": final_state.metrics_analysis,
                "logs_analysis": final_state.logs_analysis,
                "deploy_analysis": final_state.deploy_analysis,
                "correlation": final_state.correlation,
                "decision": final_state.decision,
                "confidence": f"{final_state.confidence * 100:.1f}%"
            },
            "report": final_state.report,
            "raw_data": {
                "metrics_count": len(metrics_data),
                "logs_count": len(logs_data),
                "deployments_count": len(deploy_data),
                "alerts_count": len(alerts_data)
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "details": "Ensure GROQ_API_KEY is set in .env file"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Incident AI Advanced"}

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "Incident AI - Advanced Multi-Agent Incident Response System",
        "version": "2.0",
        "endpoints": {
            "/incident": "Trigger full incident analysis",
            "/health": "Service health check"
        },
        "powered_by": "LangGraph + Groq LLM"
    }