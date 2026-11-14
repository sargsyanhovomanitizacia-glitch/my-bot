import os
import asyncio
import logging
import sys
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.client.default import DefaultBotProperties

# ==========================================
# ⚙️ ՀԻՄՆԱԿԱՆ ԿԱՐԳԱՎՈՐՈՒՄՆԵՐ
# ==========================================
TOKEN = os.getenv("BOT_TOKEN", "9197794771:AAFzNqdHgkpF86BPdTE_S01dyBfpmm_c")
CHANNEL_ID = "@canabisee"
CHANNEL_URL = "https://t.me/canabisee"
ADMIN_ID = 6199289062

router = Router()
USERS_FILE = "users_db.json"

# ==========================================
# 🎬 ՀԱՎԵՐԺ ՊԱՀՊԱՆՎՈՂ ՆՅՈՒԹԵՐ
# ==========================================
MEDIA_STORAGE = [
    {
        'type': 'video',
        'file_id': 'BAACAgIAAxkBAAIBUmr33Hx4yzjT_1P_luDi8-tIV1gAALjG2sbQwzASwLDFzrb9AhzAQADAgADaADPQQ',
        'caption': '🔥 **Վերջին Գամբիթ — Սերիա 1**\n\nԲարի դիտում ախպերներ ջան!'
    }
]

# ==========================================
# 💾 ԲԱԶԱՅԻ ՖՈՒՆԿՑԻԱՆԵՐ
# ==========================================
def load_users() -> list:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_users(users: list):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Save error: {e}")

def register_user(user_id: int):
    if user_id == ADMIN_ID:
        return
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

# ==========================================
# 🛡️ ՍՏՈՒԳՄԱՆ ՀԱՄԱԿԱՐԳ (ANTI-CHEAT)
# ==========================================
async def is_user_subscribed(user_id: int, bot: Bot) -> bool:
    if user_id == ADMIN_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        ]
    except Exception as e:
        logging.error(f"Sub check error: {e}")
        return False

def get_sub_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Միանալ ալիքին", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="🔄 Ստուգել բաժանորդագրությունը", callback_data="verify_sub")]
        ]
    )

async def send_all_media(chat_id: int, bot: Bot):
    await bot.send_message(chat_id, "✅ **Բարի գալուստ! Ահա քեզ հասանելի նյութերը:**", parse_mode=ParseMode.MARKDOWN)
    for media in MEDIA_STORAGE:
        try:
            if media['type'] == 'video':
                await bot.send_video(
                    chat_id, 
                    media['file_id'], 
                    caption=media['caption'], 
                    parse_mode=ParseMode.MARKDOWN, 
                    protect_content=True
                )
            elif media['type'] == 'photo':
                await bot.send_photo(
                    chat_id, 
                    media['file_id'], 
                    caption=media['caption'], 
                    parse_mode=ParseMode.MARKDOWN, 
                    protect_content=True
                )
            await asyncio.sleep(0.3)
        except Exception as e:
            logging.error(f"Send media error: {e}")

# ==========================================
# 🚀 ՕԳՏԱՏԵՐԵՐԻ ՄՈՒՏՔ ԵՎ ՍՏՈՒԳՈՒՄ
# ==========================================
@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    register_user(user_id)

    if not await is_user_subscribed(user_id, bot):
        await message.answer(
            "❌ **Խաբել չի ստացվի! Բոտից օգտվելու համար պետք է անպայման լինես մեր ալիքի անդամ:**\n\n"
            "Նախ միացիր ալիքին, հետո սեղմիր «Ստուգել բաժանորդագրությունը»։",
            reply_markup=get_sub_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    await send_all_media(message.chat.id, bot)

@router.callback_query(F.data == "verify_sub")
async def callback_verify_sub(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    register_user(user_id)

    if await is_user_subscribed(user_id, bot):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await send_all_media(callback.message.chat.id, bot)
    else:
        await callback.answer(
            "❌ Դու դեռ դուրս ես եկել ալիքից կամ միացած չես: Անպայման միացիր ալիքին!",
            show_alert=True
        )

# ==========================================
# 👑 ԱԴՄԻՆԻ ԱՆԳԱՄԻՑ ՈՒՂԱՐԿՄԱՆ ՀԱՄԱԿԱՐԳ (BROADCAST)
# ==========================================
@router.message(F.from_user.id == ADMIN_ID)
async def admin_broadcast(message: Message, bot: Bot):
    users = load_users()
    media_type = "text"
    fid = None
    caption = message.caption or message.text or ""

    if message.video:
        media_type = "video"
        fid = message.video.file_id
    elif message.photo:
        media_type = "photo"
        fid = message.photo[-1].file_id

    status_msg = await message.answer(f"⏳ Հրապարակվում է... (Բազայում կա {len(users)} հոգի)")

    sent_count = 0
    skipped_unsub = 0

    for uid in users:
        if not await is_user_subscribed(uid, bot):
            skipped_unsub += 1
            continue

        try:
            if media_type == "video":
                await bot.send_video(uid, fid, caption=caption, protect_content=True)
            elif media_type == "photo":
                await bot.send_photo(uid, fid, caption=caption, protect_content=True)
            else:
                await bot.send_message(uid, caption)
            sent_count += 1
            await asyncio.sleep(0.2)
        except Exception:
            pass

    report = (
        f"✅ **Հրապարակումն ավարտվեց!**\n\n"
        f"📨 Հասավ (ակտիվ բաժանորդների)՝ **{sent_count}** հոգու\n"
        f"🚫 Արգելափակվեց (ալիքից դուրս եկածներ)՝ **{skipped_unsub}** հոգի\n"
    )
    if fid:
        report += f"\n🔑 **Ֆայլի ID (կոդում ավելացնելու համար)՝**\n`{fid}`"

    await status_msg.edit_text(report, parse_mode=ParseMode.MARKDOWN)

# ==========================================
# 🌐 24/7 ՍԵՐՎԵՐ (RENDER)
# ==========================================
async def handle(request):
    return web.Response(text="Bot is running 24/7!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    
    await web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    
    while True:
        try:
            logging.info("Բոտը միանում է...")
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Error: {e}. Վերագործարկում 5 վայրկյանից...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
    
