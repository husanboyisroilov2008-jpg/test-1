from __future__ import annotations

import hmac
import json
import logging
import os
from hashlib import sha256
from io import BytesIO
from typing import Any
from urllib.parse import parse_qsl

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from telegram import InputFile, KeyboardButton, ReplyKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("husanboy-telegram-bot")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
ALLOWED_ORIGINS = [item.strip() for item in os.getenv("ALLOWED_ORIGINS", "").split(",") if item.strip()]

app = FastAPI(title="Husanboy Telegram Bot API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

telegram_app: Application | None = None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not WEBAPP_URL:
        await update.message.reply_text("WEBAPP_URL hali sozlanmagan. Admin Render env'ga WEBAPP_URL qo'yishi kerak.")
        return

    button = KeyboardButton(text="📄 Husanboy Scan ochish", web_app=WebAppInfo(url=WEBAPP_URL))
    markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True)
    text = (
        "Assalomu alaykum. Bu Husanboy Scan boti.\n\n"
        "Nima qiladi:\n"
        "- kameradan hujjatni topadi\n"
        "- qiyshiq sahifani tekislaydi\n"
        "- oqartiradi va PDF qiladi\n"
        "- xohlasangiz tayyor PDF'ni shu chatga yuboradi\n\n"
        "Ishlatish:\n"
        "1) Pastdagi tugmani bosing\n"
        "2) Sahifalarni skaner qiling\n"
        "3) Telegramga yuborish tugmasini bosing"
    )
    await update.message.reply_text(text, reply_markup=markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("/start bosing va Husanboy Scan mini app'ni oching.")


async def startup_bot() -> None:
    global telegram_app
    if not BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN topilmadi. Bot polling ishga tushmaydi.")
        return
    if telegram_app is not None:
        return
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start_command))
    telegram_app.add_handler(CommandHandler("help", help_command))
    await telegram_app.initialize()
    await telegram_app.start()
    if telegram_app.updater:
        await telegram_app.updater.start_polling(drop_pending_updates=True)
    logger.info("Telegram bot polling started")


async def shutdown_bot() -> None:
    global telegram_app
    if telegram_app is None:
        return
    try:
        if telegram_app.updater:
            await telegram_app.updater.stop()
        await telegram_app.stop()
        await telegram_app.shutdown()
    finally:
        telegram_app = None


@app.on_event("startup")
async def on_startup() -> None:
    await startup_bot()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await shutdown_bot()


@app.get("/")
def root() -> dict[str, Any]:
    return {"ok": True, "service": "Husanboy Telegram Bot API", "webapp": WEBAPP_URL or None}


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "Husanboy Telegram Bot API", "bot_configured": bool(BOT_TOKEN), "webapp_configured": bool(WEBAPP_URL)}


def verify_telegram_init_data(init_data: str) -> dict[str, Any]:
    if not BOT_TOKEN:
        raise HTTPException(status_code=500, detail="TELEGRAM_BOT_TOKEN sozlanmagan")
    if not init_data:
        raise HTTPException(status_code=400, detail="init_data bo'sh")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=400, detail="Telegram hash topilmadi")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(key=b"WebAppData", msg=BOT_TOKEN.encode(), digestmod=sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=403, detail="Telegram init data tasdiqlanmadi")

    user_raw = pairs.get("user")
    user = json.loads(user_raw) if user_raw else None
    if not user or "id" not in user:
        raise HTTPException(status_code=400, detail="Telegram user topilmadi")
    return {"user": user, "data": pairs}


@app.post("/api/telegram/send-pdf")
async def send_pdf_to_chat(
    pdf: UploadFile = File(...),
    init_data: str = Form(...),
    filename: str = Form("husanboy-scan.pdf"),
):
    if telegram_app is None:
        raise HTTPException(status_code=503, detail="Telegram bot hali tayyor emas")

    verified = verify_telegram_init_data(init_data)
    user = verified["user"]
    chat_id = int(user["id"])
    raw = await pdf.read()
    if not raw:
        raise HTTPException(status_code=400, detail="PDF bo'sh")

    bio = BytesIO(raw)
    bio.name = filename
    await telegram_app.bot.send_document(
        chat_id=chat_id,
        document=InputFile(bio, filename=filename),
        caption="📄 Husanboy Scan tayyor PDF",
    )
    return {"ok": True, "chat_id": chat_id, "filename": filename}
