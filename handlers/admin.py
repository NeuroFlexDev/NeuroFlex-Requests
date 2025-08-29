from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from storage import export_csv, export_json, list_attachments_by_request
from config import settings
from pathlib import Path

async def _is_admin(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == settings.ADMIN_ID

async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_admin(update): return
    Path("data").mkdir(exist_ok=True)
    csv_path = export_csv("data/requests.csv")
    json_path = export_json("data/requests.json")
    await update.message.reply_document(open(csv_path,"rb"))
    await update.message.reply_document(open(json_path,"rb"))

async def cmd_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_admin(update): return
    if not context.args:
        await update.message.reply_text("Usage: /files <request_id>")
        return
    rid = int(context.args[0])
    items = list_attachments_by_request(rid)
    if not items:
        await update.message.reply_text("No files.")
        return
    msg = "\n".join([f"- {i.get('file_name') or i.get('local_path')} ({i.get('mime_type')}, {i.get('file_size')})" for i in items])
    await update.message.reply_text(msg)

def setup(app):
    app.add_handler(CommandHandler("export", cmd_export))
    app.add_handler(CommandHandler("files", cmd_files))
