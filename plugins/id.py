from pyrogram import filters, enums
from config import *

from bot import Bot


@Bot.on_message(filters.command("id") & filters.private)
async def showid(client, message):
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        user_id = message.chat.id

        await message.reply_photo(
            caption=f"""<b><blockquote>MadxBotz ~ Subscription Bot</blockquote>

Your User ID is : <code>{user_id}</code>

<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>""",
            photo=IMG_URL,
            quote=True,
        )
