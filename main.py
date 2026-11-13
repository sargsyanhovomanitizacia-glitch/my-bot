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
CHANNEL_ID = "@canabisee"  # <--- Ճիշտ ալիքի username-ը

router = Router()

async def check_subscription(user_id: int, bot: Bot) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
            return True
    except Exception:
        pass
    return False

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    is_subscribed = await check_subscription(user_id, bot)
    
    if not is_subscribed:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📢 Միանալ ալիքին", url=f"https://t.me/{CHANNEL_ID.replace('@', '')}")],
                [InlineKeyboardButton(text="🔄 Ստուգել բաժանորդագրությունը", callback_data="check_sub")]
            ]
        )
        await message.answer(
            "❌ **Բոտից օգտվելու և նյութերը դիտելու համար պետք է բաժանորդագրվես մեր ալիքին:**\n\nԲաժանորդագրվիր ու սեղմիր «Ստուգել բաժանորդագրությունը» կոճակը։",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await message.answer("✅ Բարի գալուստ! Դու արդեն բաժանորդագրված ես։ Ուղարկիր կամ ընտրիր քեզ հետաքրքրող նյութը:")

@router.callback_query(F.data == "check_sub")
async def process_check_sub(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    is_subscribed = await check_subscription(user_id, bot)
    
    if is_subscribed:
        await callback.message.edit_text(
            "✅ **Շնորհավորում եմ!** Դու հաջողությամբ միացար ալիքին:\n\nՀիմա կարող ես անարգել օգտվել բոտից:",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await callback.answer("❌ Դու դեռ չես միացել ալիքին: Խնդրում ենք նախ միանալ, հետո սեղմել կրկին։", show_alert=True)

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
    
