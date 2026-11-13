import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ChatMemberStatus
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

TOKEN = os.getenv("BOT_TOKEN", "9197794771:AAFzNqdHgkpF86BPdTE_S01dyBfpmm_c")
CHANNEL_ID = -1006199289062  # Ալիքի ID-ն
ADMIN_ID = 123456789  # <--- ԱՅՍՏԵՂ ԳՐԻՐ ՔՈ TELEGRAM-Ի ԹՎԱՅԻՆ ID-Ն (օրինակ՝ 123456789)

router = Router()

# Այստեղ կհավաքվեն քո ուղարկած նյութերը
MEDIA_STORAGE = []

async def check_subscription(user_id: int, bot: Bot) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
            return True
    except Exception:
        pass
    return False

# Բոտի սկիզբը (/start)
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
            "❌ **Բոտից օգտվելու և նյութերը դիտելու համար պետք է բաժանորդագրվես մեր ալիքին:**\n\nԲաժանորդագրվիր ու սեղմիր «Ստուգել բաժանորդագրությունը» կոճակը։",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await send_all_media(message)

# Նյութերը օգտատիրոջն ուղարկելու ֆունկցիա
async def send_all_media(target_message):
    if not MEDIA_STORAGE:
        await target_message.answer("✅ Բարի գալուստ! Դու արդեն բաժանորդագրված ես։ Առայժմ նոր նյութեր չկան։")
        return
    
    await target_message.answer("✅ Բարի գալուստ! Ահա քեզ հասանելի նյութերը:")
    for media in MEDIA_STORAGE:
        if media['type'] == 'video':
            await target_message.answer_video(media['file_id'], caption=media.get('caption', ''))
        elif media['type'] == 'photo':
            await target_message.answer_photo(media['file_id'], caption=media.get('caption', ''))

# Բաժանորդագրության ստուգման կոճակը
@router.callback_query(F.data == "check_sub")
async def process_check_sub(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id, bot)
    
    if is_subscribed:
        await callback.message.delete()
        if not MEDIA_STORAGE:
            await callback.message.answer("✅ **Շնորհավորում եմ!** Դու հաջողությամբ միացար ալիքին:\n\nԱռայժմ նյութեր չկան:")
        else:
            await callback.message.answer("✅ **Շնորհավորում եմ!** Դու հաջողությամբ միացար ալիքին: Ահա նյութերը:")
            for media in MEDIA_STORAGE:
                if media['type'] == 'video':
                    await callback.message.answer_video(media['file_id'], caption=media.get('caption', ''))
                elif media['type'] == 'photo':
                    await callback.message.answer_photo(media['file_id'], caption=media.get('caption', ''))
    else:
        await callback.answer("❌ Դու դեռ չես միացել ալիքին: Խնդրում ենք նախ միանալ, հետո սեղմել կրկին։", show_alert=True)

# ՄԻԱՅՆ ԱԴՄԻՆԻ ՀԱՄԱՐ. Երբ դու վիդեո կամ նկար ես ուղարկում բոտին
@router.message(F.from_user.id == ADMIN_ID)
async def admin_upload_media(message: Message):
    if message.video:
        MEDIA_STORAGE.append({'type': 'video', 'file_id': message.video.file_id, 'caption': message.caption})
        await message.answer("💾 Վիդեոն հաջողությամբ ավելացվեց բոտի բազա և հասանելի կլինի բոլորին!")
    elif message.photo:
        MEDIA_STORAGE.append({'type': 'photo', 'file_id': message.photo[-1].file_id, 'caption': message.caption})
        await message.answer("💾 Նկարը հաջողությամբ ավելացվեց բոտի բազա և հասանելի կլինի բոլորին!")
    else:
        await message.answer("Ախպեր ջան, միայն վիդեո կամ նկար ուղարկիր, որ պահպանեմ։")

async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    
    while True:
        try:
            logging.info("Բոտը միանում է...")
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Գրանցվել է սխալ: {e}. Վերագործարկում 5 վայրկյանից...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout if 'sys' in globals() else None)
    import sys
    asyncio.run(main())
    
