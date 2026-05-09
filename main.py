import os
import logging
import asyncio
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Flask HTTP سرور (د Render لپاره) ---
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host='0.0.0.0', port=port)

# --- لاګونه ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- د بوټ توکین او چټ آي ډي ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8043838519:AAFeFPZ574e4F4kYmXOQMP7let3aSk0qTFQ")
CHAT_ID = os.environ.get("CHAT_ID", "8518408753")

# --- د معلوماتو ذخیره ---
user_warnings = {}
warn_reasons = {}

# --- تڼۍ جوړول ---
def get_welcome_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 زموږ چینل", url="https://t.me/WahidMode")],
        [InlineKeyboardButton("💻 دوهم چینل", url="https://t.me/ProTech43")],
        [InlineKeyboardButton("🔥 دریم چینل", url="https://t.me/Javeed_Tech")],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- چک کول چې کارن اډمین دی ---
async def is_admin(update: Update, user_id: int) -> bool:
    try:
        member = await update.effective_chat.get_member(user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False

# --- چک کول چې سم ګروپ دی ---
async def is_correct_group(update: Update) -> bool:
    if not update.effective_chat:
        return False
    return str(update.effective_chat.id) == CHAT_ID

# ========== د نوي غړي راتګ (د بشپړ معلوماتو او انځور سره) ==========
async def new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_correct_group(update):
        return
    
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
        
        # د کارن معلومات
        user_id = member.id
        username = f"@{member.username}" if member.username else "ندارد"
        first_name = member.first_name
        last_name = member.last_name if member.last_name else ""
        full_name = f"{first_name} {last_name}".strip()
        
        # د ښه راغلاست پیغام (د معلوماتو سره)
        WELCOME_MESSAGE = f"""🐉 **زه د وحید ګروف کنترولر باټ یم!**

✨ **ګروپ ته ښه راغلاست!** ✨

👤 **نوم:** {full_name}
🆔 **آی ډي:** `{user_id}`
📝 **یوزرنیم:** {username}

لاندې تڼۍ کېکاږئ او زموږ چینلونو سره یوځای شئ:

*📌 دا پیغام به د 10 ثانیو وروسته حذف شي*"""
        
        # د کارن پروفایل انځور ترلاسه کول
        try:
            user_photos = await context.bot.get_user_profile_photos(user_id, limit=1)
            if user_photos.total_count > 0:
                photo_file_id = user_photos.photos[0][0].file_id
                # د انځور سره پیغام واستوئ
                sent_message = await update.message.reply_photo(
                    photo=photo_file_id,
                    caption=WELCOME_MESSAGE,
                    parse_mode="Markdown",
                    reply_markup=get_welcome_keyboard()
                )
            else:
                # پرته له انځوره پیغام واستوئ
                sent_message = await update.message.reply_text(
                    WELCOME_MESSAGE,
                    parse_mode="Markdown",
                    reply_markup=get_welcome_keyboard()
                )
        except Exception as e:
            # که انځور ترلاسه نشي، یوازې متن واستوئ
            print(f"د انځور ترلاسه کولو تېروتنه: {e}")
            sent_message = await update.message.reply_text(
                WELCOME_MESSAGE,
                parse_mode="Markdown",
                reply_markup=get_welcome_keyboard()
            )
        
        # د 10 ثانیو وروسته پیغام حذف کړئ
        await asyncio.sleep(10)
        try:
            await sent_message.delete()
            print(f"د {full_name} لپاره د ښه راغلاست پیغام حذف شو")
        except Exception as e:
            print(f"پیغام حذف نشو: {e}")

# ========== د پیل کمانډ ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **زه د وحید ګروف کنترولر باټ یم!**\n\n"
        "د اډمینانو لپاره امرونه:\n"
        "• `/kick` - کارن ویشتئ\n"
        "• `/ban` - کارن بند کړئ\n"
        "• `/unban` - کارن انبان کړئ\n"
        "• `/mute` - کارن خاموش کړئ\n"
        "• `/unmute` - کارن بیداره کړئ\n"
        "• `/warn` - خبرداری ورکړئ\n"
        "• `/reset_warns` - خبرداری له منځه یوسئ\n"
        "• `/info` - معلومات وګورئ\n\n"
        "💡 ټول امرونه د کارن په ریپلای کې وکاروئ!",
        parse_mode="Markdown"
    )

# ========== /kick ==========
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

# ========== /ban ==========
async def ban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_correct_group(update):
        return
    if not await is_admin(update, update.effective_user.id):
        await update.message.reply_text("❌ یوازې اډمینان کولی شي دا امر وکاروي!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ مهرباني وکړئ د یو کارن په ریپلای کې /ban وکاروئ!")
        return
    target = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "هیڅ دلیل نشته"
    try:
        await update.effective_chat.ban_member(target.id)
        await update.message.reply_text(f"✅ {target.first_name} د تل لپاره بند شو!\n📝 دلیل: {reason}")
    except Exception as e:
        await update.message.reply_text(f"❌ تېروتنه: {e}")

# ========== /unban ==========
async def unban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_correct_group(update):
        return
    if not await is_admin(update, update.effective_user.id):
        await update.message.reply_text("❌ یوازې اډمینان کولی شي دا امر وکاروي!")
        return
    if not context.args:
        await update.message.reply_text("⚠️ مهرباني وکړئ د کارن یوزرنیم ورکړئ!\nمثال: /unban @username")
        return
    try:
        username = context.args[0].replace("@", "")
        await update.effective_chat.unban_member(username)
        await update.message.reply_text(f"✅ {username} انبان شو!")
    except Exception as e:
        await update.message.reply_text(f"❌ تېروتنه: {e}")

# ========== /mute ==========
async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_correct_group(update):
        return
    if not await is_admin(update, update.effective_user.id):
        await update.message.reply_text("❌ یوازې اډمینان کولی شي دا امر وکاروي!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ مهرباني وکړئ د یو کارن په ریپلای کې /mute وکاروئ!")
        return
    target = update.message.reply_to_message.from_user
    duration = 10
    if context.args:
        try:
            duration = int(context.args[0])
        except:
            pass
    permissions = ChatPermissions(can_send_messages=False)
    try:
        until_date = datetime.now() + timedelta(minutes=duration)
        await update.effective_chat.restrict_member(target.id, permissions, until_date=until_date)
        await update.message.reply_text(f"🔇 {target.first_name} د {duration} دقیقو لپاره خاموش شو!")
    except Exception as e:
        await update.message.reply_text(f"❌ تېروتنه: {e}")

# ========== /unmute ==========
async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_correct_group(update):
        return
    if not await is_admin(update, update.effective_user.id):
        await update.message.reply_text("❌ یوازې اډمینان کولی شي دا امر وکاروي!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ مهرباني وکړئ د یو کارن په ریپلای کې /unmute وکاروئ!")
        return
    target = update.message.reply_to_message.from_user
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )
    try:
        await update.effective_chat.restrict_member(target.id, permissions)
        await update.message.reply_text(f"🔊 {target.first_name} بیا خبرې کولی شي!")
    except Exception as e:
        await update.message.reply_text(f"❌ تېروتنه: {e}")

# ========== /warn ==========
async def warn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_correct_group(update):
        return
    if not await is_admin(update, update.effective_user.id):
        await update.message.reply_text("❌ یوازې اډمینان کولی شي دا امر وکاروي!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ مهرباني وکړئ د یو کارن په ریپلای کې /warn وکاروئ!")
        return
    target = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "نه دی ورکړل شوی"
    user_warnings[target.id] = user_warnings.get(target.id, 0) + 1
    if target.id not in warn_reasons:
        warn_reasons[target.id] = []
    warn_reasons[target.id].append(reason)
    if user_warnings[target.id] >= 3:
        try:
            await update.effective_chat.ban_member(target.id)
            reasons_list = "\n".join(f"• {r}" for r in warn_reasons[target.id])
            await update.message.reply_text(f"⚠️ {target.first_name} د 3 خبرداریو وروسته بند شو!\nدلیلونه:\n{reasons_list}")
            user_warnings[target.id] = 0
            warn_reasons[target.id] = []
        except Exception as e:
            await update.message.reply_text(f"❌ تېروتنه: {e}")
    else:
        await update.message.reply_text(f"⚠️ {target.first_name} ته خبرداری! ({user_warnings[target.id]}/3)\n📝 دلیل: {reason}")

# ========== /reset_warns ==========
async def reset_warns_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_correct_group(update):
        return
    if not await is_admin(update, update.effective_user.id):
        await update.message.reply_text("❌ یوازې اډمینان کولی شي دا امر وکاروي!")
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ مهرباني وکړئ د یو کارن په ریپلای کې /reset_warns وکاروئ!")
        return
    target = update.message.reply_to_message.from_user
    user_warnings[target.id] = 0
    warn_reasons[target.id] = []
    await update.message.reply_text(f"✅ د {target.first_name} ټول خبرداری له منځه لاړل!")

# ========== /info ==========
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_correct_group(update):
        return
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    else:
        target = update.effective_user
    warnings = user_warnings.get(target.id, 0)
    info_text = f"""📋 **د کارن معلومات**

**نوم:** {target.first_name}
**آی ډي:** `{target.id}`
**یوزرنیم:** @{target.username if target.username else 'ندارد'}
**خبرداری:** {warnings}/3"""
    await update.message.reply_text(info_text, parse_mode="Markdown")

# ========== د بوټ پیلول ==========
async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()
    await app.bot.delete_webhook(drop_pending_updates=True)
    print("✅ Webhook پاک شو!")
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("kick", kick_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("unban", unban_command))
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("unmute", unmute_command))
    app.add_handler(CommandHandler("warn", warn_command))
    app.add_handler(CommandHandler("reset_warns", reset_warns_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_handler))
    
    print("🚀 بوټ روان دی...")
    await app.run_polling()

# ========== د پروګرام پیل ==========
if __name__ == "__main__":
    # په جلا تار کې Flask پیل کړئ (د Render لپاره)
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    
    # بوټ پیل کړئ
    asyncio.run(run_bot())
