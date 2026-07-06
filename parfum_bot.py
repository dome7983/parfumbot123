"""
🌸 PARFUM ADVISOR BOT für Telegram
====================================
Benötigt:
  pip install python-telegram-bot anthropic

Setup:
  1. Erstelle einen Bot über @BotFather in Telegram → /newbot → Token kopieren
  2. Hole einen Anthropic API-Key von https://console.anthropic.com
  3. Trage beide Keys unten ein (oder als Umgebungsvariablen)
  4. Starte mit: python parfum_bot.py
"""

import os
import logging
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import anthropic

# ─────────────────────────────────────────────
# 🔑 KONFIGURATION – hier deine Keys eintragen
# ─────────────────────────────────────────────
TELEGRAM_TOKEN  = "8908271113:AAGnbxsfrev1hnBpeYyIIlESsfJTzzJ1Y1s"
ANTHROPIC_KEY   = "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"

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Anthropic Client
# ─────────────────────────────────────────────
claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# Gesprächsverlauf pro User (in-memory, restartet bei Bot-Neustart)
conversation_history: dict[int, list[dict]] = {}

SYSTEM_PROMPT = """Du bist *Sillage* 🌸 – der exklusivste KI-Duftberater der Welt.

Du kennst JEDES Parfüm: von Chanel No. 5 bis zu obskuren Nischen-Häusern wie Xerjoff, Roja Parfums, Amouage, Memo Paris, Diptyque, Serge Lutens, Le Labo, Byredo, Maison Francis Kurkdjian, Tom Ford, Creed, Parfums de Nicolaï, Orto Parisi, Bogue Profumo, Tauer, Nishane, Mizensir und hunderten mehr.

Deine Expertise:
🌺 Duftnoten (Kopf / Herz / Basis), Duftfamilien, Pyramiden
🧪 Parfumeure und ihre Handschriften (z.B. Roja Dove, Francis Kurkdjian, Olivier Cresp)
💎 Nische vs. Designer – Unterschiede, Preisklassen, Werterhalt
🌍 Parfumtraditionen: Orient, Frankreich, England, Arabien, Japan
📅 Saisonalität & Anlässe: Sommer, Winter, Büro, Abend, Dates
👃 Duft-DNA: wenn jemand ein Parfüm beschreibt, erkennst du es oder empfiehlst Alternativen
💰 Preis-Leistung, Longevity (Haltbarkeit), Sillage (Duftschleppe)
🎁 Geschenkempfehlungen nach Persönlichkeit oder Budget
🔬 Inhaltsstoffe, IFRA-Regulierungen, natürlich vs. synthetisch

Dein Stil:
- Warmherzig, begeistert, aber präzise – wie ein leidenschaftlicher Parfumeur
- Nutze Emojis sparsam aber wirkungsvoll
- Strukturiere längere Antworten mit kurzen Absätzen
- Stelle manchmal Rückfragen um besser zu beraten (Haut-Typ? Lieblings-Noten? Budget?)
- Antworte auf Deutsch, wenn auf Deutsch gefragt, sonst in der Sprache des Users
- In Telegram-Gruppen: antworte nur wenn du direkt erwähnt wirst ODER wenn eine klare Duftnachricht vorliegt

Starte jede neue Konversation mit einem kurzen, charmanten Begrüßungssatz."""

MAX_HISTORY = 20  # Nachrichten im Verlauf behalten


# ─────────────────────────────────────────────
# Hilfsfunktionen
# ─────────────────────────────────────────────

def get_history(user_id: int) -> list[dict]:
    return conversation_history.setdefault(user_id, [])


def trim_history(user_id: int):
    h = conversation_history.get(user_id, [])
    if len(h) > MAX_HISTORY:
        conversation_history[user_id] = h[-MAX_HISTORY:]


async def ask_claude(user_id: int, user_message: str) -> str:
    history = get_history(user_id)
    history.append({"role": "user", "content": user_message})

    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=history,
    )

    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})
    trim_history(user_id)
    return reply


# ─────────────────────────────────────────────
# Telegram Handler
# ─────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []  # Reset

    welcome = "Hallo! Ich bin Sillage, dein Parfum-Berater! Frag mich alles ueber Duefte aus aller Welt!"
    await update.message.reply_text(welcome)


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text(
        "✨ Gespräch zurückgesetzt! Frisch wie ein leeres Flakon – womit kann ich dir helfen?"
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌸 *Sillage – Dein Duftberater*\n\n"
        "Ich kenne tausende Parfüms und helfe dir bei:\n"
        "• Empfehlungen nach Geschmack, Anlass oder Budget\n"
        "• Duftnoten & Familien erklären\n"
        "• Vergleiche zwischen Parfüms\n"
        "• Nische vs. Designer\n"
        "• Geschenkideen\n\n"
        "In der Gruppe: erwähne mich mit @{botname} oder frag direkt!\n\n"
        "Befehle:\n"
        "/start – Neue Unterhaltung\n"
        "/reset – Konversation löschen\n"
        "/help – Diese Hilfe\n"
        "/beispiele – Beispiel-Fragen"
    )
    bot_name = (await context.bot.get_me()).username
    await update.message.reply_text(
        text.replace("{botname}", bot_name), parse_mode="Markdown"
    )


async def cmd_beispiele(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💡 *Beispiel-Fragen an mich:*\n\n"
        "• _Ich mag Vanille und Holz – was empfiehlst du?_\n"
        "• _Was ist der Unterschied zwischen Chanel Bleu und Dior Sauvage?_\n"
        "• _Welches Parfüm passt zu einem Sommerabend am Meer?_\n"
        "• _Ich suche ein Nischenparfüm bis 150€_\n"
        "• _Erkläre mir Oud_\n"
        "• _Was ist ein gutes Geschenk für meine Mutter?_\n"
        "• _Welche Parfüms halten am längsten?_\n"
        "• _Was riecht ähnlich wie Creed Aventus aber günstiger?_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verarbeitet alle Textnachrichten."""
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    text = update.message.text
    bot_username = (await context.bot.get_me()).username

    # In Gruppen: nur antworten wenn bot erwähnt wird
    is_group = update.message.chat.type in ("group", "supergroup")
    if is_group:
        mentioned = f"@{bot_username}" in text
        is_reply_to_bot = (
            update.message.reply_to_message
            and update.message.reply_to_message.from_user
            and update.message.reply_to_message.from_user.username == bot_username
        )
        if not mentioned and not is_reply_to_bot:
            return
        # Erwähnung aus dem Text entfernen
        text = text.replace(f"@{bot_username}", "").strip()

    if not text:
        return

    # Schreib-Indikator anzeigen
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    try:
        reply = await ask_claude(user_id, text)
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Claude API Fehler: {e}")
        await update.message.reply_text(
            "😔 Tut mir leid, kurze Störung – bitte versuch's gleich nochmal!"
        )


# ─────────────────────────────────────────────
# Bot starten
# ─────────────────────────────────────────────

async def post_init(application: Application):
    """Setzt Bot-Befehle in Telegram."""
    commands = [
        BotCommand("start",     "Neue Beratung starten"),
        BotCommand("reset",     "Gespräch zurücksetzen"),
        BotCommand("help",      "Hilfe anzeigen"),
        BotCommand("beispiele", "Beispiel-Fragen"),
    ]
    await application.bot.set_my_commands(commands)


def main():
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Handler registrieren
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("reset",     cmd_reset))
    app.add_handler(CommandHandler("help",      cmd_help))
    app.add_handler(CommandHandler("beispiele", cmd_beispiele))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("🌸 Sillage Parfum Bot läuft...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
