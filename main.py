import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

TOKEN = "9197794771:AAFxNqdHgkpF86BPdTE_SO1dyBfpmm_dF4U"

async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    @dp.message(CommandStart())
    async def command_start_handler(message: Message) -> None:
        await message.answer(f"Բարև, {html.bold(message.from_user.full_name)}! Բոտն հաջողությամբ միացված է և աշխատում է 24/7 ռեժիմով։")

    while True:
        try:
            logging.info("Բոտը միանում է...")
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Գրանցվել է սխալ: {e}. Վերամիացում 5 վայրկյանից...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
  
