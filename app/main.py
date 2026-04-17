from fastapi import FastAPI
from app.agents.commander import run_investigation
from app.services.correlation import correlate
from app.services.decision import decide
from app.utils.report_generator import generate_report

app = FastAPI()

@app.get("/incident")
def handle_incident():
    data = run_investigation()
    corr = correlate(data)
    decision = decide(data, corr)
    report = generate_report(decision)

    return {
        "data": data,
        "decision": decision,
        "report": report
    }