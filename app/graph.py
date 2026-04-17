import os
from typing import List, Dict, Any
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

# Initialize shared LLM configuration (single model for all agents)
DEFAULT_LLM_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

def get_agent_llm(agent_name: str) -> ChatOpenAI:
    """Return a shared OpenAI-based LLM for all agents.

    The agent_name is accepted for compatibility but ignored because
    we use a single model for all agents as requested.
    """
    return ChatOpenAI(
        model=DEFAULT_LLM_MODEL,
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.0
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
    if isinstance(state, dict):
        state = IncidentState(**state)
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
    return state_data

def logs_agent(state: IncidentState) -> IncidentState:
    """Logs Agent: The Forensic Expert - Deep-scans logs for stack traces and error correlations"""
    if isinstance(state, dict):
        state = IncidentState(**state)
    try:
        prompt = f"""
        You are the Logs Agent - Forensic Expert. Deep-scan these application logs to find specific stack traces and error correlations.
        
        Logs Data: {state.logs_data}
        
        Your analysis should include:
        1. Error patterns and frequencies
        2. Stack traces or detailed error information
        3. Correlations between different error types (especially DB timeouts with latency spikes)
        4. Timeline of error progression
        5. Any repeated or escalating issues
        6. SPECIAL ATTENTION: DB connection timeouts often indicate connection pool exhaustion
        
        Focus on ERROR and CRITICAL level entries, and identify sequences that suggest problems.
        Look for patterns like:
        - Repeated "DB connection timeout" errors within short windows (5-10 minutes)
        - Timeout escalation (timeouts increasing in frequency/severity)
        - Service becoming unresponsive after timeout cascade
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
    return state_data

def metrics_agent(state: IncidentState) -> IncidentState:
    """Metrics Agent: The Telemetry Analyst - Monitors performance counters for anomalies"""
    if isinstance(state, dict):
        state = IncidentState(**state)
    try:
        prompt = f"""
        You are the Metrics Agent - Telemetry Analyst. Monitor these performance counters to spot anomalies.
        
        Metrics Data: {state.metrics_data}
        
        Analyze for:
        1. Latency spikes (p99 patterns) - especially those exceeding 1000ms threshold
        2. High CPU usage patterns and correlation with latency
        3. Memory leak indicators or sustained high memory usage
        4. Request rate anomalies - sudden drops in throughput with latency spikes
        5. Performance degradation trends
        6. CRITICAL: Look for sudden latency spikes (e.g., 120ms baseline → 2000ms+)
        
        Provide detailed analysis of any anomalies found, including timestamps, severity, and potential causes.
        Calculate baselines and identify deviations from normal patterns.
        
        IMPORTANT PATTERN: If latency spike is followed by request rate drop, indicates system under stress or connections exhausted.
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
            Latency Spike Pattern: {'Detected - suggests resource exhaustion' if max_latency > 1500 else 'Normal'}
            Note: LLM analysis unavailable, using basic threshold detection.
            """
        else:
            analysis = "No metrics data available for analysis."
    
    state_data = state.dict()
    state_data["metrics_analysis"] = analysis
    return state_data

def deploy_agent(state: IncidentState) -> IncidentState:
    """Deploy Intelligence Agent: The Historian - Maps errors against deployment timeline"""
    if isinstance(state, dict):
        state = IncidentState(**state)
    try:
        prompt = f"""
        You are the Deploy Intelligence Agent - Historian. Map real-time errors against the timeline of CI/CD deployments.
        
        Deployment Data: {state.deploy_data}
        Alert Timeline: {state.alerts_data}
        Logs Data: {state.logs_data}
        
        Your analysis should:
        1. Identify recent deployments and configuration changes (especially DB config, connection pools, timeouts)
        2. Correlate error occurrences with deployment timing (look for 5-20 minute lag)
        3. Map specific errors to deployment changes (e.g., DB timeouts after DB config update)
        4. Identify potential causal relationships - configuration bugs often manifest gradually
        5. Flag deployments that may have introduced issues, especially config/infrastructure changes
        6. Consider "latent bugs" - configurations that work initially then fail under load
        
        CRITICAL: Look for DB connection pool changes correlated with DB timeout errors.
        
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
    return state_data

def commander_correlation_decision(state: IncidentState) -> IncidentState:
    """Commander Agent: Correlate findings and make final decisions"""
    if isinstance(state, dict):
        state = IncidentState(**state)
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
        2. DETERMINE root cause based on evidence (prioritize deployment/config changes correlated with errors)
        3. PROVIDE specific recommendations and actions:
           - If DB config change detected before DB timeouts: RECOMMEND IMMEDIATE ROLLBACK
           - If latency spike follows config deployment: CONSIDER CONFIGURATION BUG
           - If errors resolve after rollback: CONFIRM ROOT CAUSE
        4. ASSIGN confidence level (0-100%) to your assessment
        5. IDENTIFY prevention measures (configuration testing, staged rollouts)
        
        SPECIAL FOCUS: Latent configuration bugs that manifest 5-20 minutes after deployment.
        
        Structure your response with clear sections:
        - Correlation Analysis
        - Root Cause Determination (include deployment correlation)
        - Recommended Actions (include rollback if applicable)
        - Confidence Level
        - Prevention Measures (focus on config validation and staged deployment)
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
        If DB config deployment detected before DB timeouts, this suggests a LATENT CONFIGURATION BUG.
        
        Recommended Actions:
        1. IMMEDIATE: Review recent configuration deployments (especially DB connection pool settings)
        2. If config change suspected: EXECUTE ROLLBACK to previous version
        3. Monitor system performance metrics
        4. Check application logs for error patterns
        
        Confidence Level: 50%
        
        Prevention Measures:
        - Implement configuration validation before deployment
        - Use staged rollout for infrastructure changes
        - Test connection pool settings under load before production
        - Automatic rollback on critical alerts
        
        Note: LLM analysis unavailable, using rule-based correlation.
        """
    
    state_data = state.dict()
    state_data["correlation"] = "Correlation and decision analysis completed by Commander Agent"
    state_data["decision"] = decision
    state_data["confidence"] = confidence
    return state_data

def generate_report(state: IncidentState) -> IncidentState:
    """Generate final incident report"""
    if isinstance(state, dict):
        state = IncidentState(**state)
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
    return state_data

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