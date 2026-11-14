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
CHANNEL_ID = "@canabisee"
ADMIN_ID = 6199289062  # <--- ՔՈ ՃԻՇՏ ID-Ն

router = Router()
DB_FILE = "media_data.json"
USERS_FILE = "users_data.json"

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

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_users(users_list):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users_list, f, ensure_ascii=False, indent=4)
    except Exception as e:
        pass

def add_user(user_id):
    users = load_users()
    if user_id not in users and user_id != ADMIN_ID:
        users.append(user_id)
        save_users(users)

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

async def send_media_to_user(target_chat_id: int, bot: Bot):
    media_storage = load_media()
    if not media_storage:
        await bot.send_message(target_chat_id, "✅ Բարի գալուստ! Բայց առայժմ նյութեր չկան:")
        return
    
    await bot.send_message(target_chat_id, "✅ Բարի գալուստ! Ահա քեզ հասանելի նյութերը:")
    
    for media in media_storage:
        try:
            chat_id = target_chat_id
            from_chat_id = ADMIN_ID
            message_id = media['sent_message_ids'].get(str(target_chat_id))
            
            if media['type'] == 'video':
                sent = await bot.send_video(chat_id, media['file_id'], caption=media.get('caption', ''))
            elif media['type'] == 'photo':
                sent = await bot.send_photo(chat_id, media['file_id'], caption=media.get('caption', ''))
            else:
                sent = await bot.send_message(chat_id, media.get('text', ''))
                
            # Հիշում ենք ուղարկված հաղորդագրության ID-ն, որ հետո հեշտ ջնջվի
            media['sent_message_ids'][str(target_chat_id)] = sent.message_id
            await asyncio.sleep(0.3)
        except Exception as e:
            logging.error(f"Send media error: {e}")
    save_media(media_storage)

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    add_user(user_id)
    
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
        await send_media_to_user(message.chat.id, bot)

@router.callback_query(F.data == "check_sub")
async def process_check_sub(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    add_user(user_id)
    is_subscribed = await check_subscription(user_id, bot)
    
    if is_subscribed:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await send_media_to_user(callback.message.chat.id, bot)
    else:
        await callback.answer("❌ Դու դեռ չես միացել ալիքին: Նախ միացիր, հետո սեղմիր կրկին։", show_alert=True)

# Երբ ադմինը ջնջում է հաղորդագրությունը իր մոտ, բոտը ջնջում է այն բոլորի մոտից
@router.edited_message(F.from_user.id == ADMIN_ID)
async def admin_edited_message(message: Message, bot: Bot):
    pass

@router.message(F.from_user.id == ADMIN_ID)
async def admin_upload_media(message: Message, bot: Bot):
    media_storage = load_media()
    users = load_users()
    
    sent_ids = {}
    media_type = 'text'
    file_id = None
    caption = message.caption or message.text or ''
    
    if message.video:
        media_type = 'video'
        file_id = message.video.file_id
    elif message.photo:
        media_type = 'photo'
        file_id = message.photo[-1].file_id
    else:
        media_type = 'text'

    await message.answer("💾 Հրապարակվում է և ուղարկվում բոլորին...")

    for uid in users:
        try:
            if media_type == 'video':
                sent = await bot.send_video(uid, file_id, caption=caption)
            elif media_type == 'photo':
                sent = await bot.send_photo(uid, file_id, caption=caption)
            else:
                sent = await bot.send_message(uid, caption)
            
            sent_ids[str(uid)] = sent.message_id
            await asyncio.sleep(0.3)
        except Exception as e:
            logging.error(f"Broadcast error for {uid}: {e}")

    media_data = {
        'type': media_type,
        'file_id': file_id,
        'text': caption if media_type == 'text' else '',
        'caption': caption if media_type != 'text' else '',
        'sent_message_ids': sent_ids,
        'admin_msg_id': message.message_id
    }
    media_storage.append(media_data)
    save_media(media_storage)
    
    await message.answer("🚀 Հաջողությամբ ուղարկվեց բոլորին!")

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
        
