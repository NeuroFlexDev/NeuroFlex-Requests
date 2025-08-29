from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from keyboards import main_menu_inline, main_menu_reply, lang_keyboard
from i18n import t

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang","ru")
    await update.message.reply_text(
        t(lang,"menu_title"),
        reply_markup=main_menu_inline(lang)
    )
    # и дублируем реплай-меню
    await update.message.reply_text(t(lang,"menu_hint"), reply_markup=main_menu_reply(lang))

async def menu_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    _, action = q.data.split(":")
    lang = context.user_data.get("lang","ru")
    await q.answer()
    if action == "form":
        await q.edit_message_text(t(lang,"goto_form"))
        # подсказать /form
        await q.message.reply_text(t(lang,"hint_form"))
    elif action == "calc":
        await q.edit_message_text(t(lang,"goto_calc"))
        await q.message.reply_text("/calc")
    elif action == "lang":
        await q.edit_message_text(t(lang,"choose_lang"), reply_markup=lang_keyboard())
    elif action == "help":
        await q.edit_message_text(t(lang,"help_text"))
    else:
        await q.edit_message_text("…")

async def reply_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang","ru")
    text = (update.message.text or "").lower()
    if "заявка" in text or "request" in text:
        await update.message.reply_text(t(lang,"goto_form")); await update.message.reply_text("/form")
    elif "калькулятор" in text or "estimator" in text:
        await update.message.reply_text(t(lang,"goto_calc")); await update.message.reply_text("/calc")
    elif "язык" in text or "language" in text:
        await update.message.reply_text(t(lang,"choose_lang"), reply_markup=lang_keyboard())
    elif "прикреп" in text or "attach" in text or "files" in text:
        await update.message.reply_text(t(lang,"attach_hint"))
    elif "help" in text or "помощ" in text:
        await update.message.reply_text(t(lang,"help_text"))
    else:
        # оставляем как общий фоллбек — не спамим
        pass

def setup(app):
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CallbackQueryHandler(menu_cb, pattern=r"^menu:(form|calc|lang|help)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply_router))
