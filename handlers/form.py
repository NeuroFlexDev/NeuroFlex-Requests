from telegram import Update, Message
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler, filters
from states import Form
from validators import RequestModel, validate_email, validate_phone
from storage import (
    save_request, save_temp_attachment, link_user_files_to_request,
    FILES_ROOT, draft_save, draft_load, draft_delete
)
from sheets import append_row_safe
from i18n import t
from keyboards import (
    confirm_keyboard, contact_keyboard, reqtype_inline, budget_inline,
    nav_inline, edit_fields_keyboard, remove_kb
)

# ===== Навигация: назад/вперёд =====
def _prev_state(cur: Form) -> Form:
    order = [Form.NAME, Form.COMPANY, Form.EMAIL, Form.CONTACT, Form.REQ_TYPE, Form.DESC, Form.FILES, Form.BUDGET, Form.CONFIRM]
    if cur in (Form.AI_DATA, Form.AI_DATASET):
        return Form.REQ_TYPE
    if cur in (Form.WEB_AUTH, Form.WEB_INTEGRATIONS):
        return Form.REQ_TYPE
    i = order.index(cur) if cur in order else 0
    return order[max(0, i - 1)]

def _next_state(cur: Form, context) -> Form:
    # ветка по типу
    if cur == Form.REQ_TYPE:
        v = context.user_data.get("req_type")
        if v == "AI":
            return Form.AI_DATA
        if v == "WEB":
            return Form.WEB_AUTH
        return Form.DESC
    chain = [Form.NAME, Form.COMPANY, Form.EMAIL, Form.CONTACT, Form.REQ_TYPE, Form.DESC, Form.FILES, Form.BUDGET, Form.CONFIRM]
    if cur not in chain:
        if cur == Form.AI_DATA:
            return Form.AI_DATASET
        if cur == Form.AI_DATASET:
            return Form.DESC
        if cur == Form.WEB_AUTH:
            return Form.WEB_INTEGRATIONS
        if cur == Form.WEB_INTEGRATIONS:
            return Form.DESC
        return Form.DESC
    i = chain.index(cur)
    return chain[min(len(chain) - 1, i + 1)]

async def _handle_nav(update: Update, context: ContextTypes.DEFAULT_TYPE, state_on_skip: Form):
    """Обработчик inline nav:* в любом шаге"""
    q = update.callback_query
    _, action = q.data.split(":")
    lang = context.user_data.get("lang", "ru")

    if action == "back":
        prev = _prev_state(context.user_data.get("_state", Form.NAME))
        context.user_data["_state"] = prev
        await q.answer()
        await q.edit_message_text(t(lang, "back_step"))
        return await ask_for_state(q.message, context, prev)

    if action == "skip":
        nxt = _next_state(context.user_data.get("_state", Form.NAME), context)
        context.user_data["_state"] = nxt
        await q.answer(t(lang, "skipped"))
        return await ask_for_state(q.message, context, nxt)

    if action == "save":
        draft_save(q.from_user.id, context.user_data)
        await q.answer("Saved")
        await q.edit_message_text(t(lang, "draft_saved"))
        return context.user_data["_state"]

    return context.user_data["_state"]

async def ask_for_state(message, context, state: Form):
    lang = context.user_data.get("lang", "ru")
    if state == Form.NAME:
        await message.reply_text(t(lang, "ask_name"), reply_markup=nav_inline(lang))
        return Form.NAME
    if state == Form.COMPANY:
        await message.reply_text(t(lang, "ask_company"), reply_markup=nav_inline(lang))
        return Form.COMPANY
    if state == Form.EMAIL:
        await message.reply_text(t(lang, "ask_email"), reply_markup=nav_inline(lang))
        return Form.EMAIL
    if state == Form.CONTACT:
        await message.reply_text(t(lang, "ask_contact"), reply_markup=contact_keyboard(lang))
        return Form.CONTACT
    if state == Form.REQ_TYPE:
        await message.reply_text(t(lang, "ask_req_type"))
        await message.reply_text(t(lang, "choose_req_type"), reply_markup=reqtype_inline(lang))
        return Form.REQ_TYPE
    if state == Form.DESC:
        await message.reply_text(t(lang, "ask_description"), reply_markup=nav_inline(lang))
        return Form.DESC
    if state == Form.FILES:
        await message.reply_text(t(lang, "ask_files") + " " + t(lang, "hint_files"), reply_markup=nav_inline(lang))
        return Form.FILES
    if state == Form.BUDGET:
        await message.reply_text(t(lang, "ask_budget"), reply_markup=budget_inline(lang))
        return Form.BUDGET
    return Form.CONFIRM

# ===== старт / черновик =====
async def form_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "ru")
    context.user_data["_state"] = Form.NAME
    # авто-черновик
    d = draft_load(update.effective_user.id)
    if d:
        context.user_data.update(d)
        await update.message.reply_text(t(lang, "draft_found"))
        return await ask_for_state(update.message, context, d.get("_state", Form.NAME))
    await update.message.reply_text(t(lang, "ask_name"), reply_markup=nav_inline(lang))
    return Form.NAME

# ===== шаги =====
async def name_h(update, context):
    context.user_data["_state"] = Form.NAME
    context.user_data["name"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "ask_company"), reply_markup=nav_inline(lang))
    return Form.COMPANY

async def company_h(update, context):
    context.user_data["_state"] = Form.COMPANY
    context.user_data["company"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "ask_email"), reply_markup=nav_inline(lang))
    return Form.EMAIL

async def email_h(update, context):
    context.user_data["_state"] = Form.EMAIL
    val = update.message.text
    lang = context.user_data["lang"]
    if not validate_email(val):
        await update.message.reply_text(t(lang, "bad_email"), reply_markup=nav_inline(lang))
        return Form.EMAIL
    context.user_data["email"] = val
    await update.message.reply_text(t(lang, "ask_contact"), reply_markup=contact_keyboard(lang))
    return Form.CONTACT

async def contact_h(update, context):
    context.user_data["_state"] = Form.CONTACT
    lang = context.user_data["lang"]
    if update.message.contact:
        phone = update.message.contact.phone_number
    else:
        phone = update.message.text
    if not validate_phone(phone):
        await update.message.reply_text(t(lang, "bad_phone"), reply_markup=contact_keyboard(lang))
        return Form.CONTACT
    context.user_data["contact"] = phone
    # убрать клавиатуру контакта
    await update.message.reply_text(t(lang, "ask_req_type"), reply_markup=remove_kb())
    await update.message.reply_text(t(lang, "choose_req_type"), reply_markup=reqtype_inline(lang))
    return Form.REQ_TYPE

# тип запроса: текст или кнопка
async def reqtype_text(update, context):
    context.user_data["_state"] = Form.REQ_TYPE
    context.user_data["req_type"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "ask_description"), reply_markup=nav_inline(lang))
    return Form.DESC

async def reqtype_cb(update, context):
    q = update.callback_query
    _, value = q.data.split(":")
    lang = context.user_data.get("lang", "ru")
    context.user_data["req_type"] = value
    context.user_data["_state"] = Form.REQ_TYPE
    await q.answer("OK")
    # ветвление
    if value == "AI":
        await q.edit_message_text(t(lang, "ai_data"))
        return Form.AI_DATA
    if value == "WEB":
        await q.edit_message_text(t(lang, "web_auth"))
        return Form.WEB_AUTH
    # без доп.ветвления
    await q.edit_message_text(t(lang, "ask_description"))
    return Form.DESC

async def ai_data_h(update, context):
    context.user_data["_state"] = Form.AI_DATA
    context.user_data["ai_data"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "ai_dataset"), reply_markup=nav_inline(lang))
    return Form.AI_DATASET

async def ai_dataset_h(update, context):
    context.user_data["_state"] = Form.AI_DATASET
    context.user_data["ai_dataset"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "ask_description"), reply_markup=nav_inline(lang))
    return Form.DESC

async def web_auth_h(update, context):
    context.user_data["_state"] = Form.WEB_AUTH
    context.user_data["web_auth"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "web_integrations"), reply_markup=nav_inline(lang))
    return Form.WEB_INTEGRATIONS

async def web_integrations_h(update, context):
    context.user_data["_state"] = Form.WEB_INTEGRATIONS
    context.user_data["web_integrations"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "ask_description"), reply_markup=nav_inline(lang))
    return Form.DESC

async def desc_h(update, context):
    context.user_data["_state"] = Form.DESC
    context.user_data["description"] = update.message.text
    lang = context.user_data["lang"]
    await update.message.reply_text(t(lang, "ask_files") + " " + t(lang, "hint_files"), reply_markup=nav_inline(lang))
    return Form.FILES

async def files_h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["_state"] = Form.FILES
    lang = context.user_data["lang"]
    uid = update.effective_user.id

    # документы
    if update.message.document:
        doc = update.message.document
        allowed = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "image/png",
            "image/jpeg",
        }
        if doc.mime_type and doc.mime_type not in allowed:
            await update.message.reply_text(t(lang, "file_reject"))
            return Form.FILES
        tg_file = await doc.get_file()
        dest = (FILES_ROOT / f"user_{uid}")
        dest.mkdir(parents=True, exist_ok=True)
        local_path = dest / f"{doc.file_unique_id}_{doc.file_name or 'file'}"
        await tg_file.download_to_drive(custom_path=str(local_path))
        save_temp_attachment(
            uid,
            file_id=doc.file_id,
            file_name=doc.file_name,
            mime_type=doc.mime_type,
            file_size=doc.file_size,
            local_path=str(local_path),
        )
        await update.message.reply_text(t(lang, "file_saved"))
        return Form.FILES

    # фото
    if update.message.photo:
        photo = update.message.photo[-1]
        tg_file = await photo.get_file()
        dest = (FILES_ROOT / f"user_{uid}")
        dest.mkdir(parents=True, exist_ok=True)
        local_path = dest / f"{photo.file_unique_id}.jpg"
        await tg_file.download_to_drive(custom_path=str(local_path))
        save_temp_attachment(
            uid,
            file_id=photo.file_id,
            file_name=f"{photo.file_unique_id}.jpg",
            mime_type="image/jpeg",
            file_size=photo.file_size or 0,
            local_path=str(local_path),
        )
        await update.message.reply_text(t(lang, "file_saved"))
        return Form.FILES

    # просто текст — подскажем ещё раз
    await update.message.reply_text(t(lang, "hint_files"))
    return Form.FILES

async def budget_text(update, context):
    context.user_data["_state"]=Form.BUDGET
    context.user_data["budget"]=update.message.text
    return await preview_and_confirm(update.message, context)


async def budget_cb(update, context):
    q = update.callback_query
    _, val = q.data.split(":")
    context.user_data["budget"] = val
    lang = context.user_data["lang"]
    await q.answer("OK")
    return await preview_and_confirm(q.message, context)

from telegram import Message

async def preview_and_confirm(target, context):
    """
    Принимает либо Message, либо Update, либо CallbackQuery.message;
    сам достанет корректный объект Message и вызовет reply_text().
    """
    # ---- normalize to Message
    if isinstance(target, Message):
        msg = target
    else:
        # target может быть Update, CallbackQuery.message, etc.
        # пробуем вытащить .message или .effective_message
        msg = getattr(target, "message", None) or getattr(target, "effective_message", None)
        if msg is None and hasattr(target, "callback_query") and target.callback_query:
            msg = target.callback_query.message
    if msg is None:
        # крайний случай — шлем в личку пользователю
        chat_id = context._chat_id  # fallback, PTB хранит контекст чата
        await context.bot.send_message(chat_id, "Preview unavailable due to context error.")
        return Form.CONFIRM

    lang = context.user_data["lang"]
    p = context.user_data
    preview = t(lang, "preview") + "\n" + "\n".join([
        f"{t(lang, 'f_name')}: {p.get('name', '')}",
        f"{t(lang, 'f_company')}: {p.get('company', '')}",
        f"{t(lang, 'f_email')}: {p.get('email', '')}",
        f"{t(lang, 'f_contact')}: {p.get('contact', '')}",
        f"{t(lang, 'f_type')}: {p.get('req_type', '')}",
        f"{t(lang, 'f_desc')}: {p.get('description', '')}",
        f"{t(lang, 'f_budget')}: {p.get('budget', '')}",
        f"AI data: {p.get('ai_data', '')}" if p.get("ai_data") else "",
        f"AI dataset: {p.get('ai_dataset', '')}" if p.get("ai_dataset") else "",
        f"Web auth: {p.get('web_auth', '')}" if p.get("web_auth") else "",
        f"Web integrations: {p.get('web_integrations', '')}" if p.get("web_integrations") else "",
    ]).strip()

    await msg.reply_text(preview)
    await msg.reply_text(t(lang, "edit_hint"), reply_markup=edit_fields_keyboard(lang))
    await msg.reply_text(t(lang, "confirm_hint"), reply_markup=confirm_keyboard(lang))
    return Form.CONFIRM


# ===== точечное редактирование =====
async def edit_cb(update, context):
    q = update.callback_query
    _, field = q.data.split(":")
    lang = context.user_data.get("lang", "ru")
    await q.answer()
    if field == "done":
        await q.edit_message_text(t(lang, "confirm_hint"))
        return Form.CONFIRM
    if field == "files":
        context.user_data["_state"] = Form.FILES
        await q.edit_message_text(t(lang, "ask_files") + " " + t(lang, "hint_files"))
        return Form.FILES
    if field == "req_type":
        await q.edit_message_text(t(lang, "choose_req_type"), reply_markup=reqtype_inline(lang))
        return Form.REQ_TYPE
    if field == "budget":
        await q.edit_message_text(t(lang, "ask_budget"), reply_markup=budget_inline(lang))
        return Form.BUDGET

    context.user_data["_edit_field"] = field
    prompt = {
        "name": "ask_name", "company": "ask_company", "email": "ask_email", "contact": "ask_contact",
        "req_type": "ask_req_type", "description": "ask_description", "budget": "ask_budget", "files": "ask_files"
    }.get(field, "ask_description")
    await q.edit_message_text(t(lang, prompt))
    return Form.EDIT_FIELD

async def edit_field_h(update, context):
    lang=context.user_data["lang"]; field=context.user_data.get("_edit_field")
    val = update.message.text
    if field == "email" and not validate_email(val):
        await update.message.reply_text(t(lang,"bad_email")); return Form.EDIT_FIELD
    if field == "contact" and not validate_phone(val):
        await update.message.reply_text(t(lang,"bad_phone")); return Form.EDIT_FIELD
    context.user_data[field] = val
    await update.message.reply_text(t(lang,"field_updated"))
    return await preview_and_confirm(update.message, context)


# ===== подтверждение =====
async def confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    _, val = q.data.split(":")
    lang = context.user_data.get("lang", "ru")
    if val == "yes":
        data = dict(context.user_data)
        # финальная валидация
        model = RequestModel(
            name=data["name"], company=data.get("company"),
            email=data["email"], contact=data["contact"],
            req_type=data["req_type"], description=data["description"],
            budget=data.get("budget"),
            ai_data=data.get("ai_data"), ai_dataset=data.get("ai_dataset"),
            web_auth=data.get("web_auth"), web_integrations=data.get("web_integrations")
        )
        payload = model.dict()
        payload["lang"] = lang
        rid = save_request(payload)
        uid = q.from_user.id
        link_user_files_to_request(user_id=uid, request_id=rid)
        draft_delete(uid)
        append_row_safe([
            payload["name"], payload.get("company", ""), payload["email"], payload["contact"],
            payload["req_type"], payload["description"], payload.get("budget", "")
        ])
        await q.edit_message_text(t(lang, "thanks_id").format(id=rid))
        from config import settings
        await context.bot.send_message(settings.ADMIN_ID, f"New request #{rid}:\n{payload}")
    else:
        await q.edit_message_text(t(lang, "cancelled"))
    return ConversationHandler.END

# ==== NAV callback (общий) ====
async def nav_cb(update, context):
    cur = context.user_data.get("_state", Form.NAME)
    return await _handle_nav(update, context, state_on_skip=cur if cur != Form.BUDGET else Form.CONFIRM)

def setup(app):
    conv = ConversationHandler(
        entry_points=[CommandHandler("form", form_start)],
        states={
            Form.NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, name_h),
                CallbackQueryHandler(nav_cb, pattern=r"^nav:(back|skip|save)$")
            ],
            Form.COMPANY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, company_h),
                CallbackQueryHandler(nav_cb, pattern=r"^nav:(back|skip|save)$")
            ],
            Form.EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, email_h),
                CallbackQueryHandler(nav_cb, pattern=r"^nav:(back|skip|save)$")
            ],
            Form.CONTACT: [
                MessageHandler((filters.CONTACT | (filters.TEXT & ~filters.COMMAND)), contact_h),
                CallbackQueryHandler(nav_cb, pattern=r"^nav:(back|skip|save)$")
            ],
            Form.REQ_TYPE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, reqtype_text),
                CallbackQueryHandler(reqtype_cb, pattern=r"^req:(AI|WEB|CV|RND|PRTN|OTHER)$")
            ],
            Form.AI_DATA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ai_data_h),
                CallbackQueryHandler(nav_cb, pattern=r"^nav:(back|skip|save)$")
            ],
            Form.AI_DATASET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ai_dataset_h),
                CallbackQueryHandler(nav_cb, pattern=r"^nav:(back|skip|save)$")
            ],
            Form.WEB_AUTH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, web_auth_h),
                CallbackQueryHandler(nav_cb, pattern=r"^nav:(back|skip|save)$")
            ],
            Form.WEB_INTEGRATIONS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, web_integrations_h),
                CallbackQueryHandler(nav_cb, pattern=r"^nav:(back|skip|save)$")
            ],
            Form.DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, desc_h),
                CallbackQueryHandler(nav_cb, pattern=r"^nav:(back|skip|save)$")
            ],
            Form.FILES: [
                MessageHandler((filters.Document.ALL | filters.PHOTO | (filters.TEXT & ~filters.COMMAND)), files_h),
                CallbackQueryHandler(nav_cb, pattern=r"^nav:(back|skip|save)$")
            ],
            Form.BUDGET: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, budget_text),
                CallbackQueryHandler(budget_cb, pattern=r"^budget:.+")
            ],
            Form.CONFIRM: [
                CallbackQueryHandler(confirm_cb, pattern=r"^confirm:(yes|no)$"),
                CallbackQueryHandler(edit_cb, pattern=r"^edit:(.+)$")
            ],
            Form.EDIT_FIELD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field_h)
            ],
        },
        fallbacks=[CommandHandler("form", form_start)],
        allow_reentry=True
    )
    app.add_handler(conv)
