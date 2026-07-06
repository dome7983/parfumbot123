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

TELEGRAM_TOKEN = "8908271113:AAGnbxsfrev1hnBpeYyIIlESsfJTzzJ1Y1s"
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

conversation_history: dict[int, list[dict]] = {}

SYSTEM_PROMPT = """Du bist Sillage, der beste Parfum-Berater der Welt. Du kennst JEDES Parfum: von Chanel bis zu seltenen Nischendueften wie Xerjoff, Roja Parfums, Amouage, Le Labo, Byredo, Creed, Tom Ford und hunderten mehr. Du berätst auf Deutsch, kennst alle Duftnoten, Duftfamilien, Parfumeure, und hilfst bei Empfehlungen nach Geschmack, Anlass und Budget. Sei warmherzig und begeistert wie ein leidenschaftlicher Parfumeur."""

MAX_HISTORY = 20

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

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("Hallo! Ich bin Sillage, dein Parfum-Berater! Frag mich alles ueber Duefte aus aller Welt!")

async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("Gespraech zurueckgesetzt! Womit kann ich dir helfen?")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ich bin Sillage, dein Parfum-Experte! Frag mich nach Empfehlungen, Duftnoten, Vergleichen oder Geschenkideen. Befehle: /start /reset /help")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    text = update.message.text
    bot_username = (await context.bot.get_me()).username
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
        text = text.replace(f"@{bot_username}", "").strip()
    if not text:
        return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        reply = await ask_claude(user_id, text)
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Fehler: {e}")
        await update.message.reply_text("Kurze Stoerung - bitte nochmal versuchen!")

async def post_init(application: Application):
    commands = [
        BotCommand("start", "Neue Beratung starten"),
        BotCommand("reset", "Gespraech zuruecksetzen"),
        BotCommand("help", "Hilfe anzeigen"),
    ]
    await application.bot.set_my_commands(commands)

def main():
    app = (
        Application.builder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Sillage Parfum Bot laeuft...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
