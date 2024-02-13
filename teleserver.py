import logging
import os
import sys
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from aiogram.utils.markdown import hbold
import asyncio
from astrometry_utils import astrometry

logging.basicConfig(level=logging.INFO)

TOK = ''
# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Приветствую, {hbold(message.from_user.full_name)}!\n"
                         f"Этот бот представляет собой простой способ астрометрического решения штучных fits файлов "
                         f"при помощи API Astrometry.net.\n"
                         f"Чтобы получить решение вашего звездного поля отправьте .fits файл весом до 20 МБ и, "
                         f"чтобы ускорить процесс выполнения укажите дополнительные параметры "
                         f"(центр кадра по оси прямого вохождения, по оси склонения и радиус поиска в градусах, "
                         f"а так же верхний и нижний придел масштаба изображения в угловых секундах на пиксель)"
                         f"текстом разделяя их пробелом в соответствии с примером:\n"
                         f"0.0 0.0 0.25 1.2 1.4")


@dp.message()
async def echo_handler(message: types.Message) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    try:
        file_id = message.document.file_id
        comments = message.text
        file = await message.bot.get_file(file_id=file_id)
        file_path = file.file_path

        file_name = message.document.file_name
        await message.bot.download_file(file_path=file_path, destination=file_name)
        if not ('.fits' in file_name or '.fit' in file_name or '.fts' in file_name):
            await message.answer("Файл должен иметь расширение .fit, .fits или .fts")

        await message.answer(f'file name: {file_name}')
        wcs_file, info_wcs, check_wcs = astrometry(file_name, comments)
        wcs_file_png = wcs_file + '.png'
        if not check_wcs:
            wcs_send = FSInputFile(wcs_file)
            await message.answer(info_wcs)
            await message.answer_document(wcs_send)
            if os.path.isfile(wcs_file):
                os.remove(wcs_file)
        else:
            await message.answer("WCS уже записана в шапку")
        wcs_png_send = FSInputFile(wcs_file_png)
        await message.answer_photo(wcs_png_send)
        if os.path.isfile(wcs_file_png):
            os.remove(wcs_file_png)
    except TypeError:
        # But not all the types is supported to be copied so need to handle it
        await message.answer("Что-то пошло не так")


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOK, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())


# @dp.message_handler()
# async def echo(message: types.Message):
#     if "кал" in message.text:
#         await message.delete()
#
# if __name__ == '__main__':
#     executor.start_polling(dp, skip_updates=True)
