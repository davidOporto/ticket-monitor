# One Piece Treasure Cup Ticket Monitor 🎟️

Monitor automático para tickets: https://tickets.organizedplay.events/Event/Index?id=165

Notificación instant a Telegram quan entrades disponibles!

## Setup (5 minuts)

### 1. Crear Telegram Bot

1. Obre Telegram → cerca `@BotFather`
2. Envia `/newbot`
3. Nom: `Ticket Monitor` (o el que vulguis)
4. Username: `ticket_monitor_bot` (ha de acabar en _bot)
5. Copia el **TOKEN** que et dona (tipus: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Chat ID

1. Envia missatge al teu bot nou (cerca-lo per username)
2. Obre al navegador: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Canvia `<TOKEN>` pel teu token
3. Cerca `"chat":{"id":123456789` → copia el número

### 3. Deploy a GitHub

```bash
cd ticket-monitor
git init
git add .
git commit -m "Init ticket monitor"
gh repo create ticket-monitor --public --source=. --push
```

### 4. Configurar Secrets

GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**:

- Nom: `TELEGRAM_BOT_TOKEN`
  Valor: token de @BotFather
  
- Nom: `TELEGRAM_CHAT_ID`
  Valor: chat ID (número)

### 5. Activar Monitor

- GitHub repo → **Actions** tab
- Click "I understand, enable Actions"
- Click workflow "Ticket Monitor" → **Run workflow**

## Com funciona

- ✅ Check cada **15 minuts** automàtic
- 🔔 Notificació Telegram instant si disponible
- 💰 **100% gratis** (GitHub Actions free tier)
- 📱 Click link al missatge → comprar directe

## Test local

```bash
pip install requests
export TELEGRAM_BOT_TOKEN="tu_token"
export TELEGRAM_CHAT_ID="tu_chat_id"
python check_tickets.py
```

Output:
```
❌ All sold out - 2026-05-13 14:45:00
```

Quan disponible:
```
🎉 TICKETS AVAILABLE: One Piece Treasure Cup Ticket - Friday 10:00AM
🔗 https://tickets.organizedplay.events/Event/Index?id=165
✅ Telegram notification sent
```

## Troubleshooting

**Bot no envia missatges?**
- Verifica que has enviat primer missatge al bot
- Check secrets correctes a GitHub

**Actions no executen?**
- Repo ha de ser públic (o tenir GitHub Pro)
- Actions enabled a Settings

**Vull canviar frequència?**
- Edita `.github/workflows/monitor.yml`
- Línia `cron: '*/15 * * * *'`
- `*/15` = cada 15 min, `*/5` = cada 5 min

## Debug

Check logs: GitHub repo → Actions → últim run → Check tickets and notify
