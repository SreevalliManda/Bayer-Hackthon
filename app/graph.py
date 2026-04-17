import os
from typing import List, Dict, Any
from pydantic import BaseModel
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq LLM configuration
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
AGENT_MODEL_OVERRIDES = {
    "commander_agent": os.getenv("GROQ_MODEL_COMMANDER"),
    "logs_agent": os.getenv("GROQ_MODEL_LOGS"),
    "metrics_agent": os.getenv("GROQ_MODEL_METRICS"),
    "deploy_agent": os.getenv("GROQ_MODEL_DEPLOY"),
    "commander_correlation_decision": os.getenv("GROQ_MODEL_CORRELATION"),
    "generate_report": os.getenv("GROQ_MODEL_REPORT")
}

def get_agent_model(agent_name: str) -> str:
    return AGENT_MODEL_OVERRIDES.get(agent_name) or DEFAULT_GROQ_MODEL


def get_agent_llm(agent_name: str) -> ChatGroq:
    return ChatGroq(
        model=get_agent_model(agent_name),
        api_key=os.getenv("GROQ_API_KEY")
    )

# Define the state
class IncidentState(BaseModel):
    metrics_data: List[Dict[str, Any]]
    logs_data: List[Dict[str, Any]]
    deploy_data: List[Dict[str, Any]]
    alerts_data: List[Dict[str, Any]]
    investigation_plan: str = ""
    metrics_analysis: str = ""
    logs_analysis: str = ""
    deploy_analysis: str = ""
    correlation: str = ""
    decision: str = ""
    confidence: float = 0.0
    report: str = ""

# Agent functions
def commander_agent(state: IncidentState) -> IncidentState:
    """Commander Agent: The Orchestrator - Evaluates alerts, develops plan, coordinates investigation"""
    alerts = state.alerts_data
    
    # Evaluate alerts and develop investigation plan
    critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
    high_alerts = [a for a in alerts if a.get('severity') == 'high']
    
    if critical_alerts:
        priority = "CRITICAL - Full investigation required"
        focus = "All systems: metrics, logs, and deployments"
    elif high_alerts:
        priority = "HIGH - Targeted investigation needed"
        alert_types = set(a.get('alert_type', '') for a in high_alerts)
        if 'db_timeout' in alert_types or 'latency_spike' in alert_types:
            focus = "Focus on database performance, logs, and recent deployments"
        else:
            focus = "Focus on metrics and logs"
    else:
        priority = "MEDIUM - Monitor and investigate metrics"
        focus = "Primary focus on performance metrics"
    
    investigation_plan = f"""
    INVESTIGATION PLAN:
    Priority Level: {priority}
    Focus Areas: {focus}
    Alert Timeline: {', '.join([f"{a.get('timestamp', '')}: {a.get('description', '')}" for a in sorted(alerts, key=lambda x: x.get('timestamp', ''))])}
    
    Coordinating specialized investigators based on alert analysis.
    """
    
    state_data = state.dict()
    state_data["investigation_plan"] = investigation_plan
    return IncidentState(**state_data)

def logs_agent(state: IncidentState) -> IncidentState:
    """Logs Agent: The Forensic Expert - Deep-scans logs for stack traces and error correlations"""
    try:
        prompt = f"""
        You are the Logs Agent - Forensic Expert. Deep-scan these application logs to find specific stack traces and error correlations.
        
        Logs Data: {state.logs_data}
        
        Your analysis should include:
        1. Error patterns and frequencies
        2. Stack traces or detailed error information
        3. Correlations between different error types
        4. Timeline of error progression
        5. Any repeated or escalating issues
        
        Focus on ERROR and CRITICAL level entries, and identify sequences that suggest problems.
        """
        
        response = get_agent_llm("logs_agent").invoke(prompt)
        analysis = response.content
    except Exception as e:
        # Fallback analysis without LLM
        error_logs = [log for log in state.logs_data if log.get("level") in ["ERROR", "CRITICAL"]]
        analysis = f"""
        LOGS ANALYSIS (Fallback Mode):
        Total Error Logs: {len(error_logs)}
        Error Types Found: {set(log.get("message", "").split()[0] for log in error_logs if log.get("message"))}
        Timeline: {' -> '.join([f"{log.get('timestamp')}: {log.get('message')}" for log in error_logs[:3]])}
        Note: LLM analysis unavailable, using basic pattern detection.
        """
    
    state_data = state.dict()
    state_data["logs_analysis"] = analysis
    return IncidentState(**state_data)

def metrics_agent(state: IncidentState) -> IncidentState:
    """Metrics Agent: The Telemetry Analyst - Monitors performance counters for anomalies"""
    try:
        prompt = f"""
        You are the Metrics Agent - Telemetry Analyst. Monitor these performance counters to spot anomalies.
        
        Metrics Data: {state.metrics_data}
        
        Analyze for:
        1. Latency spikes (p99 patterns)
        2. High CPU usage patterns
        3. Memory leak indicators
        4. Request rate anomalies
        5. Performance degradation trends
        
        Provide detailed analysis of any anomalies found, including timestamps, severity, and potential causes.
        Calculate baselines and identify deviations from normal patterns.
        """
        
        response = get_agent_llm("metrics_agent").invoke(prompt)
        analysis = response.content
    except Exception as e:
        # Fallback analysis
        if state.metrics_data:
            latencies = [m.get("latency_ms", 0) for m in state.metrics_data]
            max_latency = max(latencies) if latencies else 0
            analysis = f"""
            METRICS ANALYSIS (Fallback Mode):
            Data Points: {len(state.metrics_data)}
            Max Latency: {max_latency}ms
            Anomalies Detected: {'Yes' if max_latency > 1000 else 'No'}
            Note: LLM analysis unavailable, using basic threshold detection.
            """
        else:
            analysis = "No metrics data available for analysis."
    
    state_data = state.dict()
    state_data["metrics_analysis"] = analysis
    return IncidentState(**state_data)

def deploy_agent(state: IncidentState) -> IncidentState:
    """Deploy Intelligence Agent: The Historian - Maps errors against deployment timeline"""
    try:
        prompt = f"""
        You are the Deploy Intelligence Agent - Historian. Map real-time errors against the timeline of CI/CD deployments.
        
        Deployment Data: {state.deploy_data}
        Alert Timeline: {state.alerts_data}
        
        Your analysis should:
        1. Identify recent deployments and configuration changes
        2. Correlate error occurrences with deployment timing
        3. Map specific errors to deployment changes
        4. Identify potential causal relationships
        5. Flag deployments that may have introduced issues
        
        Consider the chronological relationship between deployments and subsequent errors.
        """
        
        response = get_agent_llm("deploy_agent").invoke(prompt)
        analysis = response.content
    except Exception as e:
        # Fallback analysis
        recent_deploys = state.deploy_data[-3:] if state.deploy_data else []
        analysis = f"""
        DEPLOYMENT ANALYSIS (Fallback Mode):
        Recent Deployments: {len(recent_deploys)}
        Latest Changes: {[d.get('change', '') for d in recent_deploys]}
        Note: LLM analysis unavailable, showing recent deployment summary.
        """
    
    state_data = state.dict()
    state_data["deploy_analysis"] = analysis
    return IncidentState(**state_data)

def commander_correlation_decision(state: IncidentState) -> IncidentState:
    """Commander Agent: Correlate findings and make final decisions"""
    try:
        prompt = f"""
        You are the Commander Agent completing the investigation. Correlate all findings and make final decisions.
        
        Investigation Plan: {state.investigation_plan}
        
        Specialized Agent Reports:
        - Metrics Analysis: {state.metrics_analysis}
        - Logs Analysis: {state.logs_analysis}
        - Deploy Analysis: {state.deploy_analysis}
        
        Your tasks:
        1. CORRELATE findings across all agents to identify relationships
        2. DETERMINE root cause based on evidence
        3. PROVIDE specific recommendations and actions
        4. ASSIGN confidence level (0-100%) to your assessment
        5. IDENTIFY prevention measures
        
        Structure your response with clear sections:
        - Correlation Analysis
        - Root Cause Determination  
        - Recommended Actions
        - Confidence Level
        - Prevention Measures
        """
        
        response = get_agent_llm("commander_correlation_decision").invoke(prompt)
        content = response.content
        
        # Extract confidence from response
        confidence = 0.0
        import re
        match = re.search(r'(\d+)%', content)
        if match:
            confidence = float(match.group(1)) / 100
        
        decision = content
    except Exception as e:
        # Fallback correlation and decision
        confidence = 0.5  # 50% confidence for fallback
        decision = f"""
        COMMANDER DECISION (Fallback Mode):
        
        Correlation Analysis:
        - Metrics show anomalies: {'Yes' if 'Anomalies Detected: Yes' in state.metrics_analysis else 'No'}
        - Logs show errors: {'Yes' if 'ERROR' in state.logs_analysis or 'CRITICAL' in state.logs_analysis else 'No'}
        - Recent deployments identified: {'Yes' if state.deploy_data else 'No'}
        
        Root Cause Determination:
        Based on pattern analysis, likely related to recent system changes or performance issues.
        
        Recommended Actions:
        1. Review recent deployments for potential issues
        2. Monitor system performance metrics
        3. Check application logs for error patterns
        
        Confidence Level: 50%
        
        Prevention Measures:
        - Implement automated monitoring alerts
        - Regular deployment validation
        - Performance baseline monitoring
        
        Note: LLM analysis unavailable, using rule-based correlation.
        """
    
    state_data = state.dict()
    state_data["correlation"] = "Correlation and decision analysis completed by Commander Agent"
    state_data["decision"] = decision
    state_data["confidence"] = confidence
    return IncidentState(**state_data)

def generate_report(state: IncidentState) -> IncidentState:
    """Generate final incident report"""
    prompt = f"""
    Generate a comprehensive incident report based on the Commander Agent's complete investigation:
    
    Investigation Overview: {state.investigation_plan}
    Metrics Findings: {state.metrics_analysis}
    Logs Findings: {state.logs_analysis}
    Deployment Analysis: {state.deploy_analysis}
    Commander Decision: {state.decision}
    Confidence Level: {state.confidence * 100}%
    
    Create a professional incident report with:
    - Executive Summary
    - Investigation Timeline
    - Root Cause Analysis
    - Impact Assessment
    - Recommendations
    - Prevention Measures
    """
    
    response = get_agent_llm("generate_report").invoke(prompt)
    state_data = state.dict()
    state_data["report"] = response.content
    return IncidentState(**state_data)

# Build the graph with 4 agents (sequential to avoid concurrent update issues)
def create_incident_graph():
    graph = StateGraph(IncidentState)
    
    # Add nodes - only 4 agents
    graph.add_node("commander_agent", commander_agent)
    graph.add_node("logs_agent", logs_agent)
    graph.add_node("metrics_agent", metrics_agent)
    graph.add_node("deploy_agent", deploy_agent)
    graph.add_node("commander_correlation_decision", commander_correlation_decision)
    graph.add_node("generate_report", generate_report)

    # Define flow: Commander starts -> sequential specialized agents -> Commander correlates/decides -> Report
    graph.set_entry_point("commander_agent")

    # Sequential execution to avoid concurrent state update conflicts
    graph.add_edge("commander_agent", "logs_agent")
    graph.add_edge("logs_agent", "metrics_agent")
    graph.add_edge("metrics_agent", "deploy_agent")
    graph.add_edge("deploy_agent", "commander_correlation_decision")
    
    # Final report generation
    graph.add_edge("commander_correlation_decision", "generate_report")
    graph.add_edge("generate_report", END)
    
    return graph.compile()

# Create the compiled graph
incident_graph = create_incident_graph()