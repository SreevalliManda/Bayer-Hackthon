def correlate(data):
    if data["metrics"]["anomaly"] and data["logs"]["db_timeout"]:
        return {"correlated": True}
    return {"correlated": False}