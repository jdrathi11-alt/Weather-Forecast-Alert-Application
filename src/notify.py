"""
notify.py - OPTIONAL email alerts via standard-library smtplib.

This module demonstrates the "automation" angle of the project: when a
CRITICAL/WARNING alert fires, an email can be sent automatically.

SECURITY
--------
* Credentials are read from environment variables / .env file ONLY.
  Never hard-code them. .env is in .gitignore, so it never reaches GitHub.
* Gmail: you need an "App Password" (not your normal password):
  https://myaccount.google.com/security -> App passwords

.env example (see .env.example):
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=your.email@gmail.com
    SMTP_PASS=xxxxxxxxxxxxxxx
    ALERT_RECIPIENT=recipient@example.com

Usage from main.py is automatic when --email flag is set and SMTP vars exist.
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Iterable


def _smtp_config() -> dict | None:
    """Return SMTP settings if fully configured, else None."""
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")
    recipient = os.environ.get("ALERT_RECIPIENT")
    if not all([host, user, password, recipient]):
        return None
    return {
        "host": host,
        "port": int(os.environ.get("SMTP_PORT", "587")),
        "user": user,
        "password": password,
        "recipient": recipient,
    }


def build_email(city: str, alerts: Iterable[dict], source: str) -> tuple[str, str]:
    """Compose subject + body from the alert list."""
    alert_list = list(alerts)
    subject = f"[WEATHER ALERT] {city}: {len(alert_list)} active alert(s)"
    lines = [
        f"Weather Forecast & Alert Application",
        f"City: {city}",
        f"Source: {source} mode",
        f"Alerts: {len(alert_list)}",
        "-" * 50,
    ]
    for a in alert_list:
        lines.append(f"[{a['level']}] {a['title']} ({a['time']})")
        lines.append(f"    {a['message']}")
        lines.append("")
    lines.append("Generated automatically by the Weather Forecast & Alert App.")
    return subject, "\n".join(lines)


def send_email(subject: str, body: str) -> str:
    """
    Send the email. Returns a status string.
    Never raises - email failure must not crash the weather run.
    """
    cfg = _smtp_config()
    if cfg is None:
        return "SKIPPED - SMTP not configured (set SMTP_HOST/SMTP_USER/SMTP_PASS/ALERT_RECIPIENT in .env)"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["user"]
    msg["To"] = cfg["recipient"]
    msg.set_content(body)

    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=15) as server:
            server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.send_message(msg)
        return f"SENT to {cfg['recipient']}"
    except Exception as exc:                                    # noqa: BLE001
        return f"FAILED - {exc}"


def notify_if_needed(city: str, alerts: list[dict], source: str,
                     force: bool = False) -> str:
    """
        Send email only when CRITICAL/WARNING alerts exist (or force=True).
        Returns a human-readable status line for the console.
    """
    if not force and not any(a["level"] in ("CRITICAL", "WARNING") for a in alerts):
        return "No CRITICAL/WARNING alerts - email skipped"
    subject, body = build_email(city, alerts, source)
    status = send_email(body=body, subject=subject)
    return status
