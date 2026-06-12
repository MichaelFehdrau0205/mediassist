import json
import logging
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

import database
from agent import run_agent

app = FastAPI(title="MediAssist")

# Logging setup
os.makedirs("logs", exist_ok=True)
log_handler = logging.FileHandler("logs/requests.log")
log_handler.setFormatter(logging.Formatter("%(message)s"))
request_logger = logging.getLogger("mediassist.requests")
request_logger.addHandler(log_handler)
request_logger.setLevel(logging.INFO)


class ChatRequest(BaseModel):
    patient_id: int
    message: str
    conversation_history: list = []


class ResetRequest(BaseModel):
    patient_id: int


@app.on_event("startup")
def startup():
    database.init_db()


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


@app.get("/patient/{patient_id}")
def get_patient(patient_id: int):
    summary = database.get_patient_summary(patient_id)
    if not summary:
        return JSONResponse(status_code=404, content={"error": "Patient not found"})
    return summary


@app.post("/chat")
def chat(req: ChatRequest):
    request_id = uuid.uuid4().hex[:8]
    start_time = time.time()

    response_text, tool_calls = run_agent(
        req.patient_id,
        req.message,
        req.conversation_history
    )

    duration_ms = int((time.time() - start_time) * 1000)

    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
        "request_id": request_id,
        "patient_id": req.patient_id,
        "user_message": req.message,
        "tool_calls": tool_calls,
        "response_summary": response_text[:100],
        "response_length_chars": len(response_text),
        "tool_call_count": len(tool_calls),
        "duration_ms": duration_ms,
    }
    request_logger.info(json.dumps(log_entry))

    return {
        "response": response_text,
        "tool_calls": [tc["tool_name"] for tc in tool_calls],
        "request_id": request_id,
    }


@app.post("/reset")
def reset_memory(req: ResetRequest):
    database.clear_memory(req.patient_id)
    return {"status": "ok", "message": f"Session memory cleared for patient {req.patient_id}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)
