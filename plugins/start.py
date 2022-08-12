from plugins.db import database
from configs import START_MESSAGE
from pyrogram import Client, filters


@Client.on_message(filters.command('start') & filters.private)
async def start(client, message):
    my_db = database()
    # database().create_table()
    # if user not exist, add to database
    if my_db.is_user_exist(message.from_user) is False:
        my_db.add_user(message.from_user)
        # print('added user:', message.from_user.id)
    # my_db.show_users()
    await message.reply_text(START_MESSAGE)
