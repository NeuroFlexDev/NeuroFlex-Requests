import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import BOT_TOKEN, ADMIN_ID, GOOGLE_SHEET_NAME, GOOGLE_CREDS_FILE
import locale_data

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

LANG, NAME, COMPANY, EMAIL, CONTACT, REQ_TYPE, DESCRIPTION, BUDGET, CONFIRM = range(9)

user_data_temp = {}

def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDS_FILE, scope)
    return gspread.authorize(creds)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang_code = update.effective_user.language_code
    if lang_code not in locale_data.messages:
        lang_code = 'en'
    context.user_data['lang'] = lang_code
    await update.message.reply_text(locale_data.messages[lang_code]['start'])
    return NAME

async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']
    context.user_data['name'] = update.message.text
    await update.message.reply_text(locale_data.messages[lang]['ask_company'])
    return COMPANY

async def company_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']
    context.user_data['company'] = update.message.text
    await update.message.reply_text(locale_data.messages[lang]['ask_email'])
    return EMAIL

async def email_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']
    context.user_data['email'] = update.message.text
    await update.message.reply_text(locale_data.messages[lang]['ask_contact'])
    return CONTACT

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']
    context.user_data['contact'] = update.message.text
    await update.message.reply_text(locale_data.messages[lang]['ask_req_type'])
    return REQ_TYPE

async def req_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']
    context.user_data['req_type'] = update.message.text
    await update.message.reply_text(locale_data.messages[lang]['ask_description'])
    return DESCRIPTION

async def description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']
    context.user_data['description'] = update.message.text
    await update.message.reply_text(locale_data.messages[lang]['ask_budget'])
    return BUDGET

async def budget_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']
    context.user_data['budget'] = update.message.text
    await update.message.reply_text(locale_data.messages[lang]['confirm'])
    return CONFIRM

async def confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data['lang']
    text = update.message.text.lower()
    if text in ['yes', 'да']:
        save_request(context.user_data)
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"New request:\n{json.dumps(context.user_data, ensure_ascii=False, indent=2)}")
        await update.message.reply_text(locale_data.messages[lang]['thanks'])
    else:
        await update.message.reply_text(locale_data.messages[lang]['cancelled'])
    return ConversationHandler.END

def save_request(data):
    os.makedirs("data", exist_ok=True)
    json_path = "data/requests.json"
    csv_path = "data/requests.csv"

    # Save to JSON
    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    else:
        existing = []
    existing.append(data)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    # Save to CSV
    df = pd.DataFrame(existing)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    # Save to Google Sheets
    try:
        gc = get_gsheet_client()
        sh = gc.open(GOOGLE_SHEET_NAME)
        worksheet = sh.sheet1
        worksheet.append_row([
            data.get('name', ''),
            data.get('company', ''),
            data.get('email', ''),
            data.get('contact', ''),
            data.get('req_type', ''),
            data.get('description', ''),
            data.get('budget', '')
        ])
    except Exception as e:
        logging.error(f"Google Sheets save error: {e}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_handler)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email_handler)],
            CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, contact_handler)],
            REQ_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, req_type_handler)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_handler)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget_handler)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_handler)],
        },
        fallbacks=[CommandHandler('start', start)]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()
