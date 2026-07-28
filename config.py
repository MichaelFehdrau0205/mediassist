import os
from dotenv import load_dotenv

load_dotenv()

# All secrets are loaded from the environment (.env locally, real env vars in
# deployment). No secret is hardcoded here — a value committed to source is a
# leaked value. See .env.example for the variables this file expects.

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# SendGrid — patient appointment reminder emails
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

# Twilio — SMS notifications
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

# Legacy records system connection string
LEGACY_DB_URL = os.getenv("LEGACY_DB_URL")

# Insurance verification API
INSURANCE_VERIFY_API_KEY = os.getenv("INSURANCE_VERIFY_KEY")
