import json
import logging
import os
import time
import uuid

from fastapi import FastAPI, Request, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

import database
import auth
from agent import run_agent

app = FastAPI(title="MediAssist")


def _session_from_header(authorization: Optional[str]) -> Optional[int]:
    """Extract the patient_id from a 'Bearer <token>' Authorization header.
    Returns None if the header is missing or the token is invalid/expired."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    return auth.get_session_patient_id(token)

# Logging setup
os.makedirs("logs", exist_ok=True)
log_handler = logging.FileHandler("logs/requests.log")
log_handler.setFormatter(logging.Formatter("%(message)s"))
request_logger = logging.getLogger("mediassist.requests")
request_logger.addHandler(log_handler)
request_logger.setLevel(logging.INFO)


class LoginRequest(BaseModel):
    username: str
    password: str


class MfaRequest(BaseModel):
    login_token: str
    code: str


class ChatRequest(BaseModel):
    # NOTE: no patient_id here. Identity comes from the session token in the
    # Authorization header, never from the request body.
    message: str
    conversation_history: list = []


@app.on_event("startup")
def startup():
    database.init_db()


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


def _normalize_username(username: str) -> str:
    """Accept email or local-part; ignore surrounding whitespace and case."""
    username = username.strip().lower()
    if "@" in username:
        username = username.split("@", 1)[0]
    return username


@app.post("/login")
def login(req: LoginRequest):
    """Step 1: verify username + password. On success, start an MFA challenge
    and 'send' a 6-digit code. Does NOT return a session yet."""
    username = _normalize_username(req.username)
    password = req.password.strip()
    user = database.get_user_by_username(username)
    # Verify even on unknown users would leak timing; keep it simple but generic.
    if not user or not auth.verify_password(password, user["password_hash"], user["salt"]):
        return JSONResponse(status_code=401, content={"error": "Invalid username or password."})

    patient = database.get_patient(user["patient_id"])
    login_token, code = auth.start_mfa_challenge(user["patient_id"])
    destination = auth.deliver_mfa_code(code, patient.get("email"), patient.get("phone"))
    response = {"login_token": login_token, "mfa_sent_to": destination}
    if auth.is_dev_mode():
        response["dev_mfa_code"] = code
        response["dev_mfa_hint"] = (
            "Dev mode: email/SMS delivery is disabled. "
            "Use the code below, or check the terminal running python main.py."
        )
    return response


@app.post("/verify-mfa")
def verify_mfa(req: MfaRequest):
    """Step 2: verify the 6-digit code. Only now is a session token issued."""
    patient_id = auth.verify_mfa_code(req.login_token, req.code)
    if patient_id is None:
        return JSONResponse(status_code=401, content={"error": "Invalid or expired code."})
    session_token = auth.create_session(patient_id)
    summary = database.get_patient_summary(patient_id)
    return {"session_token": session_token, "patient_name": summary["name"]}


@app.get("/me")
def me(authorization: Optional[str] = Header(default=None)):
    """Return the logged-in patient's own summary, derived from the session."""
    patient_id = _session_from_header(authorization)
    if patient_id is None:
        return JSONResponse(status_code=401, content={"error": "Not authenticated."})
    return database.get_patient_summary(patient_id)


@app.post("/logout")
def logout(authorization: Optional[str] = Header(default=None)):
    if authorization and authorization.lower().startswith("bearer "):
        auth.end_session(authorization.split(" ", 1)[1].strip())
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest, authorization: Optional[str] = Header(default=None)):
    patient_id = _session_from_header(authorization)
    if patient_id is None:
        return JSONResponse(status_code=401, content={"error": "Not authenticated."})

    request_id = uuid.uuid4().hex[:8]
    start_time = time.time()

    response_text, tool_calls = run_agent(
        patient_id,
        req.message,
        req.conversation_history
    )

    duration_ms = int((time.time() - start_time) * 1000)

    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
        "request_id": request_id,
        "patient_id": patient_id,
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
def reset_memory(authorization: Optional[str] = Header(default=None)):
    patient_id = _session_from_header(authorization)
    if patient_id is None:
        return JSONResponse(status_code=401, content={"error": "Not authenticated."})
    database.clear_memory(patient_id)
    return {"status": "ok", "message": "Session memory cleared."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)
