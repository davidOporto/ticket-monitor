#!/usr/bin/env python3
"""
Combined Flask API + Telegram Bot (webhook mode)
Webhook compatible with gunicorn workers
"""
import os
import asyncio
from flask import Flask, jsonify, request
from datetime import datetime
from check_tickets import check_all_events

# Import bot components
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from bot import (
    start, add_event_start, add_event_url, add_event_name, add_event_tickets,
    list_events, remove_event, toggle_event, cancel,
    WAITING_URL, WAITING_NAME, WAITING_TICKETS
)

# Flask app
app = Flask(__name__)

# Bot application (global)
bot_app = None


def setup_bot():
    """Setup bot application with handlers"""
    global bot_app

    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN not set - bot disabled")
        return None

    # Create application
    bot_app = Application.builder().token(token).build()

    # Add conversation handler for /add_event
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add_event', add_event_start)],
        states={
            WAITING_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_url)],
            WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_name)],
            WAITING_TICKETS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_event_tickets)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    bot_app.add_handler(conv_handler)
    bot_app.add_handler(CommandHandler('start', start))
    bot_app.add_handler(CommandHandler('list_events', list_events))
    bot_app.add_handler(CommandHandler('remove_event', remove_event))
    bot_app.add_handler(CommandHandler('toggle_event', toggle_event))

    print("🤖 Bot configured (webhook mode)")
    return bot_app


# Initialize bot on import
setup_bot()


@app.route('/')
def index():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'ticket-monitor',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/check')
def check():
    """Run ticket check - called by cron-job.org"""
    try:
        print(f"🔔 Check triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        found = check_all_events()

        return jsonify({
            'status': 'success',
            'tickets_found': found,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f"⚠️ Error in /check: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'healthy'})


@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    if not bot_app:
        return jsonify({'error': 'Bot not configured'}), 500

    try:
        # Get update from Telegram
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, bot_app.bot)

        # Process update
        asyncio.run(bot_app.process_update(update))

        return jsonify({'ok': True})

    except Exception as e:
        print(f"⚠️ Webhook error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/setup_webhook', methods=['GET'])
def setup_webhook():
    """Setup Telegram webhook (call once after deploy)"""
    if not bot_app:
        return jsonify({'error': 'Bot not configured'}), 500

    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    webhook_url = os.environ.get('WEBHOOK_URL', 'https://ticket-monitor-gxdi.onrender.com/webhook')

    try:
        import requests
        telegram_api = f"https://api.telegram.org/bot{token}/setWebhook"
        response = requests.post(telegram_api, json={'url': webhook_url}, timeout=10)
        response.raise_for_status()
        result = response.json()

        return jsonify({
            'status': 'success',
            'webhook_set': result.get('ok'),
            'webhook_url': webhook_url,
            'result': result
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
