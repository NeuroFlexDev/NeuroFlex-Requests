from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CommandHandler, CallbackQueryHandler, filters
from states import Form
from validators import RequestModel
from storage import save_request, save_temp_attachment, link_user_files_to_request, FILES_ROOT
from sheets import append_row_safe
from i18n import t
from keyboards import confirm_keyboard, contact_keyboard, reqtype_inline, budget_inline, remove_kb
from telegram.ext import CallbackQueryHandler



async def form_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang","ru")
    await update.message.reply_text(t(lang,"ask_name"))
    return Form.NAME

async def name_h(update, context):
    context.user_data["name"]=update.message.text
    lang=context.user_data["lang"]
    await update.message.reply_text(t(lang,"ask_company"))
    return Form.COMPANY

async def company_h(update, context):
    context.user_data["company"]=update.message.text
    lang=context.user_data["lang"]
    await update.message.reply_text(t(lang,"ask_email"))
    return Form.EMAIL

async def email_h(update, context):
    context.user_data["email"]=update.message.text
    lang=context.user_data["lang"]
    await update.message.reply_text(t(lang,"ask_contact"), reply_markup=contact_keyboard(lang))
    return Form.CONTACT

async def contact_h(update, context):
    lang=context.user_data["lang"]
    if update.message.contact:
        # телега сама прислала phone_number
        context.user_data["contact"] = update.message.contact.phone_number
    else:
        context.user_data["contact"] = update.message.text
    await update.message.reply_text(t(lang,"ask_req_type"), reply_markup=None)
    await update.message.reply_text(t(lang,"choose_req_type"), reply_markup=reqtype_inline(lang))
    return Form.REQ_TYPE

async def type_h(update, context):
    # если пришло текстом (например, пользователь не нажал кнопку)
    context.user_data["req_type"]=update.message.text
    lang=context.user_data["lang"]
    await update.message.reply_text(t(lang,"ask_description"))
    return Form.DESC

async def reqtype_cb(update, context):
    q = update.callback_query
    _, value = q.data.split(":")
    context.user_data["req_type"] = value
    lang=context.user_data["lang"]
    await q.answer("OK")
    await q.edit_message_text(t(lang,"ask_description"))
    return Form.DESC


async def desc_h(update, context):
    context.user_data["description"]=update.message.text
    lang=context.user_data["lang"]
    await update.message.reply_text(t(lang,"ask_files") + " " + t(lang,"hint_files"))
    return Form.FILES


async def files_h(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data["lang"]
    uid = update.effective_user.id
    if update.message.document:
        doc = update.message.document
        tg_file = await doc.get_file()
        dest = (FILES_ROOT / f"user_{uid}")
        dest.mkdir(parents=True, exist_ok=True)
        local_path = dest / f"{doc.file_unique_id}_{doc.file_name or 'file'}"
        await tg_file.download_to_drive(custom_path=str(local_path))
        save_temp_attachment(uid, file_id=doc.file_id, file_name=doc.file_name,
                             mime_type=doc.mime_type, file_size=doc.file_size, local_path=str(local_path))
        await update.message.reply_text(t(lang,"file_saved"))
        return Form.FILES
    if update.message.photo:
        photo = update.message.photo[-1]
        tg_file = await photo.get_file()
        dest = (FILES_ROOT / f"user_{uid}")
        dest.mkdir(parents=True, exist_ok=True)
        local_path = dest / f"{photo.file_unique_id}.jpg"
        await tg_file.download_to_drive(custom_path=str(local_path))
        save_temp_attachment(uid, file_id=photo.file_id, file_name=f"{photo.file_unique_id}.jpg",
                             mime_type="image/jpeg", file_size=photo.file_size or 0, local_path=str(local_path))
        await update.message.reply_text(t(lang,"file_saved"))
        return Form.FILES
    txt = (update.message.text or "").strip().lower()
    if txt in {"пропустить","skip","далее","next"}:
        await update.message.reply_text(t(lang,"ask_budget"))
        return Form.BUDGET
    await update.message.reply_text(t(lang,"hint_files"))
    return Form.FILES

async def budget_h(update, context):
    # если человек написал сам — примем; но предложим кнопки
    context.user_data["budget"]=update.message.text
    lang=context.user_data["lang"]
    await update.message.reply_text(t(lang,"or_choose_budget"), reply_markup=budget_inline(lang))
    # и покажем сразу превью + confirm в колбэке выбора бюджета
    preview = t(lang,"preview") + "\n" + "\n".join([
        f"{t(lang,'f_name')}: {context.user_data['name']}",
        f"{t(lang,'f_company')}: {context.user_data.get('company','')}",
        f"{t(lang,'f_email')}: {context.user_data['email']}",
        f"{t(lang,'f_contact')}: {context.user_data['contact']}",
        f"{t(lang,'f_type')}: {context.user_data['req_type']}",
        f"{t(lang,'f_desc')}: {context.user_data['description']}",
        f"{t(lang,'f_budget')}: {context.user_data.get('budget','')}",
    ])
    await update.message.reply_text(preview, reply_markup=confirm_keyboard(lang))
    return Form.CONFIRM

async def budget_cb(update, context):
    q = update.callback_query
    _, value = q.data.split(":")
    context.user_data["budget"] = value
    lang=context.user_data["lang"]
    # обновим превью и предложим подтверждение
    preview = t(lang,"preview") + "\n" + "\n".join([
        f"{t(lang,'f_name')}: {context.user_data['name']}",
        f"{t(lang,'f_company')}: {context.user_data.get('company','')}",
        f"{t(lang,'f_email')}: {context.user_data['email']}",
        f"{t(lang,'f_contact')}: {context.user_data['contact']}",
        f"{t(lang,'f_type')}: {context.user_data['req_type']}",
        f"{t(lang,'f_desc')}: {context.user_data['description']}",
        f"{t(lang,'f_budget')}: {context.user_data.get('budget','')}",
    ])
    await q.edit_message_text(preview, reply_markup=confirm_keyboard(lang))
    return Form.CONFIRM


async def confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    _, val = q.data.split(":")
    lang = context.user_data["lang"]
    if val == "yes":
        data = dict(context.user_data)
        model = RequestModel(
            name=data["name"], company=data.get("company"),
            email=data["email"], contact=data["contact"],
            req_type=data["req_type"], description=data["description"],
            budget=data.get("budget")
        )
        payload = model.dict(); payload["lang"]=lang
        req_id = save_request(payload)
        uid = q.from_user.id
        link_user_files_to_request(user_id=uid, request_id=req_id)
        append_row_safe([payload["name"], payload.get("company",""), payload["email"], payload["contact"],
                         payload["req_type"], payload["description"], payload.get("budget","")])
        await q.edit_message_text(t(lang,"thanks"))
        from config import settings
        await context.bot.send_message(settings.ADMIN_ID, f"New request #{req_id}:\n{payload}")
    else:
        await q.edit_message_text(t(lang,"cancelled"))
    return ConversationHandler.END

def setup(app):
    conv = ConversationHandler(
    entry_points=[CommandHandler("form", form_start)],
    states={
        Form.NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_h)],
        Form.COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, company_h)],
        Form.EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email_h)],
        Form.CONTACT: [MessageHandler((filters.CONTACT | (filters.TEXT & ~filters.COMMAND)), contact_h)],
        Form.REQ_TYPE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, type_h),
            CallbackQueryHandler(reqtype_cb, pattern=r"^req:.+")
        ],
        Form.DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, desc_h)],
        Form.FILES: [MessageHandler((filters.Document.ALL | filters.PHOTO | (filters.TEXT & ~filters.COMMAND)), files_h)],
        Form.BUDGET: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, budget_h),
            CallbackQueryHandler(budget_cb, pattern=r"^budget:.+")
        ],
        Form.CONFIRM: [CallbackQueryHandler(confirm_cb, pattern=r"^confirm:(yes|no)$")]
    },
    fallbacks=[CommandHandler("form", form_start)],
    allow_reentry=True,
    per_message=True,   # ← ДОБАВЬ ЭТО

    )

    app.add_handler(conv)
