import os
import asyncio
import logging
import sys
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

TOKEN = os.getenv("BOT_TOKEN", "9197794771:AAFzNqdHgkpF86BPdTE_S01dyBfpmm_c")
CHANNEL_ID = "@canabisee"  # <--- Ալիքի անունը ուղղակի այսպես
ADMIN_ID = 6199289062    # <--- ՔՈ ՃԻՇՏ ID-Ն

router = Router()
DB_FILE = "media_data.json"

def load_media():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_media(media_list):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(media_list, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Save error: {e}")

async def check_subscription(user_id: int, bot: Bot) -> bool:
    if user_id == ADMIN_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            return True
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
    return False

async def send_media_to_user(target):
    media_storage = load_media()
    if not media_storage:
        await target.answer("✅ Բարի գալուստ! Բայց առայժմ նյութեր չկան:")
        return
    
    await target.answer("✅ Բարի գալուստ! Ահա քեզ հասանելի նյութերը:")
    for media in media_storage:
        if media['type'] == 'video':
            await target.answer_video(media['file_id'], caption=media.get('caption', ''))
        elif media['type'] == 'photo':
            await target.answer_photo(media['file_id'], caption=media.get('caption', ''))

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id, bot)
    
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Միանալ ալիքին", url="https://t.me/canabisee")],
                [InlineKeyboardButton(text="🔄 Ստուգել բաժանորդագրությունը", callback_data="check_sub")]
            ]
        )
        await message.answer(
            "❌ **Բոտից օգտվելու համար պետք է բաժանորդագրվես մեր ալիքին:**\n\nԲաժանորդագրվիր ու սեղմիր «Ստուգել բաժանորդագրությունը» կոճակը։",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await send_media_to_user(message)

@router.callback_query(F.data == "check_sub")
async def process_check_sub(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id, bot)
    
    if is_subscribed:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await send_media_to_user(callback.message)
    else:
        await callback.answer("❌ Դու դեռ չես միացել ալիքին: Նախ միացիր, հետո սեղմիր կրկին։", show_alert=True)

@router.message(F.from_user.id == ADMIN_ID)
async def admin_upload_media(message: Message):
    media_storage = load_media()
    if message.video:
        media_storage.append({'type': 'video', 'file_id': message.video.file_id, 'caption': message.caption})
        save_media(media_storage)
        await message.answer("💾 Վիդեոն հաջողությամբ պահպանվեց և հասանելի դարձավ բոլորին!")
    elif message.photo:
        media_storage.append({'type': 'photo', 'file_id': message.photo[-1].file_id, 'caption': message.caption})
        save_media(media_storage)
        await message.answer("💾 Նկարը հաջողությամբ պահպանվեց և հասանելի դարձավ բոլորին!")
    else:
        await message.answer("Ախպեր ջան, միայն նկար կամ վիդեո ուղարկիր:")

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
    
    while True:
        try:
            logging.info("Բոտը միանում է...")
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Error: {e}. Վերագործարկում 5 վայրկյանից...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
    
