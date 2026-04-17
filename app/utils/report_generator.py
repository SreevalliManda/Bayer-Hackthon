def generate_report(decision):
    return f"""
# Incident Report

Root Cause:
{decision['root_cause']}

Recommended Action:
{decision['action']}

Confidence: {decision.get('confidence', 'N/A')}

Timeline:
10:00 → Deploy: DB config updated
10:14 → Log: DB connection timeout
10:15 → Metric: Latency spike (2000ms)
"""