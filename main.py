import os
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# لاګونه
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# د بوټ توکین او چټ آي ډي
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8043838519:AAFeFPZ574e4F4kYmXOQMP7let3aSk0qTFQ")
CHAT_ID = os.environ.get("CHAT_ID", "8518408753")

# د معلوماتو ذخیره
user_warnings = {}
warn_reasons = {}

# د ښه راغلاست پیغام
WELCOME_MESSAGE = """🐉 زه د وحید ګروف کنترولر باټ یم!

ګروپ ته ښه راغلاست! 🎉

لاندې تڼۍ کېکاږئ او زموږ چینلونو سره یوځای شئ:"""

def get_welcome_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 زموږ چینل", url="https://t.me/WahidMode")],
        [InlineKeyboardButton("💻 دوهم چینل", url="https://t.me/ProTech43")],
        [InlineKeyboardButton("🔥 دریم چینل", url="https://t.me/Javeed_Tech")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def is_admin(update: Update, user_id: int) -> bool:
    try:
        member = await update.effective_chat.get_member(user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

async def is_correct_group(update: Update) -> bool:
    if not update.effective_chat:
        return False
    return str(update.effective_chat.id) == CHAT_ID

# نوی غړی
async def new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_correct_group(update):
        return
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
        await update.message.reply_text(
            WELCOME_MESSAGE,
            parse_mode="Markdown",
            reply_markup=get_welcome_keyboard()
        )

# /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 زه د وحید ګروف کنترولر باټ یم!\n\n"
        "د اډمینانو لپاره امرونه:\n"
        "• /kick - کارن ویشتئ\n"
        "• /ban - کارن بند کړئ\n"
        "• /unban - کارن انبان کړئ\n"
        "• /mute - کارن خاموش کړئ\n"
        "• /unmute - کارن بیداره کړئ\n"
        "• /warn - خبرداری ورکړئ\n"
        "• /reset_warns - خبرداری له منځه یوسئ\n"
        "• /info - معلومات وګورئ\n\n"
        "💡 ټول امرونه د کارن په ریپلای کې وکاروئ!",
        parse_mode="Markdown"
    )

# /kick
async def kick_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_correct_group(update):
        return
    if not await is_admin(update, update.effective_user.id):
        await update.message.reply_text("❌ یوازې اډمینان کولی شي دا امر وکاروي!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ مهرباني وکړئ د یو کارن په ریپلای کې /kick وکاروئ!")
        return
    target = update.message.reply_to_message.from_user
    if target.id == context.bot.id:
        await update.message.reply_text("😅 زه نه شم ځان تښتولی!")
        return
    try:
        await update.effective_chat.ban_member(target.id)
        await update.effective_chat.unban_member(target.id)
        await update.message.reply_text(f"✅ {target.first_name} له ګروپ څخه وویستل شو!")
    except Exception as e:
        await update.message.reply_text(f"❌ تېروتنه: {e}")

# /ban
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_correct_group(update):
        return
    if not await is_admin(update, update.effective_user.id):
        await update.message.reply_text("❌ یوازې اډمینان کولی شي دا امر وکاروي!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ مهرباني وکړئ د یو کارن په ریپلای کې /ban وکاروئ!")