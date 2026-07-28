# MediAssist

MediAssist is a mock AI-powered healthcare triage chatbot for a fictional clinic called Riverside Medical Center. Patients log in with their patient ID and can chat with an AI assistant to:

- Describe symptoms and receive triage guidance
- Review their medical history, medications, and allergies
- Book appointments and request specialist referrals
- Ask questions about their care

The system is built with a Python/FastAPI backend, a Claude-compatible LLM via OpenRouter, a SQLite patient database, and a simple browser-based chat UI. It includes 10 pre-loaded fictional patients, a clinical knowledge base, and structured request logging.

This is a practice target system used in AI cybersecurity curriculum for red team exercises. Builders use it to learn how to probe, test, and evaluate the security of AI agent systems.

**Disclaimer:** This is not a real healthcare product. It is not affiliated with any organization, company, or medical institution. All patient data, names, records, and credentials in this system are entirely fictional and randomly generated. Do not use this system for any real medical purpose.

---

## Security Hardening (this fork)

This is a **hardened fork** of the MediAssist practice target. Starting from a red team of
the original, all eight identified findings were remediated. Summary:

| # | Finding | Fix |
|---|---|---|
| 1 | Prompt-injection role escalation | Session-scoped tools + system-prompt backdoor removed |
| 2 | RAG poisoning (knowledge base) | Poisoned documents quarantined at load; content labeled reference-only |
| 3 | Cross-patient PHI disclosure | Tools derive identity from the session, never from the model |
| 4 | No authentication | Password login + 6-digit MFA; identity from a session token |
| 5 | Unsafe advice / no output review | Output filter (PHI + prompt-leak net) + safety rules in the prompt |
| 6 | Tool misuse + SQL injection | Session-scoped writes + allow-listed update fields |
| 7 | Memory poisoning | Notes screened on write, labeled untrusted on read |
| 8 | Hardcoded secrets | All secrets moved to environment variables |

The design principle throughout: **the model never decides whose data it touches — the
tools derive identity from a verified session.** Even a fully successful prompt injection
cannot reach another patient's data. Full write-ups, with before/after evidence, are in the
companion repo (`mediassist-protection`).

**Known limitations (not production-ready):** no login rate-limiting/lockout, sessions are
in-memory (reset on restart), and MFA delivery is stubbed to the server console (a real
send needs a paid Twilio/SendGrid account). These are the gap between a hardened demo and a
deployable product.

---

## Getting Started

### 1. Fork and Clone

1. Click the **Fork** button at the top right of this repo to create your own copy.
2. Clone your fork:

```bash
git clone https://github.com/<your-username>/mediassist.git
cd mediassist
```

### 2. Set Up a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get an OpenRouter API Key (Free)

1. Go to [openrouter.ai](https://openrouter.ai) and create a free account.
2. Go to [openrouter.ai/keys](https://openrouter.ai/keys) and generate an API key.
3. Create your `.env` file:

```bash
cp .env.example .env
```

4. Open `.env` and paste your key:

```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 5. Run the App

```bash
python main.py
```

Open **http://localhost:8000** in your browser.

### 6. Sign In (username + password + MFA)

Log in with a username and password, then a 6-digit code. Username = the email local-part;
password = `MediPass<id>!`.

| ID | Name | Username | Password |
|----|------|----------|----------|
| 1 | Margaret Chen | `mchen1965` | `MediPass1!` |
| 2 | James Okafor | `jokafor78` | `MediPass2!` |
| 3 | Sofia Ramirez | `sramirez92` | `MediPass3!` |
| … | … | (email before @) | `MediPass<id>!` |

After the password step, the **6-digit MFA code is printed in the terminal** running the app
(`[MFA] Code for m********@email.com: 123456`). In production this would be texted or emailed;
for this demo it prints to the console. Enter the code to reach the chat.

---

## Seed Log Data

To populate historical log data for observability exercises:

```bash
python seed_logs.py
```

This generates 80 log entries in `logs/requests.log`.

---

## Resetting

- Click **Reset Memory** in the chat header to clear saved session notes for the current patient.
- Refreshing the page clears the conversation, but session memory persists until explicitly reset.
- To fully reset the database:

```bash
rm data/patients.db && python main.py
```

---

## Requirements

- Python 3.11+
- A free [OpenRouter](https://openrouter.ai) API key
