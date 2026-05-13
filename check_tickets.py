#!/usr/bin/env python3
"""
Monitor One Piece Treasure Cup tickets
Checks if 'Sold out' changes to available
Sends Telegram notification
"""
import requests
import sys
import os
from datetime import datetime

URL = "https://tickets.organizedplay.events/Event/Index?id=165"
TICKETS = [
    "One Piece Treasure Cup Ticket - Friday 10:00AM",
    "One Piece Treasure Cup Ticket - Saturday 10:00AM",
    "One Piece Treasure Cup Ticket - Sunday 09:00AM"
]

def send_telegram(message):
    """Send Telegram notification"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("⚠️ Telegram credentials not set")
        return False

    try:
        telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False
        }
        response = requests.post(telegram_url, json=data, timeout=10)
        response.raise_for_status()
        print("✅ Telegram notification sent")
        return True
    except Exception as e:
        print(f"⚠️ Error sending Telegram: {e}")
        return False

def check_availability():
    """Check if any ticket available"""
    try:
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        html = response.text

        available = []
        for ticket in TICKETS:
            # Check if ticket section contains 'Sold out'
            if ticket in html:
                # Find ticket section
                start = html.find(ticket)
                # Get next 500 chars after ticket name
                section = html[start:start+500]

                # If 'Sold out' NOT in section = available!
                if 'Sold out' not in section and 'Available' in section:
                    available.append(ticket)

        if available:
            message = (
                "🎟️ <b>TICKETS DISPONIBLES!</b>\n\n"
                + "\n".join([f"✅ {t}" for t in available])
                + f"\n\n🔗 <a href='{URL}'>COMPRAR AHORA</a>"
            )
            print(f"🎉 TICKETS AVAILABLE: {', '.join(available)}")
            print(f"🔗 {URL}")
            send_telegram(message)
            return True
        else:
            print(f"❌ All sold out - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return False

    except Exception as e:
        print(f"⚠️ Error checking: {e}")
        return False

if __name__ == "__main__":
    found = check_availability()
    sys.exit(0 if found else 1)
