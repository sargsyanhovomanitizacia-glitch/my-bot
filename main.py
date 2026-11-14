import os
import asyncio
import logging
import sys
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

# 📌 ՎԻԴԵՈՆ ՀԱՎԵՐԺ ԳՐՎԱԾ Է ԱՅՍՏԵՂ
MEDIA_STORAGE = [
    {
        'type': 'video', 
        'file_id': 'BAACAgIAAxkBAAIBUmr33Hx4yzjT_1P_luDi8-tIV1gAALjG2sbQwzASwLDFzrb9AhzAQADAgADaADPQQ', 
        'caption': 'Սերիա 1'
    }
]

async def check_subscription(user_id: int, bot: Bot) -> bool:
    if user_id == ADMIN_ID:
        return True
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        # Ստուգում ենք, որ մարդը իրոք ալիքի անդամ է (չի լքել այն)
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            return True
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
    return False

async def send_media_to_user(target_chat_id: int, bot: Bot):
    await bot.send_message(target_chat_id, "✅ Բարի գալուստ! Ահա քեզ հասանելի նյութերը:")
    for media in MEDIA_STORAGE:
        try:
            if media['type'] == 'video':
                await bot.send_video(target_chat_id, media['file_id'], caption=media.get('caption', ''))
            elif media['type'] == 'photo':
                await bot.send_photo(target_chat_id, media['file_id'], caption=media.get('caption', ''))
            await asyncio.sleep(0.3)
        except Exception as e:
            logging.error(f"Send media error: {e}")

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    
    # 📌 ԱՄԵՆ ԱՆԳԱՄ ՍՏՈՒԳՈՒՄ ԵՆՔ՝ ԻՐՈ՞Ք ԱԼԻՔՈՒՄ Է, ԹԵ ԽԱԲՈՒՄ Է
    is_subscribed = await check_subscription(user_id, bot)
    
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Միանալ ալիքին", url="https://t.me/canabisee")],
                [InlineKeyboardButton(text="🔄 Ստուգել բաժանորդագրությունը", callback_data="check_sub")]
            ]
        )
        await message.answer(
            "❌ **Խաբել չի ստացվի! Բոտից օգտվելու համար պետք է անպայման լինես մեր ալիքի անդամ:**\n\nՆախ միացիր ալիքին, հետո սեղմիր «Ստուգել բաժանորդագրությունը»։",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await send_media_to_user(message.chat.id, bot)

@router.callback_query(F.data == "check_sub")
async def process_check_sub(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    
    # 📌 ԿՈՃԱԿԻ ՎՐԱ ՍԵՂՄԵԼԻՍ ԵԼՍ ՍՏՈՒԳՈՒՄ ԵՆՔ
    is_subscribed = await check_subscription(user_id, bot)
    
    if is_subscribed:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await send_media_to_user(callback.message.chat.id, bot)
    else:
        await callback.answer("❌ Դու դեռ դուրս եկել ալիքից կամ միացած չես: Անպայման միացիր ալիքին, որ բոտը բացվի։", show_alert=True)

@router.message(F.from_user.id == ADMIN_ID)
async def admin_upload_media(message: Message, bot: Bot):
    if message.video or message.photo:
        fid = message.video.file_id if message.video else message.photo[-1].file_id
        await message.answer(f"💾 Ադմին, ֆայլը հաստատված է:\n`{fid}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.answer("Ախպեր ջան, բոտը հսկում է ալիքը:")

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
            asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
    
