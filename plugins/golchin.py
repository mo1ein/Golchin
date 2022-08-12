import os
from functools import wraps
from typing import Union, List
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from core.text_extractor import ExtractText
from configs import COMMANDS, ERROR_MESSAGE, BUTTON_MESSAGE, CAPTION
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message


# TODO: move to config?!
user_data = {}


def build_menu(
    buttons: List[InlineKeyboardButton],
    n_cols: int,
    header_buttons: Union[
        InlineKeyboardButton,
        List[InlineKeyboardButton]
    ] = None,
    footer_buttons: Union[
        InlineKeyboardButton,
        List[InlineKeyboardButton]
    ] = None
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


# TODO: add typing
def send_action(action: ChatAction):
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


@Client.on_message(
    filters.document &
    filters.private &
    ~filters.command(COMMANDS)
)
@send_action(ChatAction.TYPING)
async def dl_file(client, message) -> None:
    # print('here')
    original_name = message.document.file_name
    file_type = message.document.mime_type
    # print(file_type)
    chat_id = message.chat.id
    user_data[chat_id] = original_name
    if (file_type == "application/pdf"
            or file_type == "application/x-subrip"
            or file_type == "text/plain"):
        # TODO: set pattern to file name for uniqe names
        # export with words.pdf or words.html
        await client.download_media(message.document.file_id, original_name)

        buttons = create_button()
        reply_markup = InlineKeyboardMarkup(build_menu(buttons, n_cols=3))

        await message.reply_text(
            BUTTON_MESSAGE,
            quote=True,
            reply_markup=reply_markup,
        )
    else:
        await message.reply_text(ERROR_MESSAGE, quote=True)


@Client.on_callback_query()
async def send_pdf(client, callback_query) -> None:
    query = callback_query
    extract_text = ExtractText()
    chat_id = query.message.chat.id
    filename = user_data[chat_id]
    ext = filename.split('.')[-1]
    name_without_ext = '.'.join(filename.split('.')[:-1])
    # TODO: add exception for create upload dir if not exist
    output_filename = f'./upload/Words_of_{name_without_ext}'
    path = f"./downloads/{filename}"
    print(os.path.exists(path))

    # TODO: check from mime not name
    if ext == 'pdf':
        fulltext = extract_text.read_pdf(path)
    elif ext == 'txt':
        fulltext = extract_text.read_txt(path)
        # TODO: add other format of srt
    elif ext == 'srt':
        fulltext = extract_text.read_srt(path)

    await query.message.edit_text(f'خب خروجی رو به شکل {query.data} برات می‌فرستم.\nیکم صبر کن الان آماده می‌شه.')

    (
        words_list,
        not_added_count,
        blacklist_words,
        not_word_count,
        duplicates_count
    ) = extract_text.clean_words(fulltext)

    """
    TODO: add bot username to caption
    bot_username = ''
    CAPTION = (
        f'words length: {len(words_list)}\n'
        f'not added count: {not_added_count}\n'
        f'blacklist words: {blacklist_words}\n'
        f'not word count:  {not_word_count}\n'
        f'duplicates count: {duplicates_count}\n'
    )
    """

    # TODO: change var d name
    d = extract_text.translate_words(words_list)
    d = sorted(d, key=lambda d: d['count'], reverse=True)

    if query.data == 'pdf' or query.data == 'html':
        # TODO: exception
        # if os.path.exists(path):
        html = extract_text.dic_to_html(
            d,
            len(d),
            not_added_count,
            blacklist_words,
            not_word_count,
            duplicates_count
        )
        # TODO: name of output
        extract_text.export_pdf(html, output_filename)
        # TODO: add send doc..to other func??
        ex = '.pdf' if query.data == 'pdf' else '.html'
        output_filename += ex
        await upload_document(client, query, output_filename)
    else:
        extract_text.dic_to_csv(
            d,
            len(d),
            not_added_count,
            blacklist_words,
            not_word_count,
            duplicates_count,
            output_filename
        )

        output_filename += '.csv'
        await upload_document(client, query, output_filename)
    await query.message.delete()


@send_action(ChatAction.UPLOAD_DOCUMENT)
async def upload_document(
    client,
    message,
    file_name: str,
) -> None:

    # print(os.path.exists(f"./downloads/{file_name}"))
    # TODO:
    # if os.path.exists(f"./downloads/{file_name}"):

    await client.send_document(
        chat_id=message.from_user.id,
        document=file_name,
        caption=CAPTION,
    )
    os.remove(file_name)
    print('end of code')
