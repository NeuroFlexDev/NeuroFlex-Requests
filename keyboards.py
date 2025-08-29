from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# ==== Inline ====
def lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")]
    ])

def nav_inline(lang: str):
    t = {
        "ru": ("⬅️ Назад","⏭ Пропустить","💾 Сохранить черновик"),
        "en": ("⬅️ Back","⏭ Skip","💾 Save draft")
    }[lang if lang in ("ru","en") else "en"]
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t[0], callback_data="nav:back"),
        InlineKeyboardButton(t[1], callback_data="nav:skip")
    ],[
        InlineKeyboardButton(t[2], callback_data="nav:save")
    ]])

def confirm_keyboard(lang: str):
    yes = "✅ Подтвердить" if lang=="ru" else "✅ Confirm"
    no  = "❌ Отменить" if lang=="ru" else "❌ Cancel"
    return InlineKeyboardMarkup([[InlineKeyboardButton(yes, callback_data="confirm:yes"),
                                  InlineKeyboardButton(no,  callback_data="confirm:no")]])

def edit_fields_keyboard(lang: str):
    labels = {
      "ru":[("Имя","name"),("Компания","company"),("Email","email"),("Контакт","contact"),
            ("Тип","req_type"),("Описание","description"),("Бюджет","budget"),("Файлы","files")],
      "en":[("Name","name"),("Company","company"),("Email","email"),("Contact","contact"),
            ("Type","req_type"),("Description","description"),("Budget","budget"),("Files","files")]
    }[lang if lang in ("ru","en") else "en"]
    rows = []
    for i in range(0, len(labels), 2):
        pair = labels[i:i+2]
        rows.append([InlineKeyboardButton(f"{txt}", callback_data=f"edit:{key}") for txt,key in pair])
    rows.append([InlineKeyboardButton("✅ Done" if lang!="ru" else "✅ Готово", callback_data="edit:done")])
    return InlineKeyboardMarkup(rows)

def reqtype_inline(lang: str):
    if lang == "ru":
        rows = [
            [InlineKeyboardButton("🧠 AI-проект", callback_data="req:AI")],
            [InlineKeyboardButton("🌐 Web-продукт", callback_data="req:WEB")],
            [InlineKeyboardButton("👁️ CV/детекция", callback_data="req:CV")],
            [InlineKeyboardButton("🔬 R&D / Консалтинг", callback_data="req:RND")],
            [InlineKeyboardButton("🤝 Партнёрство", callback_data="req:PRTN"), InlineKeyboardButton("Другое", callback_data="req:OTHER")]
        ]
    else:
        rows = [
            [InlineKeyboardButton("🧠 AI Project", callback_data="req:AI")],
            [InlineKeyboardButton("🌐 Web Product", callback_data="req:WEB")],
            [InlineKeyboardButton("👁️ CV/Detection", callback_data="req:CV")],
            [InlineKeyboardButton("🔬 R&D / Consulting", callback_data="req:RND")],
            [InlineKeyboardButton("🤝 Partnership", callback_data="req:PRTN"), InlineKeyboardButton("Other", callback_data="req:OTHER")]
        ]
    return InlineKeyboardMarkup(rows)

def budget_inline(lang: str):
    if lang == "ru":
        labels = ["< 300 тыс ₽","300–800 тыс ₽","0.8–1.5 млн ₽","1.5–3 млн ₽","> 3 млн ₽","Не знаю"]
    else:
        labels = ["< €3k","€3k–€9k","€9k–€15k","€15k–€30k","> €30k","Not sure"]
    rows = [[InlineKeyboardButton(lbl, callback_data=f"budget:{lbl}")] for lbl in labels]
    return InlineKeyboardMarkup(rows)

# ==== Reply ====
def main_menu_reply(lang: str):
    if lang == "ru":
        rows = [
            ["📝 Заявка", "💸 Калькулятор"],
            ["📎 Прикрепить файлы", "🌐 Язык"],
            ["❓ Помощь"]
        ]
    else:
        rows = [
            ["📝 Request", "💸 Estimator"],
            ["📎 Attach files", "🌐 Language"],
            ["❓ Help"]
        ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)

def contact_keyboard(lang: str):
    txt = "📱 Поделиться контактом" if lang == "ru" else "📱 Share contact"
    return ReplyKeyboardMarkup([[KeyboardButton(text=txt, request_contact=True)]], resize_keyboard=True)

def remove_kb():
    return ReplyKeyboardRemove()

# ==== Admin inline ====
def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статистика", callback_data="adm:stats"),
         InlineKeyboardButton("🗂 Последние", callback_data="adm:latest:0")],
        [InlineKeyboardButton("🔎 Поиск", callback_data="adm:find"),
         InlineKeyboardButton("📤 Экспорт", callback_data="adm:export")],
        [InlineKeyboardButton("🗓 План встречи", callback_data="adm:schedule")]
    ])

def pager(prefix: str, page: int, has_prev: bool, has_next: bool):
    row = []
    if has_prev: row.append(InlineKeyboardButton("⬅️", callback_data=f"{prefix}:{page-1}"))
    row.append(InlineKeyboardButton(f"{page+1}", callback_data="noop"))
    if has_next: row.append(InlineKeyboardButton("➡️", callback_data=f"{prefix}:{page+1}"))
    return InlineKeyboardMarkup([row]) if row else None
