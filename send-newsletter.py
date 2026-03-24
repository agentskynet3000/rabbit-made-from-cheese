#!/usr/bin/env python3
"""Send hourly rabbit newsletter to all subscribers via Cloudflare KV + Gmail SMTP."""

import json
import os
import re
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")

# ── Config ────────────────────────────────────────────────────────────────────

CF_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
CF_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
KV_NAMESPACE_ID = "800d55419b2b4ea7806135b228bd4711"
KV_BASE = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/storage/kv/namespaces/{KV_NAMESPACE_ID}"

GMAIL_USER = "agent.skynet.3000@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
FROM_NAME = "Rabbit Made From Cheese"
FROM_EMAIL = "agent.skynet.3000@gmail.com"

SITE_URL = "https://rabbit-made-from-cheese.pages.dev"
OBSIDIAN_SUBSCRIBERS_FILE = "/home/marius-jopen/shared/obsidian/skynet/0200_projects/rabbit-made-from-cheese-subscribers.md"

def generate_caption(caption: str, number: int) -> str:
    """Generate a unique deadpan one-liner about this rabbit via Perplexity sonar."""
    try:
        prompt = (
            f"Write one short deadpan sentence about a rabbit made from cheese that is '{caption}'. "
            f"Dry absurdist humor, Lukas Arz style. Max 20 words. No quotes. No explanation."
        )
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"},
            json={"model": "sonar", "max_tokens": 60, "messages": [{"role": "user", "content": prompt}]},
            timeout=15,
        )
        resp.raise_for_status()
        text = resp.json()["choices"][0]["message"]["content"].strip()
        # Strip citation markers like [1][2]
        import re
        text = re.sub(r'\[\d+\]', '', text).strip()
        return text
    except Exception as e:
        print(f"Caption generation failed: {e}")
        return f"Rabbit #{number:03d} has arrived. It is made from cheese. This is not up for debate."

IMAGES_DIR = Path(__file__).parent / "images"


def get_latest_rabbit():
    """Return (filename, number, caption) of the most recent rabbit image."""
    images = sorted(IMAGES_DIR.glob("rabbit-*.jpg"), reverse=True)
    if not images:
        return None, None, None
    latest = images[0]
    match = re.match(r"rabbit-(\d+)-(.+)\.jpg", latest.name)
    if not match:
        return latest.name, 0, latest.stem
    number = int(match.group(1))
    caption = match.group(2).replace("-", " ")
    return latest.name, number, caption


def get_subscribers():
    """Fetch all subscribers from Cloudflare KV."""
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}"}
    # List all keys with prefix "sub:"
    resp = requests.get(f"{KV_BASE}/keys?prefix=sub%3A&limit=1000", headers=headers, timeout=30)
    if not resp.ok:
        print(f"KV list error: {resp.status_code} {resp.text}")
        return []

    keys = resp.json().get("result", [])
    subscribers = []
    for key_obj in keys:
        key = key_obj["name"]
        val_resp = requests.get(f"{KV_BASE}/values/{requests.utils.quote(key, safe='')}", headers=headers, timeout=10)
        if val_resp.ok:
            try:
                sub = json.loads(val_resp.text)
                subscribers.append(sub)
            except Exception:
                pass
    return subscribers


def build_email_html(rabbit_filename, rabbit_number, caption, token, ai_caption):
    image_url = f"{SITE_URL}/images/{rabbit_filename}" if not rabbit_filename.startswith("images/") else f"{SITE_URL}/{rabbit_filename}"
    unsub_url = f"{SITE_URL}/unsubscribe?token={token}"

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ margin: 0; padding: 0; background: #FFB7C5; font-family: 'Courier New', monospace; }}
    .wrap {{ max-width: 600px; margin: 0 auto; background: #FFB7C5; padding: 32px 24px; }}
    .header {{ text-align: center; margin-bottom: 24px; background: #2D1B2E; padding: 24px 16px; }}
    .title {{ font-size: 24px; font-weight: 900; color: #ffffff; letter-spacing: 3px; line-height: 1.5; text-shadow: none; }}
    .badge {{ display: inline-block; background: #F5C518; color: #2D1B2E; font-size: 11px; font-weight: bold; padding: 5px 14px; margin-top: 10px; letter-spacing: 2px; }}
    .img-wrap {{ text-align: center; margin: 24px 0 0; }}
    .img-wrap img {{ max-width: 100%; border: 4px solid #2D1B2E; box-shadow: 6px 6px 0 #2D1B2E; display: block; }}
    .ai-caption {{ background: #2D1B2E; color: #FFB7C5; font-size: 13px; font-style: italic; line-height: 1.8; padding: 16px 20px; text-align: center; margin-bottom: 8px; }}
    .caption {{ text-align: center; font-size: 11px; color: #a07080; font-weight: bold; letter-spacing: 1px; margin: 8px 0 4px; text-transform: uppercase; }}
    .rabbit-num {{ text-align: center; font-size: 11px; color: #a07080; margin-bottom: 24px; }}
    .cta {{ text-align: center; margin: 24px 0; }}
    .cta a {{ background: #2D1B2E; color: #F5C518; padding: 12px 28px; text-decoration: none; font-size: 12px; font-weight: bold; letter-spacing: 2px; display: inline-block; }}
    .footer {{ text-align: center; font-size: 10px; color: #a07080; margin-top: 32px; line-height: 2; }}
    .unsub {{ color: #a07080; text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div class="title">RABBIT MADE<br>FROM CHEESE</div>
      <div class="badge">HOURLY DROP #{rabbit_number:03d}</div>
    </div>

    <div class="img-wrap">
      <img src="{image_url}" alt="rabbit made from cheese #{rabbit_number:03d}">
    </div>
    <div class="ai-caption">{ai_caption}</div>
    <div class="caption">{caption}</div>
    <div class="rabbit-num">Rabbit #{rabbit_number:03d}</div>

    <div class="cta">
      <a href="{SITE_URL}">VIEW ALL RABBITS →</a>
    </div>

    <div class="footer">
      You subscribed to hourly rabbits made from cheese.<br>
      This will continue indefinitely.<br><br>
      <a class="unsub" href="{unsub_url}">unsubscribe</a> · if you must.
    </div>
  </div>
</body>
</html>"""


def send_email(to_email, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email

    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.sendmail(FROM_EMAIL, to_email, msg.as_string())


def update_obsidian(subscribers):
    """Mirror subscriber list to Obsidian."""
    lines = ["# Rabbit Made From Cheese — Subscribers", ""]
    lines.append(f"**Total:** {len(subscribers)}")
    lines.append("")
    lines.append("| Email | Subscribed |")
    lines.append("|-------|------------|")
    for sub in sorted(subscribers, key=lambda x: x.get("subscribedAt", "")):
        email = sub.get("email", "?")
        date = sub.get("subscribedAt", "?")[:10]
        lines.append(f"| {email} | {date} |")
    lines.append("")
    lines.append(f"*Last updated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}*")

    Path(OBSIDIAN_SUBSCRIBERS_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(OBSIDIAN_SUBSCRIBERS_FILE).write_text("\n".join(lines))
    print(f"Obsidian updated: {OBSIDIAN_SUBSCRIBERS_FILE}")


def main():
    filename, number, caption = get_latest_rabbit()
    if not filename:
        print("No rabbit images found.")
        sys.exit(1)

    print(f"Latest rabbit: #{number:03d} — {caption}")

    subscribers = get_subscribers()
    print(f"Subscribers: {len(subscribers)}")

    if not subscribers:
        print("No subscribers yet. Skipping email send.")
        update_obsidian([])
        return

    subject = f"🐰 Rabbit #{number:03d} has arrived — {caption}"

    # Generate one AI caption for all subscribers (one API call total)
    print("Generating AI caption...")
    ai_caption = generate_caption(caption, number)
    print(f"Caption: {ai_caption}")

    sent = 0
    for sub in subscribers:
        email = sub.get("email")
        token = sub.get("token")
        if not email or not token:
            continue
        html = build_email_html(filename, number, caption, token, ai_caption)
        try:
            send_email(email, subject, html)
            print(f"Sent to {email}")
            sent += 1
        except Exception as e:
            print(f"Failed to send to {email}: {e}")

    print(f"Newsletter sent: {sent}/{len(subscribers)}")
    update_obsidian(subscribers)


if __name__ == "__main__":
    main()
