import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")

DB_HOST = ""
DB_USER = os.environ.get("DB_USER")
DB_NAME = os.environ.get("DB_NAME")
DB_PASS = os.environ.get("DB_PASS")

COMMANDS = ['start', 'help']
HELP_MESSAGE = 'فایلتو بفرست تا کلمه‌هاشو برات دربیارم.\nحواست باشه که فرمتش باید pdf ،srt و یا txt باشه.'
START_MESSAGE = 'سلام خوشگله!\nیه فایل بفرست تا کلمه‌هاشو برات دربیارم. 👀'
ERROR_MESSAGE = 'این چیزی که فرستادی رو نمی<200c>فهمم.\nیه فایل درست بفرست. (pdf, srt, txt)'
BUTTON_MESSAGE = 'فایلتو دارمش!\nفرمت خروجی رو انتخاب کن:'
CAPTION = 'بفرمایین خدمتتون!'
