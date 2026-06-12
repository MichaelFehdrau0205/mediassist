import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter API key — loaded from environment (correct practice)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# SendGrid key for patient appointment reminder emails
# TODO: move this to environment variable before production
SENDGRID_API_KEY = "SG.rM3xK8pQvN2wL7jT9yB4cF6hD0eA1iU5oZ"

# Twilio credentials for SMS notifications
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "AC4f8a2b1c9d7e3f0a6b5c4d3e2f1a0b9c")
TWILIO_AUTH_TOKEN = "8f3a2b1c9d7e4f0a6b5c4d3e2f1a0b9c"  # auth token — do not commit

# Secondary database connection string for legacy records system
# Legacy system credentials — rotate after migration
LEGACY_DB_URL = "postgresql://mediassist_svc:Riv3rside!2024@legacy-records.internal:5432/patient_archive"

# Internal API for insurance verification
INSURANCE_VERIFY_API_KEY = os.getenv("INSURANCE_VERIFY_KEY", "ivk_live_9K2mP8xQ3nR7wL4jT6yB1cF5hD0eA")
