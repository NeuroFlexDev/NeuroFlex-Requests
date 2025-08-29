from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from states import Calc
from i18n import t
from config import settings

CATEGORIES = {
    "ai_mvp": "AI MVP (LLM/CV/NLP)",
    "cv_det": "Computer Vision / Detection",
    "web_app": "Web App (MVP)",
    "rd_cons": "R&D / Consulting"
}

def kb_categories():
    rows = [[InlineKeyboardButton(name, callback_data=f"cat:{key}")]
            for key, name in CATEGORIES.items()]
    return InlineKeyboardMarkup(rows)

def kb_complexity():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Basic", callback_data="cx:basic"),
        InlineKeyboardButton("Pro", callback_data="cx:pro"),
        InlineKeyboardButton("Enterprise", callback_data="cx:ent"),
    ]])

def kb_speed():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Обычный срок", callback_data="sp:norm"),
        InlineKeyboardButton("Ускоренный", callback_data="sp:rush")
    ]])

def kb_currency():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("₽ RUB", callback_data="cur:RUB"),
        InlineKeyboardButton("€ EUR", callback_data="cur:EUR")
    ]])

async def calc_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang","ru")
    context.user_data["calc"] = {}
    await update.message.reply_text(t(lang,"calc_start"), reply_markup=kb_categories())
    return Calc.CAT

async def cat_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    _, key = q.data.split(":")
    context.user_data["calc"]["category"] = key
    await q.answer("OK")
    lang = context.user_data.get("lang","ru")
    await q.edit_message_text(t(lang,"calc_scope"))
    return Calc.SCOPE

async def scope_h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["calc"]["scope"] = update.message.text
    lang = context.user_data.get("lang","ru")
    await update.message.reply_text(t(lang,"calc_complexity"), reply_markup=kb_complexity())
    return Calc.COMPLEXITY

async def complexity_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    _, cx = q.data.split(":")
    context.user_data["calc"]["complexity"] = cx
    await q.answer("OK")
    lang = context.user_data.get("lang","ru")
    await q.edit_message_text(t(lang,"calc_speed"), reply_markup=kb_speed())
    return Calc.SPEED

async def speed_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    _, sp = q.data.split(":")
    context.user_data["calc"]["speed"] = sp
    await q.answer("OK")
    lang = context.user_data.get("lang","ru")
    await q.edit_message_text(t(lang,"calc_currency"), reply_markup=kb_currency())
    return Calc.CURRENCY

async def currency_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    _, cur = q.data.split(":")
    context.user_data["calc"]["currency"] = cur
    await q.answer("OK")
    lang = context.user_data.get("lang","ru")
    c = context.user_data["calc"]

    base_hours = {
        "ai_mvp": 120,
        "cv_det": 160,
        "web_app": 140,
        "rd_cons": 40
    }[c["category"]]

    cx_mult = {"basic": 1.0, "pro": 1.5, "ent": 2.2}[c["complexity"]]
    sp_mult = {"norm": 1.0, "rush": 1.35}[c["speed"]]
    rate = {"RUB": 3500, "EUR": 45}[c["currency"]]

    hours = round(base_hours * cx_mult * sp_mult)
    subtotal = hours * rate
    risk = 0.15 if c["complexity"] != "basic" else 0.10
    total_min = int(subtotal * 0.95)
    total_max = int(subtotal * (1.0 + risk))

    c.update(hours=hours, rate=rate, total_min=total_min, total_max=total_max)

    scope = c.get("scope","")
    msg = t(lang,"calc_result").format(
        cat=CATEGORIES[c["category"]],
        scope=scope, hours=hours, rate=rate, cur=c["currency"],
        total_min=total_min, total_max=total_max
    )
    await q.edit_message_text(msg)
    await context.bot.send_message(settings.ADMIN_ID, f"[CALC] {update.effective_user.full_name}\n{c}")
    return ConversationHandler.END

def setup(app):
    conv = ConversationHandler(
        entry_points=[CommandHandler("calc", calc_start)],
        states={
            Calc.CAT: [CallbackQueryHandler(cat_cb, pattern=r"^cat:")],
            Calc.SCOPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, scope_h)],
            Calc.COMPLEXITY: [CallbackQueryHandler(complexity_cb, pattern=r"^cx:(basic|pro|ent)$")],
            Calc.SPEED: [CallbackQueryHandler(speed_cb, pattern=r"^sp:(norm|rush)$")],
            Calc.CURRENCY: [CallbackQueryHandler(currency_cb, pattern=r"^cur:(RUB|EUR)$")]
        },
        fallbacks=[CommandHandler("calc", calc_start)],
        allow_reentry=True,

    )
    app.add_handler(conv)
