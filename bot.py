# bot.py
from telegram.ext import Application
from logging_conf import setup_logging
from handlers import start as h_start, form as h_form, admin as h_admin, errors as h_err, calc as h_calc, menu as h_menu
from config import settings

def main():
    setup_logging()
    app = Application.builder().token(settings.BOT_TOKEN).build()

    # handlers
    h_start.setup(app)
    h_form.setup(app)
    h_admin.setup(app)
    h_calc.setup(app)
    h_menu.setup(app)
    app.add_error_handler(h_err.error_handler)

    # ВАЖНО: webhook не трогаем вручную.
    # run_polling сам создаёт event loop. Чтобы убрать конфликты с webhook — достаточно:
    app.run_polling(allowed_updates=None, drop_pending_updates=True)

if __name__ == "__main__":
    main()
