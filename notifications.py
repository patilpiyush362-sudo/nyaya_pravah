import os
import smtplib
from pathlib import Path
from email.message import EmailMessage
from dotenv import load_dotenv

# Explicitly load .env from the same folder as this file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SENDER_EMAIL = os.getenv("MAIL_SENDER")
APP_PASSWORD = os.getenv("MAIL_PASSWORD")

def send_hearing_alert(to_email, case_id, case_title, next_date, is_rollover=False):
    """Sends an official judicial update email to the citizen."""
    if not to_email:
        print(f"[MAIL SKIP] No email provided for Case {case_id}")
        return False

    if not SENDER_EMAIL or not APP_PASSWORD:
        print("[MAIL ERROR] Missing MAIL_SENDER or MAIL_PASSWORD in .env")
        return False

    msg = EmailMessage()
    msg["From"] = f"Nyaya Pravah Registry <{SENDER_EMAIL}>"
    msg["To"] = to_email

    if is_rollover:
        msg["Subject"] = f"PRIORITY ALERT: Hearing Rescheduled - Case {case_id}"
        body = (
            f"Official Judicial Notice\n"
            f"Portal: Nyaya Pravah e-Courts\n"
            f"--------------------------------------------------\n\n"
            f"Dear Litigant,\n\n"
            f"Regarding your case: {case_title} ({case_id})\n\n"
            f"Due to the exhaustion of today's court board capacity limit, your matter could not be heard today.\n\n"
            f"Under the Nyaya Pravah Procedural Fairness Rule, your case has been assigned BUMPED ROLLOVER PRIORITY for the next session.\n\n"
            f"Next Scheduled Hearing Date: {next_date}\n\n"
            f"Please inform your counsel/advocate accordingly.\n\n"
            f"Regards,\n"
            f"Registrar, Judicial Proceedings\n"
            f"Nyaya Pravah Portal"
        )
    else:
        msg["Subject"] = f"Case Registration Notice: {case_id}"
        body = (
            f"Dear Litigant,\n\n"
            f"Your case '{case_title}' has been officially registered in the Nyaya Pravah system.\n"
            f"Tracking ID: {case_id}\n"
            f"Next Hearing Date: {next_date}\n\n"
            f"You can track real-time progression directly via the portal using your Tracking ID.\n\n"
            f"Regards,\n"
            f"Nyaya Pravah Registry"
        )

    msg.set_content(body)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        print(f"[MAIL SUCCESS] Real notification sent to {to_email} for Case {case_id}")
        return True
    except Exception as e:
        print(f"[MAIL FAILED] Error sending email to {to_email}: {e}")
        return False