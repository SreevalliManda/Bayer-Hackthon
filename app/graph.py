import os
from typing import List, Dict, Any
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq LLM
model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
llm = ChatGroq(
    model=model_name,
    api_key=os.getenv("GROQ_API_KEY")
)

# Define the state
class IncidentState(BaseModel):
    metrics_data: List[Dict[str, Any]]
    logs_data: List[Dict[str, Any]]
    deploy_data: List[Dict[str, Any]]
    alerts_data: List[Dict[str, Any]]
    metrics_analysis: str = ""
    logs_analysis: str = ""
    deploy_analysis: str = ""
    correlation: str = ""
    decision: str = ""
    confidence: float = 0.0
    report: str = ""

# Agent functions
def start_analysis(state: IncidentState) -> IncidentState:
    """Entry point that starts parallel analysis"""
    return state

def metrics_agent(state: IncidentState) -> IncidentState:
    """Analyze metrics data using LLM"""
    prompt = f"""
    Analyze the following metrics data for anomalies. Look for spikes in latency, high CPU/memory usage, or drops in requests per second.
    Data: {state.metrics_data}
    
    Provide a detailed analysis of any anomalies found, including timestamps and severity.
    If no anomalies, state that the metrics appear normal.
    """
    
    response = llm.invoke(prompt)
    state_data = state.dict()
    state_data["metrics_analysis"] = response.content
    return IncidentState(**state_data)

def logs_agent(state: IncidentState) -> IncidentState:
    """Analyze logs data using LLM"""
    prompt = f"""
    Analyze the following log entries for errors, warnings, and patterns that might indicate issues.
    Data: {state.logs_data}
    
    Identify any error patterns, critical issues, or sequences that suggest problems.
    Focus on ERROR and CRITICAL level logs, and look for repeated issues.
    """
    
    response = llm.invoke(prompt)
    state_data = state.dict()
    state_data["logs_analysis"] = response.content
    return IncidentState(**state_data)

def deploy_agent(state: IncidentState) -> IncidentState:
    """Analyze deployment data using LLM"""
    prompt = f"""
    Analyze the following deployment history to identify recent changes that might be related to issues.
    Data: {state.deploy_data}
    
    Look for recent deployments, configuration changes, or version updates that could impact system stability.
    Consider the timing of deployments relative to potential incidents.
    """
    
    response = llm.invoke(prompt)
    state_data = state.dict()
    state_data["deploy_analysis"] = response.content
    return IncidentState(**state_data)

def correlation_agent(state: IncidentState) -> IncidentState:
    """Correlate findings from all agents using LLM"""
    prompt = f"""
    Correlate the following analyses to identify relationships between metrics anomalies, log errors, and recent deployments:
    
    Metrics Analysis: {state.metrics_analysis}
    Logs Analysis: {state.logs_analysis}
    Deployment Analysis: {state.deploy_analysis}
    
    Determine if these issues are related and what might be the common cause.
    Provide evidence for your correlation assessment.
    """
    
    response = llm.invoke(prompt)
    state_data = state.dict()
    state_data["correlation"] = response.content
    return IncidentState(**state_data)

def decision_agent(state: IncidentState) -> IncidentState:
    """Make decisions and recommendations using LLM"""
    prompt = f"""
    Based on the correlation analysis, determine the root cause of the incident and recommend actions:
    
    Correlation: {state.correlation}
    
    Provide:
    1. Root cause analysis
    2. Recommended immediate actions
    3. Confidence level (0-100%) in your assessment
    4. Any additional monitoring or preventive measures
    
    Format your response clearly with sections.
    """
    
    response = llm.invoke(prompt)
    
    # Parse confidence from response (simple extraction)
    content = response.content
    confidence = 0.0
    if "confidence" in content.lower():
        # Extract percentage
        import re
        match = re.search(r'(\d+)%', content)
        if match:
            confidence = float(match.group(1)) / 100
    
    state_data = state.dict()
    state_data["decision"] = response.content
    state_data["confidence"] = confidence
    return IncidentState(**state_data)

def report_agent(state: IncidentState) -> IncidentState:
    """Generate final incident report using LLM"""
    prompt = f"""
    Generate a comprehensive incident report based on all analyses:
    
    Metrics: {state.metrics_analysis}
    Logs: {state.logs_analysis}
    Deployments: {state.deploy_analysis}
    Correlation: {state.correlation}
    Decision: {state.decision}
    Confidence: {state.confidence * 100}%
    
    Create a professional incident report including:
    - Executive Summary
    - Timeline of Events
    - Root Cause Analysis
    - Impact Assessment
    - Recommendations
    - Prevention Measures
    
    Format as a clear, structured report.
    """
    
    response = llm.invoke(prompt)
    state_data = state.dict()
    state_data["report"] = response.content
    return IncidentState(**state_data)

# Build the graph
def create_incident_graph():
    graph = StateGraph(IncidentState)
    
    # Add nodes
    graph.add_node("start_analysis", start_analysis)
    graph.add_node("metrics_agent", metrics_agent)
    graph.add_node("logs_agent", logs_agent)
    graph.add_node("deploy_agent", deploy_agent)
    graph.add_node("correlation_agent", correlation_agent)
    graph.add_node("decision_agent", decision_agent)
    graph.add_node("report_agent", report_agent)

    # Define flow: start -> parallel analysis -> correlation -> decision -> report
    graph.set_entry_point("start_analysis")

    # Start all three agents in parallel
    graph.add_edge("start_analysis", "metrics_agent")
    graph.add_edge("start_analysis", "logs_agent")
    graph.add_edge("start_analysis", "deploy_agent")
    
    # Then decision and report
    graph.add_edge("correlation_agent", "decision_agent")
    graph.add_edge("decision_agent", "report_agent")
    graph.add_edge("report_agent", END)
    
    return graph.compile()

# Create the compiled graph
incident_graph = create_incident_graph()