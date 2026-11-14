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
# 🎬 ՄԵԴԻԱ ԲԱԶԱ (Հավերժ պահպանվող սերիաներ)
# ==========================================
MEDIA_STORAGE = [
    {
        'id': 'ep_1',
        'title': '🎬 Սերիա 1',
        'type': 'video',
        'file_id': 'BAACAgIAAxkBAAIBUmr33Hx4yzjT_1P_luDi8-tIV1gAALjG2sbQwzASwLDFzrb9AhzAQADAgADaADPQQ',
        'caption': '🔥 **Վերջին Գամբիթ — Սերիա 1**\n\nԲարի դիտում ախպերներ ջան։ Մի մոռացեք կիսվել ալիքով 👉 @canabisee'
    }
]

# ==========================================
# 💾 ՕԳՏԱՏԵՐԵՐԻ ԲԱԶԱ
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
        logging.error(f"Users save error: {e}")

def register_user(user_id: int):
    if user_id == ADMIN_ID:
        return
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

# ==========================================
# 🛡️ ՀԱԿԱԽԱԲԵԱԿԱՆ ՍՏՈՒԳՈՒՄ
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
        logging.error(f"Sub check failed for {user_id}: {e}")
        return False

def get_sub_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Միանալ ալիքին (@canabisee)", url=CHANNEL_URL)],
            [InlineKeyboardButton(text="✅ Ստուգել բաժանորդագրությունը", callback_data="verify_sub")]
        ]
    )

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for item in MEDIA_STORAGE:
        buttons.append([InlineKeyboardButton(text=item['title'], callback_data=f"watch_{item['id']}")])
    
    buttons.append([InlineKeyboardButton(text="🎬 Դիտել բոլորը միանգամից", callback_data="watch_all")])
    buttons.append([InlineKeyboardButton(text="📢 Մեր պաշտոնական ալիքը", url=CHANNEL_URL)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_media_item(chat_id: int, item: dict, bot: Bot):
    # protect_content=True -> պաշտպանում է գողանալուց / forward անելուց
    try:
        if item['type'] == 'video':
            await bot.send_video(chat_id, item['file_id'], caption=item['caption'], parse_mode=ParseMode.MARKDOWN, protect_content=True)
        elif item['type'] == 'photo':
            await bot.send_photo(chat_id, item['file_id'], caption=item['caption'], parse_mode=ParseMode.MARKDOWN, protect_content=True)
    except Exception as e:
        logging.error(f"Send error: {e}")

# ==========================================
# 🚀 ՀՐԱՄԱՆՆԵՐ ԵՎ ՄԵՆՅՈՒ
# ==========================================
@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    register_user(user_id)

    if not await is_user_subscribed(user_id, bot):
        await message.answer(
            "⛔ **Մուտքն արգելված է!**\n\n"
            "Բոտից օգտվելու և սերիաները դիտելու համար պետք է պարտադիր բաժանորդագրվես մեր ալիքին։\n"
            "👇 Միացիր ալիքին և սեղմիր ներքևի կոճակը.",
            reply_markup=get_sub_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Անմիջապես բերում ենք ողջույնը, մենյուն և միանգամից առաջին սերիան
    await message.answer(
        f"👋 Բարի գալուստ, **{message.from_user.first_name}**!\n\n"
        "Ահա քեզ հասանելի նյութերը 👇",
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    for item in MEDIA_STORAGE:
        await send_media_item(message.chat.id, item, bot)
        await asyncio.sleep(0.3)

@router.callback_query(F.data == "verify_sub")
async def callback_verify_sub(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    register_user(user_id)

    if await is_user_subscribed(user_id, bot):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            "✅ **Բաժանորդագրությունը հաստատված է!**\n\n"
            "Ահա քեզ հասանելի նյութերը 👇",
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        for item in MEDIA_STORAGE:
            await send_media_item(callback.message.chat.id, item, bot)
            await asyncio.sleep(0.3)
    else:
        await callback.answer(
            "❌ Դու դեռ չես միացել ալիքին կամ դուրս ես եկել։ Նախ միացիր @canabisee-ին!",
            show_alert=True
        )

# ==========================================
# 🎥 ԿՈՃԱԿՆԵՐՈՎ ԴԻՏՈՒՄ ԵՎ ԱՆՏԻ-ՉԻԹ
# ==========================================
@router.callback_query(F.data.startswith("watch_"))
async def callback_watch_media(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    if not await is_user_subscribed(user_id, bot):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(
            "❌ **Խաբել չի ստացվի!** Դու դուրս ես եկել ալիքից։\n"
            "Նորից միացիր ալիքին, որ կարողանաս շարունակել դիտումը 👇",
            reply_markup=get_sub_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    action = callback.data.replace("watch_", "")
    await callback.answer("⏳ Ուղարկվում է...")

    if action == "all":
        for item in MEDIA_STORAGE:
            await send_media_item(callback.message.chat.id, item, bot)
            await asyncio.sleep(0.3)
    else:
        for item in MEDIA_STORAGE:
            if item['id'] == action:
                await send_media_item(callback.message.chat.id, item, bot)
                break

# ==========================================
# 👑 ԱԴՄԻՆԻ ՎԱՀԱՆԱԿ ԵՎ ԲՐՈԱԴՔԱՍԹ
# ==========================================
@router.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def cmd_admin(message: Message):
    users = load_users()
    await message.answer(
        f"👑 **Ադմինի Կառավարման Վահանակ**\n\n"
        f"👥 Գրանցված օգտատերեր՝ **{len(users)}** հոգի\n"
        f"🎬 Ակտիվ սերիաներ կոդում՝ **{len(MEDIA_STORAGE)}** հատ\n\n"
        "📌 *Հուշում.* Ուղարկիր ինձ ցանկացած վիդեո կամ նկար, և ես այն անմիջապես կուղարկեմ բոլոր ակտիվ բաժանորդներին ու կտամ դրա ֆայլի ID-ն։",
        parse_mode=ParseMode.MARKDOWN
    )

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

    status_msg = await message.answer(f"⏳ Հրապարակվում է {len(users)} օգտատիրոջ համար...")

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
            await asyncio.sleep(0.3)
        except Exception:
            pass

    report = (
        f"✅ **Հրապարակումն ավարտվեց!**\n\n"
        f"📨 Հասավ՝ **{sent_count}** ակտիվ բաժանորդի\n"
        f"🚫 Բաց թողնվեց (ալիքից դուրս եկածներ)՝ **{skipped_unsub}** հոգի\n"
    )
    if fid:
        report += f"\n🔑 **Ֆայլի ID (կոդում ավելացնելու համար)՝**\n`{fid}`"

    await status_msg.edit_text(report, parse_mode=ParseMode.MARKDOWN)

# ==========================================
# 🌐 24/7 ՎԵԲ ՍԵՐՎԵՐ (RENDER)
# ==========================================
async def handle(request):
    return web.Response(text="Bot is online and running 24/7!")

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
            logging.info("🚀 Բոտը հաջողությամբ միացավ...")
            await dp.start_polling(bot)
        except Exception as e:
            logging.error(f"Polling error: {e}. Վերագործարկում 5 վայրկյանից...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
    
