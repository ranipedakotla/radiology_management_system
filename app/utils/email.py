import os
import smtplib
import ssl
import time
import traceback
from email.message import EmailMessage
from typing import Optional

# -------------------------------
#  SES SMTP CONFIG
# -------------------------------
SES_HOST = "email-smtp.us-east-1.amazonaws.com"
SES_PORT = 587

# ⚠️ WARNING: These should be stored in .env in real production
SES_USER = "AKIARHO7G764MQCG5SPT"
SES_PASS = "BMDzASRslP8NP1p1NveSUOJMEdPzmCrwZ04/ZvBX9A/w"

EMAIL_FROM = "careers@securxperts.com"
EMAIL_FROM_NAME = "SecurXperts"


def _smtp_config():
    """Returns validated SES configuration."""
    if not SES_USER or not SES_PASS:
        raise RuntimeError("SES SMTP credentials missing")

    return SES_HOST, SES_PORT, SES_USER, SES_PASS, EMAIL_FROM, EMAIL_FROM_NAME


# --------------------------------------------------------
# INTERNAL: LOW-LEVEL SMTP SENDING FUNCTION
# --------------------------------------------------------
def _send_via_smtp(to_email: str, subject: str, text: str, html: Optional[str]):
    host, port, user, pwd, sender, sender_name = _smtp_config()

    msg = EmailMessage()
    msg["From"] = f"{sender_name} <{sender}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    # Text & HTML versions
    if html:
        msg.set_content(text or "")
        msg.add_alternative(html, subtype="html")
    else:
        msg.set_content(text or "")

    context = ssl.create_default_context()

    with smtplib.SMTP(host, port, timeout=30) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(user, pwd)
        server.send_message(msg)


# --------------------------------------------------------
# PUBLIC: SEND EMAIL + RETRY LOGIC
# --------------------------------------------------------
def send_email(
        to_email: str,
        subject: str,
        text: str,
        html: Optional[str] = None,
        retries: int = 2,
        backoff_sec: float = 1.5,
) -> bool:
    """
    Sends an email using Amazon SES.
    Returns True or False.
    Includes exponential backoff retry strategy.
    """

    last_error = None

    for attempt in range(retries + 1):
        try:
            _send_via_smtp(to_email, subject, text, html)
            print(f"[EMAIL SUCCESS] to={to_email} subject={subject}")
            return True

        except Exception as e:
            last_error = e
            print(f"[EMAIL RETRY {attempt}] Error: {e}")
            traceback.print_exc()

            if attempt < retries:
                time.sleep(backoff_sec * (attempt + 1))

    print(f"[EMAIL FAILED] to={to_email}, subject={subject} error={last_error}")
    return False


def send_email_with_attachment(
        to_email: str,
        subject: str,
        text: str,
        pdf_bytes: bytes,
        filename: str,
        html: Optional[str] = None,
        retries: int = 2,
        backoff_sec: float = 1.5,
) -> bool:
    """
    Sends email with PDF attachment using Amazon SES SMTP
    """

    last_error = None

    for attempt in range(retries + 1):
        try:
            host, port, user, pwd, sender, sender_name = _smtp_config()

            msg = EmailMessage()
            msg["From"] = f"{sender_name} <{sender}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            if html:
                msg.set_content(text or "")
                msg.add_alternative(html, subtype="html")
            else:
                msg.set_content(text or "")

            #  ATTACH PDF
            msg.add_attachment(
                pdf_bytes,
                maintype="application",
                subtype="pdf",
                filename=filename
            )

            context = ssl.create_default_context()

            with smtplib.SMTP(host, port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(user, pwd)
                server.send_message(msg)

            print(f"[EMAIL SUCCESS] Payslip sent to {to_email}")
            return True



        except Exception as e:
            last_error = e
            print(f"[EMAIL RETRY {attempt}] Error: {e}")
            traceback.print_exc()

            if attempt < retries:
                time.sleep(backoff_sec * (attempt + 1))

    print(f"[EMAIL FAILED] to={to_email} error={last_error}")
    return False



