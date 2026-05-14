#!/usr/bin/env python3
"""
Combined Flask API + Telegram Bot
Runs both in same process (required for Render free tier)
"""
import os
import threading
from flask import Flask, jsonify
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


def run_bot():
    """Run Telegram bot in background thread"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')

    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN not set - bot disabled")
        return

    try:
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

        # Start bot
        print("🤖 Bot started in background thread...")
        bot_app.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        print(f"⚠️ Bot error: {e}")


if __name__ == '__main__':
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Start Flask app (main thread)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
