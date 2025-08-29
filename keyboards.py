from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# ==== Inline ====
def lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
         InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")]
    ])

def confirm_keyboard(lang: str):
    yes = "Да" if lang == "ru" else "Yes"
    no = "Нет" if lang == "ru" else "No"
    return InlineKeyboardMarkup([[InlineKeyboardButton(yes, callback_data="confirm:yes"),
                                  InlineKeyboardButton(no, callback_data="confirm:no")]])

def main_menu_inline(lang: str):
    t = {
        "ru": {"form":"📝 Оставить заявку","calc":"💸 Калькулятор","lang":"🌐 Язык","help":"❓ Помощь"},
        "en": {"form":"📝 Submit Request","calc":"💸 Estimator","lang":"🌐 Language","help":"❓ Help"}
    }[lang if lang in ("ru","en") else "en"]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t["form"], callback_data="menu:form"),
         InlineKeyboardButton(t["calc"], callback_data="menu:calc")],
        [InlineKeyboardButton(t["lang"], callback_data="menu:lang"),
         InlineKeyboardButton(t["help"], callback_data="menu:help")]
    ])

def reqtype_inline(lang: str):
    if lang == "ru":
        rows = [
            [InlineKeyboardButton("🤝 Партнёрство", callback_data="req:Партнёрство")],
            [InlineKeyboardButton("🧠 AI-проект", callback_data="req:AI-проект")],
            [InlineKeyboardButton("👁️ CV/детекция", callback_data="req:Компьютерное зрение")],
            [InlineKeyboardButton("🌐 Web-продукт", callback_data="req:Web-продукт")],
            [InlineKeyboardButton("🔬 R&D / Консалтинг", callback_data="req:R&D")],
            [InlineKeyboardButton("Другое", callback_data="req:Другое")]
        ]
    else:
        rows = [
            [InlineKeyboardButton("🤝 Partnership", callback_data="req:Partnership")],
            [InlineKeyboardButton("🧠 AI Project", callback_data="req:AI Project")],
            [InlineKeyboardButton("👁️ CV/Detection", callback_data="req:Computer Vision")],
            [InlineKeyboardButton("🌐 Web Product", callback_data="req:Web Product")],
            [InlineKeyboardButton("🔬 R&D / Consulting", callback_data="req:R&D")],
            [InlineKeyboardButton("Other", callback_data="req:Other")]
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
