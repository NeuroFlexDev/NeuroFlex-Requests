from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from i18n import t
from keyboards import lang_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'lang' not in context.user_data:
        context.user_data['lang'] = (update.effective_user.language_code or 'en')[:2]
    lang = context.user_data['lang']
    await update.message.reply_text(t(lang, "start"), reply_markup=lang_keyboard())

async def choose_lang_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    _, lang = q.data.split(":")
    context.user_data["lang"] = lang
    await q.answer("OK")
    await q.edit_message_text(t(lang, "lang_selected"))
    await q.message.reply_text(t(lang, "hint_form"))

def setup(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(choose_lang_cb, pattern=r"^lang:(ru|en)$"))
