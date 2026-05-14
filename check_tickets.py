#!/usr/bin/env python3
"""
Monitor organized play event tickets
Checks if 'Sold out' changes to available
Sends Telegram notification
Uses GitHub Gist for dynamic event config
"""
import requests
import sys
import os
from datetime import datetime
from config_manager import get_config_manager

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

def check_event(event: dict) -> bool:
    """Check if any ticket available for single event"""
    url = event['url']
    tickets = event['tickets']
    name = event['name']

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html = response.text

        available = []
        for ticket in tickets:
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
                f"🎟️ <b>TICKETS DISPONIBLES: {name}</b>\n\n"
                + "\n".join([f"✅ {t}" for t in available])
                + f"\n\n🔗 <a href='{url}'>COMPRAR AHORA</a>"
            )
            print(f"🎉 [{name}] TICKETS AVAILABLE: {', '.join(available)}")
            print(f"🔗 {url}")
            send_telegram(message)
            return True
        else:
            print(f"❌ [{name}] All sold out - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return False

    except Exception as e:
        print(f"⚠️ [{name}] Error checking: {e}")
        return False


def check_all_events():
    """Check all configured events"""
    config_mgr = get_config_manager()

    if not config_mgr:
        print("⚠️ Config manager not available, exiting")
        return False

    events = config_mgr.get_events()

    if not events:
        print("⚠️ No events configured")
        return False

    print(f"📋 Checking {len(events)} event(s)...")

    found_any = False
    for event in events:
        if check_event(event):
            found_any = True

    return found_any

if __name__ == "__main__":
    found = check_all_events()
    # Always exit 0 to avoid "failed" status
    # Telegram notification only sent when available
    sys.exit(0)
