# run: python -m "infobot.run"
from aiogram import Bot
from aiogram import Dispatcher
from aiogram import executor
from aiogram import types

from .command import CommamdHandler
from .common import env_var_line
from .storage import RateStorage

bot = Bot(token=env_var_line("BOT_TOKEN"))
dp = Dispatcher(bot)
storage = RateStorage()
cmd_handler = CommamdHandler(storage)


async def setup_loop(dispatcher):
    """Setup actual loop from dispatcher into storage.
    """
    storage.actual_loop = dispatcher.loop


@dp.message_handler()
async def make_answer(message: types.Message):
    """Single enter point.
    """
    user = f"{message.from_user.full_name}({message.from_user.id})"
    msg, data = await cmd_handler.execute(user, message.text)
    if data:
        await message.reply_photo(
            data, caption=msg or "Rate history"
        )
    else:
        await message.answer(msg)

try:
    executor.start_polling(
        dp, skip_updates=True, on_startup=setup_loop
    )
finally:
    storage.close()
