"""
guards.py — Content guards for untrusted text that enters the model's context.

Right now this screens notes before they are written to persistent memory
(Finding 7 — memory poisoning). The same approach will be extended to retrieved
knowledge-base documents next (Finding 2 — RAG poisoning).

Two ideas here:
  1. SCREEN on write: reject notes that look like instructions or claims of
     permission/identity before they ever reach the memory store.
  2. (in agent.build_system_prompt) LABEL on read: when memory is placed back
     into the system prompt, mark it clearly as patient-provided data, not
     instructions.

Why screening is worthwhile here (unlike filtering live chat, which is weak):
memory notes should be short, factual preferences ("prefers morning
appointments"). Anything that reads like a command or an authorization claim has
no legitimate place in memory, so a tripwire on those shapes is a good fit. It is
still backed up by Fix 01 — even a poisoned note claiming "admin access" cannot
reach another patient's data, because the tools are session-scoped.
"""

import re

_MAX_MEMORY_CHARS = 500  # a note longer than this is suspicious (context stuffing)

# Notes that assert permissions/identity, or that read like instructions, are
# refused. These have no legitimate place in a patient preference note.
_BLOCKED_PATTERNS = [
    r"\b(admin|administrator|root|superuser)\b",
    r"\bfull\s+(record\s+)?access\b",
    r"\ball\s+(patient\s+)?records\b",
    r"\b(verified\s+)?(staff|provider|physician|doctor|nurse)\b",
    r"\b(permission|authoriz|privilege|clearance|access\s+level)\w*",
    r"\bignore\s+(all\s+)?(previous|prior|above)\b",
    r"\byou\s+are\s+now\b",
    r"\bsystem\s*:",
    r"\bsend\s+.*\s+to\s+\S+@\S+",
    r"https?://\S+\?\S*=",  # url with query params — possible exfil
]
_COMPILED = [re.compile(p, re.IGNORECASE) for p in _BLOCKED_PATTERNS]


def screen_memory_note(note: str) -> tuple[bool, str]:
    """
    Decide whether a note may be written to persistent memory.
    Returns (ok, reason). ok=False means refuse to store it.
    """
    if not note or not note.strip():
        return False, "empty note."
    if len(note) > _MAX_MEMORY_CHARS:
        return False, f"note too long (>{_MAX_MEMORY_CHARS} characters)."
    for pattern in _COMPILED:
        if pattern.search(note):
            return False, "note contains permission claims or instruction-like content."
    return True, "ok"
