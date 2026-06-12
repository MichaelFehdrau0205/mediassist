# MediAssist

A mock healthcare triage chatbot built for educational purposes. This is a practice target system for AI security exercises.

**Disclaimer:** This is not a real healthcare product. It is not affiliated with any organization, company, or medical institution. All patient data, names, records, and credentials in this system are entirely fictional and randomly generated. Do not use this system for any real medical purpose.

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

### 6. Sign In

Enter any patient ID from **1 through 10** on the login screen. No password required.

| ID | Name |
|----|------|
| 1 | Margaret |
| 2 | James |
| 3 | Sofia |
| 4 | Robert |
| 5 | Priya |
| 6 | David |
| 7 | Amara |
| 8 | Carlos |
| 9 | Lisa |
| 10 | Thomas |

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
