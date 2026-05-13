#!/usr/bin/env python3
"""
Get Telegram chat ID
Run after sending message to your bot
"""
import requests
import sys

# Paste your token here
TOKEN = "7735176818:AAGy8hyKORzR8-wR5-QV6TZZQ28aFBvelAs"

def get_chat_id():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get('ok'):
            print(f"❌ Error: {data}")
            return

        if not data.get('result'):
            print("❌ No messages found. Send a message to your bot first!")
            return

        # Get latest chat
        latest = data['result'][-1]
        chat_id = latest['message']['chat']['id']
        username = latest['message']['chat'].get('username', 'N/A')
        first_name = latest['message']['chat'].get('first_name', 'N/A')

        print("✅ Found chat!")
        print(f"Chat ID: {chat_id}")
        print(f"Name: {first_name}")
        print(f"Username: @{username}")
        print(f"\nUse this in GitHub secret: {chat_id}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nCheck:")
        print("1. Token correct? (get from @BotFather)")
        print("2. Sent message to bot? (required before getUpdates works)")

if __name__ == "__main__":
    if TOKEN == "YOUR_TOKEN_HERE":
        print("❌ Edit script and paste your token first!")
        sys.exit(1)

    get_chat_id()
