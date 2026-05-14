#!/usr/bin/env python3
"""
Telegram Bot for managing ticket monitor events
Commands:
  /start - Welcome message
  /add_event - Add new event (interactive)
  /list_events - Show all configured events
  /remove_event <id> - Remove event by ID
  /toggle_event <id> - Enable/disable event
"""
import os
import re
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from config_manager import get_config_manager

# Conversation states
WAITING_URL, WAITING_NAME, WAITING_TICKETS = range(3)

# Store temp data during conversation
user_data_store = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - welcome message"""
    await update.message.reply_text(
        "🎟️ <b>Ticket Monitor Bot</b>\n\n"
        "Gestiona events d'organized play:\n\n"
        "<b>Comandes:</b>\n"
        "/add_event - Afegir nou event\n"
        "/list_events - Veure events configurats\n"
        "/remove_event &lt;id&gt; - Eliminar event\n"
        "/toggle_event &lt;id&gt; - Activar/desactivar event\n"
        "/cancel - Cancel·lar operació actual",
        parse_mode='HTML'
    )


async def add_event_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding new event - ask for URL"""
    await update.message.reply_text(
        "📝 <b>Afegir nou event</b>\n\n"
        "Envia URL del event d'organized play:\n"
        "Exemple: https://tickets.organizedplay.events/Event/Index?id=165\n\n"
        "O /cancel per sortir",
        parse_mode='HTML'
    )
    return WAITING_URL


async def add_event_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive URL, ask for name"""
    url = update.message.text.strip()

    # Validate URL
    if not re.match(r'https://tickets\.organizedplay\.events/Event/Index\?id=\d+', url):
        await update.message.reply_text(
            "⚠️ URL invàlida. Ha de ser:\n"
            "https://tickets.organizedplay.events/Event/Index?id=NUMBER\n\n"
            "Torna a enviar URL o /cancel"
        )
        return WAITING_URL

    # Extract event ID from URL
    match = re.search(r'id=(\d+)', url)
    event_id = f"event-{match.group(1)}"

    # Store in temp data
    user_id = update.effective_user.id
    user_data_store[user_id] = {
        'url': url,
        'id': event_id
    }

    await update.message.reply_text(
        f"✅ URL guardada\n"
        f"🆔 ID auto: <code>{event_id}</code>\n\n"
        "📝 Ara envia <b>nom del event</b>:\n"
        "Exemple: One Piece Treasure Cup",
        parse_mode='HTML'
    )
    return WAITING_NAME


async def add_event_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive name, ask for tickets"""
    name = update.message.text.strip()
    user_id = update.effective_user.id

    if user_id not in user_data_store:
        await update.message.reply_text("⚠️ Error: dades perdudes. Torna a /add_event")
        return ConversationHandler.END

    user_data_store[user_id]['name'] = name

    await update.message.reply_text(
        "✅ Nom guardat\n\n"
        "🎟️ Ara envia <b>noms dels tickets</b> (un per línia):\n\n"
        "Exemple:\n"
        "<code>One Piece Treasure Cup Ticket - Friday 10:00AM\n"
        "One Piece Treasure Cup Ticket - Saturday 10:00AM</code>\n\n"
        "Envia tots de cop!",
        parse_mode='HTML'
    )
    return WAITING_TICKETS


async def add_event_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive tickets, save to Gist"""
    tickets_text = update.message.text.strip()
    user_id = update.effective_user.id

    if user_id not in user_data_store:
        await update.message.reply_text("⚠️ Error: dades perdudes. Torna a /add_event")
        return ConversationHandler.END

    # Split tickets by newlines
    tickets = [t.strip() for t in tickets_text.split('\n') if t.strip()]

    if not tickets:
        await update.message.reply_text(
            "⚠️ Cap ticket detectat. Envia almenys un nom de ticket:"
        )
        return WAITING_TICKETS

    # Get stored data
    event_data = user_data_store[user_id]
    event_id = event_data['id']
    name = event_data['name']
    url = event_data['url']

    # Save to Gist
    config_mgr = get_config_manager()
    if not config_mgr:
        await update.message.reply_text("⚠️ Error: config manager no disponible")
        return ConversationHandler.END

    success = config_mgr.add_event(event_id, name, url, tickets)

    if success:
        await update.message.reply_text(
            f"✅ <b>Event afegit!</b>\n\n"
            f"🆔 ID: <code>{event_id}</code>\n"
            f"📝 Nom: {name}\n"
            f"🎟️ Tickets: {len(tickets)}\n"
            f"🔗 URL: {url}\n\n"
            "El monitor comprovarà aquest event cada 10 minuts.",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"⚠️ Error afegint event (potser ID {event_id} ja existeix?)"
        )

    # Clean temp data
    del user_data_store[user_id]

    return ConversationHandler.END


async def list_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all configured events"""
    config_mgr = get_config_manager()
    if not config_mgr:
        await update.message.reply_text("⚠️ Config manager no disponible")
        return

    config = config_mgr.read_config()
    events = config.get('events', [])

    if not events:
        await update.message.reply_text("📭 Cap event configurat. Usa /add_event")
        return

    message = "📋 <b>Events configurats:</b>\n\n"

    for event in events:
        status = "✅" if event.get('enabled', True) else "🔕"
        message += (
            f"{status} <b>{event['name']}</b>\n"
            f"   🆔 <code>{event['id']}</code>\n"
            f"   🎟️ {len(event.get('tickets', []))} tickets\n"
            f"   🔗 {event['url']}\n\n"
        )

    await update.message.reply_text(message, parse_mode='HTML')


async def remove_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove event by ID"""
    if not context.args:
        await update.message.reply_text(
            "❌ Falta ID. Usa:\n"
            "/remove_event event-123"
        )
        return

    event_id = context.args[0]

    config_mgr = get_config_manager()
    if not config_mgr:
        await update.message.reply_text("⚠️ Config manager no disponible")
        return

    success = config_mgr.remove_event(event_id)

    if success:
        await update.message.reply_text(f"✅ Event <code>{event_id}</code> eliminat", parse_mode='HTML')
    else:
        await update.message.reply_text(f"⚠️ Event <code>{event_id}</code> no trobat", parse_mode='HTML')


async def toggle_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle event enabled/disabled"""
    if not context.args:
        await update.message.reply_text(
            "❌ Falta ID. Usa:\n"
            "/toggle_event event-123"
        )
        return

    event_id = context.args[0]

    config_mgr = get_config_manager()
    if not config_mgr:
        await update.message.reply_text("⚠️ Config manager no disponible")
        return

    # Get current state
    config = config_mgr.read_config()
    event = next((e for e in config.get('events', []) if e['id'] == event_id), None)

    if not event:
        await update.message.reply_text(f"⚠️ Event <code>{event_id}</code> no trobat", parse_mode='HTML')
        return

    new_state = not event.get('enabled', True)
    success = config_mgr.toggle_event(event_id, new_state)

    if success:
        status = "activat ✅" if new_state else "desactivat 🔕"
        await update.message.reply_text(
            f"Event <code>{event_id}</code> {status}",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("⚠️ Error canviant estat")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    user_id = update.effective_user.id
    if user_id in user_data_store:
        del user_data_store[user_id]

    await update.message.reply_text("❌ Operació cancel·lada")
    return ConversationHandler.END


def main():
    """Start bot"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')

    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN not set")
        return

    # Create application
    app = Application.builder().token(token).build()

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

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('list_events', list_events))
    app.add_handler(CommandHandler('remove_event', remove_event))
    app.add_handler(CommandHandler('toggle_event', toggle_event))

    # Start bot
    print("🤖 Bot started...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
