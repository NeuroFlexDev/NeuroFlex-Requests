from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from config import settings
from storage import stats, get_latest, search_requests, export_csv, export_json, make_pdf_brief, get_request
from keyboards import admin_menu, pager

PAGE_SIZE = 5

async def _is_admin(update: Update) -> bool:
    u = update.effective_user
    return bool(u and u.id == settings.ADMIN_ID)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_admin(update): return
    await update.message.reply_text("Админ-панель:", reply_markup=admin_menu())

async def adm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id != settings.ADMIN_ID: return
    parts = q.data.split(":")
    action = parts[1]
    if action == "stats":
        s = stats()
        txt = "📊 Статистика\nTotal: {}\n".format(s["total"]) + "\n".join([f"- {k}: {v}" for k,v in s["by_type"].items()])
        await q.edit_message_text(txt, reply_markup=admin_menu())
    elif action == "latest":
        page = int(parts[2])
        items = get_latest(limit=PAGE_SIZE, offset=page*PAGE_SIZE)
        if not items:
            await q.answer("Нет данных"); return
        lines = [f"#{i['id']} • {i['created_at']} • {i['name']} • {i['req_type']}" for i in items]
        await q.edit_message_text("🗂 Последние:\n" + "\n".join(lines), reply_markup=pager("adm:latest", page, page>0, len(items)==PAGE_SIZE))
    elif action == "export":
        csv_path = export_csv("data/requests.csv"); json_path = export_json("data/requests.json")
        await q.answer("Готовлю файлы…", show_alert=False)
        await q.message.reply_document(open(csv_path,"rb"))
        await q.message.reply_document(open(json_path,"rb"))
    elif action == "find":
        await q.edit_message_text("Отправьте команду: /find <текст>")
    elif action == "schedule":
        await q.edit_message_text("Планировщик встреч добавим после подключения Google Calendar 😉")
    else:
        await q.answer("…")

async def cmd_find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_admin(update): return
    if not context.args:
        await update.message.reply_text("Использование: /find <текст>"); return
    q = " ".join(context.args)
    rows = search_requests(q, limit=10, offset=0)
    if not rows:
        await update.message.reply_text("Ничего не найдено."); return
    text = "\n".join([f"#{r['id']} • {r['name']} • {r['company'] or '-'} • {r['req_type']}\n{r['snippet']}" for r in rows])
    await update.message.reply_text("Результаты:\n"+text+"\n\nСформировать PDF бриф: /brief <id>")

async def cmd_brief(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await _is_admin(update): return
    if not context.args:
        await update.message.reply_text("Использование: /brief <id>"); return
    rid = int(context.args[0])
    req = get_request(rid)
    if not req:
        await update.message.reply_text("Заявка не найдена"); return
    pdf = make_pdf_brief(rid)
    await update.message.reply_document(open(pdf,"rb"), caption=f"Brief #{rid}")

def setup(app):
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(adm_cb, pattern=r"^adm:(stats|latest:\d+|find|export|schedule)$"))
    app.add_handler(CommandHandler("find", cmd_find))
    app.add_handler(CommandHandler("brief", cmd_brief))
