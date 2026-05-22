from typing import Final
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

# ── Placeholders ──────────────────────────────────────────────────────────────
TOKEN: Final = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY: Final = os.getenv("OPENAI_API_KEY")
BOT_USERNAME: Final = "@LegalCodebreakerBot"
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a Singapore legal information assistant. 

Your role is to help users understand the Singaporean legal system clearly and accurately.

Rules:
1. Only answer questions related to Singapore law, legislation, and the judiciary.
2. Only use these sources:
   - Singapore Statutes Online (sso.agc.gov.sg)
   - Attorney-General's Chambers (agc.gov.sg)
   - Singapore Judiciary (judiciary.gov.sg)
   - Ministry of Law (mlaw.gov.sg)
   - Legal Aid Bureau (lab.mlaw.gov.sg)
3. Always cite your sources explicitly — include the specific Act, section number, penal code, or official URL where the information was found
4. Quote the relevant section or clause when citing a statute or penal code.
5. If a question falls outside Singapore law, politely decline and redirect the user.
6. Always remind users that your answers are for informational purposes only and do not constitute legal advice. Encourage them to consult a qualified Singapore lawyer for matters requiring professional legal advice.
7. Do not speculate or fabricate legal provisions. If you are unsure, say so clearly."""


client = OpenAI(api_key=OPENAI_API_KEY)


# ── Commands ──────────────────────────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I'm Law4U, your Singapore legal information assistant.\n\n"
        "I can help you understand Singapore laws, statutes, penal codes, and the judiciary "
        "system — with cited sources from official Singapore government websites.\n\n"
        "⚠️ Note: I provide legal information, not legal advice. Always consult a qualified "
        "lawyer for matters requiring professional guidance.\n\n"
        "Ask me anything about Singapore law!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *How to use this bot:*\n\n"
        "Simply ask any question about Singapore law and I'll do my best to answer "
        "with cited sources from official Singapore government websites.\n\n"
        "*Example questions:*\n"
        "• What is the penalty for drug trafficking in Singapore?\n"
        "• What are my rights if I'm arrested?\n"
        "• What does the Misuse of Drugs Act cover?\n\n"
        "For professional legal advice, please consult a qualified Singapore lawyer",
        parse_mode="Markdown"
    )


# ── Core response logic ───────────────────────────────────────────────────────

def handle_response(text: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1024,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"OpenAI error: {e}")
        return "Sorry, I ran into an error fetching a response. Please try again shortly."

# ── Message handler ───────────────────────────────────────────────────────────

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"User ({update.message.chat.id}) in {message_type}: {text}")

    if message_type == "group":
        if BOT_USERNAME in text:
            text = text.replace(BOT_USERNAME, "").strip()
        else:
            return  # Ignore group messages that don't mention the bot

    # Show "typing..." indicator while processing
    await context.bot.send_chat_action(
        chat_id=update.message.chat_id,
        action="typing"
    )

    response = handle_response(text)
    print(f"Bot: {response}")
    await update.message.reply_text(response)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error: {context.error}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting LegalCodebreaker bot...")
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error_handler)

    print("Polling started...")
    app.run_polling(poll_interval=1)
