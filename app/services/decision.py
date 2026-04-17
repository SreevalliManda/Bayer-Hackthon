def decide(data, correlation):
    if correlation["correlated"] and data["deploy"]["recent_change"]:
        return {
            "root_cause": "Recent DB configuration change",
            "action": "Rollback deployment",
            "confidence": "95%"
        }

    return {"root_cause": "Unknown", "confidence": "50%"}