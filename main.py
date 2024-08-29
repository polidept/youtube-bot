import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InputFile
from yt_dlp import YoutubeDL
from config import TOKEN

FFMPEG_LOCATION = '/opt/homebrew/bin/ffmpeg'  

bot = Bot(token=TOKEN)
dp = Dispatcher()

SAVE_PATH = './downloads/'

if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)

@dp.message(Command(commands=['start', 'help']))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне ссылку на видео с YouTube, и я конвертирую его в аудио файл.")

@dp.message(Command(commands=['send_audio']))
async def send_audio_file(message: types.Message):
    files = [f for f in os.listdir(SAVE_PATH) if os.path.isfile(os.path.join(SAVE_PATH, f)) and f.endswith('.mp3')]
    
    if not files:
        await message.reply("В папке downloads нет аудиофайлов.")
        return
    
    # Отправляем последний добавленный файл
    latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(SAVE_PATH, f)))
    audio_file_path = os.path.join(SAVE_PATH, latest_file)
    
    with open(audio_file_path, 'rb') as f:
        audio = InputFile(f, filename=os.path.basename(audio_file_path))
        await message.reply("Вот последний загруженный аудиофайл:")
        await bot.send_audio(message.chat.id, audio)

@dp.message()
async def download_video(message: types.Message):
    url = message.text

    # Проверяем, что сообщение содержит ссылку на YouTube
    if 'youtube.com' in url or 'youtu.be' in url:
        await message.reply("Скачиваю видео, подождите...")

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': SAVE_PATH + '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'ffmpeg_location': FFMPEG_LOCATION,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)
                audio_file_path = ydl.prepare_filename(info_dict).rsplit('.', 1)[0] + '.mp3'

            # Проверьте, что файл существует
            if os.path.isfile(audio_file_path):
                # Открываем файл для чтения в бинарном режиме
                with open(audio_file_path, 'rb') as f:
                    audio = InputFile(f, filename=os.path.basename(audio_file_path))
                    await message.reply("Конвертация завершена! Вот ваш аудиофайл:")
                    await bot.send_audio(message.chat.id, audio)

                # Удаляем скачанный файл после отправки
                os.remove(audio_file_path)
            else:
                await message.reply("Не удалось найти файл для отправки.")

        except Exception as e:
            await message.reply(f"Произошла ошибка при скачивании или конвертации: {str(e)}")
    else:
        await message.reply("Пожалуйста, отправьте действительную ссылку на видео с YouTube.")

async def main():
    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
