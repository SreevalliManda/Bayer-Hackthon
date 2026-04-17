import json

def analyze_deploy():
    with open("app/data/deploy.json") as f:
        deploy = json.load(f)

    return {"recent_change": True, "change": deploy["change"]}