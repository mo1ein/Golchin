import os
import time
import math
import asyncio
import psycopg2
from core.pdf2word import pdf2word
from functools import wraps
from typing import Union, List
from utils.progress_bar import pbar
from pyrogram import Client, filters
from utils.cover_extractor import Cover
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import FB_MSG, RECEIVE_FB_MSB, COMMANDS, FEEDBACKS

# TODO: move to config?!
user_data = {}


def build_menu(
    buttons: List[InlineKeyboardButton],
    n_cols: int,
    header_buttons: Union[InlineKeyboardButton,
                          List[InlineKeyboardButton]] = None,
    footer_buttons: Union[InlineKeyboardButton,
                          List[InlineKeyboardButton]] = None
) -> List[List[InlineKeyboardButton]]:
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons if isinstance(
            header_buttons, list) else [header_buttons])
    if footer_buttons:
        menu.append(footer_buttons if isinstance(
            footer_buttons, list) else [footer_buttons])
    return menu


# use typing guide
def create_button():
    '''
    button's shape:
    +-----------------------+
    |       <question>      |
    +-------+-------+-------+
    |  html |  pdf  |  csv  |
    +-------+-------+-------+
    '''
    control_buttons = [
        InlineKeyboardButton("html", callback_data='html'),
        InlineKeyboardButton("pdf", callback_data='pdf'),
        InlineKeyboardButton("csv", callback_data='csv'),
    ]
    '''
    buttons = [InlineKeyboardButton(str(i + 1), callback_data=str(i + 1))
               for i in range(user_data[chat_id]['begin_index'], user_data[chat_id]['end_index'])]
    '''

    return control_buttons

def send_action(action):
    """Sends `action` while processing func command."""
    def decorator(func):
        @wraps(func)
        async def command_func(client, message, *args, **kwargs):
            await client.send_chat_action(
                chat_id=message.from_user.id,
                action=action
            )
            return await func(client, message,  *args, **kwargs)
        return command_func
    return decorator


"""
@Client.on_message(
    filters.reply &
    filters.private &
    ~filters.edited &
    ~filters.command(COMMANDS)
)
async def reply_feedback(client, message):
    '''
    when user reply feedback message
    '''
    # user message replied to fb message
    if message.reply_to_message.text == FB_MSG:
        global FEEDBACKS
        if message.from_user.id in FEEDBACKS:
            FEEDBACKS[message.from_user.id].append(message.text)
        else:
            user_fbs = [message.text]
            FEEDBACKS[message.from_user.id] = user_fbs
        await message.reply_to_message.edit_text(RECEIVE_FB_MSB)

"""


@Client.on_message(
    filters.document &
    filters.private &
    ~filters.edited &
    ~filters.command(COMMANDS)
)
@send_action('typing')
async def dl_file(client, message):
    original_name = message.document.file_name
    file_type = message.document.mime_type 
    print(file_type)
    chat_id = message.chat.id
    user_data[chat_id] = original_name
    if file_type == "application/pdf" or file_type == "application/x-subrip" or file_type == "text/plain":
        # TODO: naming format for uniqe
        # export with words.pdf or words.html
        await client.download_media(message.document.file_id, original_name)

        buttons = create_button()
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=3))

        # TODO: set bold for origin name
        # f"dariaft shod! <b>{original_name}</b>\nwhat output do u want?",
        rcv_msg = await message.reply_text(
            f'فایلتو دارمش!\nفرمت خروجی رو انتخاب کن:',
            quote = True,
            reply_markup=reply_markup,
    )
    else:
        # TODO: change better text and bol with send message
        # await client.send_message(chat_id = chat_id, )
        # await message.reply_text("Please send correct file (pdf, text, srt)", quote = True)
        await message.reply_text("این چیزی که فرستادی رو نمی‌فهمم.\nیه فایل درست بفرست. (pdf, srt, txt)", quote = True)

    # TODO: caption
    '''
    loop = asyncio.get_event_loop()
    loop.create_task(upload_document(client, file_name))
    '''
    # await upload_document(client, message, file_name, rcv_msg)


@Client.on_callback_query()
async def send_pdf(client, callback_query) -> None:
    query = callback_query
    p2w = pdf2word()
    chat_id = query.message.chat.id
    filename = user_data[chat_id]
    ext = filename.split('.')[-1]
    name_without_ext = '.'.join(filename.split('.')[:-1])
    output_filename = f'./upload/Words_of_{name_without_ext}' 
    path = f"./downloads/{filename}"
    print(os.path.exists(path))

    # TODO: check from mime not name
    if ext == 'pdf':
        fulltext = p2w.read_pdf(path)
    elif ext == 'txt':
        fulltext = p2w.read_txt(path)
        #TODO: add other format of srt
    elif ext == 'srt':
        fulltext = p2w.read_srt(path)

    await query.message.edit_text(f'خب خروجی رو به شکل {query.data} برات می‌فرستم.\nیکم صبر کن الان آماده می‌شه.')

    words_list, not_added_count, blacklist_words, not_word_count, duplicates_count = p2w.clean_words(
        fulltext)

    #TODO: add bot username
    bot_username = ''
    CAPTION = f'بفرمایین خدمتتون!'
    
    """
    CAPTION = (
        f'words length: {len(words_list)}\n'
        f'not added count: {not_added_count}\n'
        f'blacklist words: {blacklist_words}\n'
        f'not word count:  {not_word_count}\n'
        f'duplicates count: {duplicates_count}\n'
    )
    """

    #TODO: change var d name
    d = p2w.trans(words_list)
    d = sorted(d, key=lambda d: d['count'], reverse=True)

    if query.data == 'pdf' or query.data == 'html':
        # TODO: exception
        # if os.path.exists(path):
        html = p2w.dic_to_html(
            d, len(d), not_added_count, blacklist_words, not_word_count, duplicates_count)
        # TODO: name of output
        p2w.export_pdf(html, output_filename)
        # TODO: add send doc..to other func??
        ex = '.pdf' if query.data == 'pdf' else '.html'
        output_filename += ex
        await upload_document(client, query, output_filename, CAPTION)
    else:
        p2w.dic_to_csv(
            d, len(d), not_added_count, blacklist_words, not_word_count, duplicates_count, output_filename)

        output_filename += '.csv'
        await upload_document(client, query, output_filename, CAPTION)
    await query.message.delete()

@send_action('upload_document')
async def upload_document(
    client, 
    message,
    file_name: str, 
    caption: str 
):

    # TODO: caption add some details words to caption...
    # print(file_name)
    # print(os.path.exists(f"./downloads/{file_name}"))
    # TODO:
    # if os.path.exists(f"./downloads/{file_name}"):

    await client.send_document(
        chat_id=message.from_user.id,
        document=file_name,
        caption=caption,
    )
    # os.remove(file_name)
    print('end of code')


"""
def main(ext: str = "srt"):
    p2w = pdf2word()
    fname = "my.srt"
    if ext == "srt":
        fulltext = p2w.read_srt(fname)
        words_list, not_added_count, blacklist_words, not_word_count, duplicates_count = p2w.clean_words(
            fulltext)
    elif ext == "pdf":
        fulltext = p2w.read_pdf(fname)
        words_list, not_added_count, blacklist_words, not_word_count, duplicates_count = p2w.clean_words(
            fulltext)
    else:
        fulltext = p2w.read_txt(fname)
        words_list, not_added_count, blacklist_words, not_word_count, duplicates_count = p2w.clean_words(
            fulltext)

    d = p2w.trans(words_list)
    # sort dicts by most frequent words to least
    d = sorted(d, key=lambda d: d['count'], reverse=True)
    # if export csv
    p2w.dic_to_csv(
        d, len(d), not_added_count, blacklist_words, not_word_count, duplicates_count, "out.csv")
    '''
    html = p2w.dic_to_html(
        d, len(d), not_added_count, blacklist_words, not_word_count, duplicates_count)
    p2w.export_pdf(html, "t.html")
    '''
# main()
"""
