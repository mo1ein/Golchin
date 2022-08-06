from configs import HELP_MESSAGE
from pyrogram import Client, filters


@Client.on_message(filters.command('help') & filters.private)
async def start(client, message):
    # 'send your pdf, srt or text file to send words frequent and translate'
    await message.reply_text(HELP_MESSAGE)
