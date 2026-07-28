"""
auth.py — Authentication: passwords, MFA, and sessions.

This module makes the session identity trustworthy. Fix 01 made the tools trust
the session's patient_id; this module makes sure that patient_id came from a
verified login instead of being whatever the browser claimed.

Design (all self-contained, no external services):
  - Passwords are hashed with PBKDF2-HMAC-SHA256 + a per-user salt. We never
    store or compare plaintext passwords.
  - Login is two steps: password first, then a 6-digit MFA code. A session is
    issued ONLY after the code is verified.
  - Session tokens and MFA challenges are random, unguessable, and expire.

Delivery note: real code delivery (text/email) needs a paid Twilio/SendGrid
account. `deliver_mfa_code` currently prints the code to the server terminal and
marks the exact spot where a real send would go. The security logic is real; only
the last-mile delivery is stubbed.
"""

import hashlib
import hmac
import secrets
import time

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_PBKDF2_ROUNDS = 200_000


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """Return (hash_hex, salt_hex). Generates a salt if none is given."""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ROUNDS)
    return dk.hex(), salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """Constant-time check of a password against a stored hash."""
    candidate, _ = hash_password(password, salt)
    return hmac.compare_digest(candidate, stored_hash)


# ---------------------------------------------------------------------------
# MFA challenges  (login_token -> {patient_id, code, expires})
# ---------------------------------------------------------------------------

_MFA_TTL_SECONDS = 300  # code valid for 5 minutes
_mfa_challenges: dict[str, dict] = {}


def start_mfa_challenge(patient_id: int) -> tuple[str, str]:
    """
    Create a 6-digit code tied to a short-lived login_token. Returns
    (login_token, code). The caller delivers the code out-of-band; the token
    is what the client sends back with the code at verify time.
    """
    login_token = secrets.token_urlsafe(24)
    code = f"{secrets.randbelow(1_000_000):06d}"  # cryptographically-random 6 digits
    _mfa_challenges[login_token] = {
        "patient_id": patient_id,
        "code": code,
        "expires": time.time() + _MFA_TTL_SECONDS,
    }
    return login_token, code


def verify_mfa_code(login_token: str, code: str) -> int | None:
    """
    Check a submitted code. Returns the patient_id on success, else None.
    A challenge is single-use: it is removed whether it passes or expires.
    """
    challenge = _mfa_challenges.get(login_token)
    if not challenge:
        return None
    if time.time() > challenge["expires"]:
        _mfa_challenges.pop(login_token, None)
        return None
    ok = hmac.compare_digest(challenge["code"], code)
    if not ok:
        return None
    _mfa_challenges.pop(login_token, None)  # success: consume it
    return challenge["patient_id"]


# ---------------------------------------------------------------------------
# Sessions  (session_token -> {patient_id, expires})
# ---------------------------------------------------------------------------

_SESSION_TTL_SECONDS = 60 * 60  # 1 hour
_sessions: dict[str, dict] = {}


def create_session(patient_id: int) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = {"patient_id": patient_id, "expires": time.time() + _SESSION_TTL_SECONDS}
    return token


def get_session_patient_id(token: str | None) -> int | None:
    """
    The single source of truth for 'who is this request'. Returns the patient_id
    for a valid, unexpired token, else None. main.py calls this instead of ever
    trusting a patient_id from the request body.
    """
    if not token:
        return None
    sess = _sessions.get(token)
    if not sess:
        return None
    if time.time() > sess["expires"]:
        _sessions.pop(token, None)
        return None
    return sess["patient_id"]


def end_session(token: str | None) -> None:
    if token:
        _sessions.pop(token, None)


# ---------------------------------------------------------------------------
# MFA delivery — STUB
# ---------------------------------------------------------------------------

def mask_destination(value: str) -> str:
    """Turn 'jokafor78@email.com' into 'j*******@email.com' for safe display."""
    if "@" in value:
        local, domain = value.split("@", 1)
        shown = local[0] if local else ""
        return f"{shown}{'*' * max(len(local) - 1, 1)}@{domain}"
    # phone-like
    return f"{'*' * max(len(value) - 4, 0)}{value[-4:]}"


def deliver_mfa_code(code: str, email: str | None, phone: str | None) -> str:
    """
    Deliver the MFA code to the patient. Returns a masked destination hint for
    display. Real delivery is not wired up (needs paid Twilio/SendGrid + a BAA).

    >>> PRODUCTION: replace the print below with a real send, e.g.:
        sendgrid_client.send(to=email, subject="Your MediAssist code", body=code)
        # or twilio_client.messages.create(to=phone, from_=..., body=code)
    """
    destination = email or phone or "your registered contact"
    # DEV ONLY: surface the code so it can be tested without a delivery service.
    print(f"\n[MFA] Code for {mask_destination(destination)}: {code}  (dev only)\n", flush=True)
    return mask_destination(destination)
