import time
from telegram import Update
from telegram.ext import ContextTypes
from config import settings

_user_bucket: dict[int, list[float]] = {}

async def rate_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    uid = update.effective_user.id if update.effective_user else 0
    now = time.time()
    bucket = _user_bucket.setdefault(uid, [])
    bucket[:] = [t for t in bucket if now - t < 60]
    if len(bucket) >= settings.RATE_LIMIT_PER_MIN:
        if update.effective_message:
            await update.effective_message.reply_text("Too many messages. Please wait a bit.")
        return False
    bucket.append(now)
    return True
