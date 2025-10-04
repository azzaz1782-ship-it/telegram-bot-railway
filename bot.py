#!/usr/bin/env python3
import os
import logging
from datetime import datetime
import threading
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    ConversationHandler, filters
)

EXCEL_FILE = "registrations.xlsx"
LOGFILE = "bot.log"
CATEGORIES = ["الأولى", "الانِيـة", "الثالثة", "الرابعة"]
(CHAIR_NAME, CHAIR_CATEGORY, CHAIR_PARTNER, LOCKER_NAME,
 LOCKER_CATEGORY, LOCKER_PARTNER1, LOCKER_PARTNER2) = range(7)

file_lock = threading.Lock()
logging.basicConfig(filename=LOGFILE, level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def _ensure_excel_exists():
    if not os.path.exists(EXCEL_FILE):
        pd.DataFrame(columns=[
            "timestamp", "type", "registrant", "category", "partner1", "partner2"
        ]).to_excel(EXCEL_FILE, index=False)

def save_row(row: dict):
    _ensure_excel_exists()
    with file_lock:
        try:
            df_existing = pd.read_excel(EXCEL_FILE)
        except Exception:
            df_existing = pd.DataFrame(columns=[
                "timestamp", "type", "registrant", "category", "partner1", "partner2"
            ])
        df_new = pd.DataFrame([row])
        df_all = pd.concat([df_existing, df_new], ignore_index=True)
        df_all.to_excel(EXCEL_FILE, index=False)
        logger.info("Saved row: %s", row)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["توزيع الكراسي", "توزيع الخزنات"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("أهلاً! اختر العملية التي تريدها:", reply_markup=reply_markup)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("تم الإلغاء.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def chair_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أكتب اسمك (اسم المسجل) ثم أرسل:", reply_markup=ReplyKeyboardRemove())
    return CHAIR_NAME

async def chair_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["chair_registrant"] = name
    kb = [[c] for c in CATEGORIES]
    reply = ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("اختر الفئة:", reply_markup=reply)
    return CHAIR_CATEGORY

async def chair_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = update.message.text.strip()
    if cat not in CATEGORIES:
        await update.message.reply_text("الرجاء اختيار فئة من الأزرار الظاهرة.")
        return CHAIR_CATEGORY
    context.user_data["chair_category"] = cat
    await update.message.reply_text("اكتب اسم الطالب الذي سيشاركك الكرسي:")
    return CHAIR_PARTNER

async def chair_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    partner = update.message.text.strip()
    registrant = context.user_data.get("chair_registrant", "")
    category = context.user_data.get("chair_category", "")
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "chair",
        "registrant": registrant,
        "category": category,
        "partner1": partner,
        "partner2": "",
    }
    try:
        save_row(row)
        await update.message.reply_text(
            f"تم تسجيل الطالبين:\n- {registrant}\n- {partner}\nتم تسجيلهما على الكرسي.",
            reply_markup=ReplyKeyboardRemove())
    except Exception as e:
        logger.exception("Error saving chair registration")
        await update.message.reply_text("حصل خطأ أثناء حفظ البيانات. حاول لاحقاً.")
    context.user_data.clear()
    return ConversationHandler.END

async def locker_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أكتب اسمك (اسم المسجل) ثم أرسل:", reply_markup=ReplyKeyboardRemove())
    return LOCKER_NAME

async def locker_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["locker_registrant"] = name
    kb = [[c] for c in CATEGORIES]
    reply = ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("اختر الفئة:", reply_markup=reply)
    return LOCKER_CATEGORY

async def locker_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cat = update.message.text.strip()
    if cat not in CATEGORIES:
        await update.message.reply_text("الرجاء اختيار فئة من الأزرار الظاهرة.")
        return LOCKER_CATEGORY
    context.user_data["locker_category"] = cat
    await update.message.reply_text("اكتب اسم الطالب الأول الذي سيشاركك الخزانة:")
    return LOCKER_PARTNER1

async def locker_partner1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p1 = update.message.text.strip()
    context.user_data["locker_partner1"] = p1
    await update.message.reply_text("اكتب اسم الطالب الثاني الذي سيشاركك الخزانة:")
    return LOCKER_PARTNER2

async def locker_partner2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p2 = update.message.text.strip()
    registrant = context.user_data.get("locker_registrant", "")
    category = context.user_data.get("locker_category", "")
    p1 = context.user_data.get("locker_partner1", "")
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": "locker",
        "registrant": registrant,
        "category": category,
        "partner1": p1,
        "partner2": p2,
    }
    try:
        save_row(row)
        await update.message.reply_text(
            f"تم تسجيل الطلاب:\n- {registrant}\n- {p1}\n- {p2}\nتم تسجيلهم على الخزانة.",
            reply_markup=ReplyKeyboardRemove())
    except Exception:
        logger.exception("Error saving locker registration")
        await update.message.reply_text("حصل خطأ أثناء حفظ البيانات. حاول لاحقاً.")
    context.user_data.clear()
    return ConversationHandler.END

async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "توزيع الكراسي":
        return await chair_start(update, context)
    elif text == "توزيع الخزنات":
        return await locker_start(update, context)
    else:
        kb = [["توزيع الكراسي", "توزيع الخزنات"]]
        await update.message.reply_text("اختر العملية من الأزرار:",
            reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True))
        return ConversationHandler.END

def build_app():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("Please set TELEGRAM_TOKEN environment variable.")
    app = ApplicationBuilder().token(token).build()
    chair_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^توزيع الكراسي$"), chair_start)],
        states={
            CHAIR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, chair_name)],
            CHAIR_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, chair_category)],
            CHAIR_PARTNER: [MessageHandler(filters.TEXT & ~filters.COMMAND, chair_partner)],
        }, fallbacks=[CommandHandler("cancel", cancel)], allow_reentry=True)
    locker_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^توزيع الخزنات$"), locker_start)],
        states={
            LOCKER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, locker_name)],
            LOCKER_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, locker_category)],
            LOCKER_PARTNER1: [MessageHandler(filters.TEXT & ~filters.COMMAND, locker_partner1)],
            LOCKER_PARTNER2: [MessageHandler(filters.TEXT & ~filters.COMMAND, locker_partner2)],
        }, fallbacks=[CommandHandler("cancel", cancel)], allow_reentry=True)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(chair_conv)
    app.add_handler(locker_conv)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_router))
    return app

if __name__ == "__main__":
    _ensure_excel_exists()
    app = build_app()
    logger.info("Bot starting on Railway...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
