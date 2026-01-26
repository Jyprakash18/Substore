from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
from math import ceil
from bson import ObjectId
import pytz

from bot import Bot
from config import *
from helper_func import *
from database.database import (
    present_user,
    verify_subscription,
    rem_subscription_user,
    subscriptions_data,
    services_data,
    full_userbase,
    del_user,
    new_user,
)

IST = pytz.timezone("Asia/Kolkata")

SUBSCRIPTIONS_PER_PAGE = 1
PAGE_SIZE = 2

user_pagination_data = {}

# ============================== START ==============================

@Client.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_id = message.from_user.id
    first = message.from_user.first_name

    if not await present_user(user_id):
        await new_user(user_id)

    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🛒 Buy Service", callback_data="buy_service")],
            [InlineKeyboardButton("📦 My Subscription", callback_data="my_sub")]
        ]
    )

    await client.send_photo(
        chat_id=user_id,
        photo=IMG_URL,
        caption=f"<b>Hello {first}\nWelcome to MadxBotz</b>",
        reply_markup=buttons,
        parse_mode=enums.ParseMode.HTML
    )

# ============================== CALLBACKS ==============================

@Client.on_callback_query(filters.regex("^my_sub$"))
async def mysub_cb(client, query):
    user_id = query.from_user.id
    subs = await subscriptions_data.find({"user_id": user_id}).to_list(None)

    if not subs:
        await query.answer("No active subscription", show_alert=True)
        return

    await send_subscription_page(client, query.message, subs, 1)

@Client.on_callback_query(filters.regex("^sub_page_"))
async def sub_page_cb(client, query):
    page = int(query.data.split("_")[-1])
    user_id = query.from_user.id

    subs = await subscriptions_data.find({"user_id": user_id}).to_list(None)
    await send_subscription_page(client, query.message, subs, page)
    await query.answer()

@Client.on_callback_query(filters.regex("^page_"))
async def admin_page_cb(client, query):
    page = int(query.data.split("_")[-1])
    users = user_pagination_data.get(query.from_user.id)

    if not users:
        await query.answer("Session expired", show_alert=True)
        return

    user_list = await get_user_list_page(client, page, users)

    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page_{page-1}"))
    if (page + 1) * PAGE_SIZE < len(users):
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page+1}"))

    await query.message.edit_caption(
        caption=f"<b><blockquote>User Details</blockquote></b>{''.join(user_list)}",
        reply_markup=InlineKeyboardMarkup([buttons]) if buttons else None,
        parse_mode=enums.ParseMode.HTML
    )
    await query.answer()

# ============================== SUB DISPLAY ==============================

async def send_subscription_page(client, message, subs, page):
    total_pages = ceil(len(subs) / SUBSCRIPTIONS_PER_PAGE)
    sub = subs[page-1]

    service_data = await services_data.find_one({"_id": ObjectId(sub["service_id"])})
    service_name = service_data["service_name"]

    expiry = datetime.fromtimestamp(sub["expiry"], IST).strftime("%d-%b-%Y %I:%M %p")
    remaining = await get_remaining_time(sub["expiry"])

    text = f"""
<b><blockquote>Subscription Details</blockquote>

🛠 Service: {service_name}
⏰ Expiry: {expiry}
⏳ Remaining: {remaining}

<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>
"""

    buttons = []
    if page > 1:
        buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"sub_page_{page-1}"))
    if page < total_pages:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"sub_page_{page+1}"))

    await message.edit_caption(
        caption=text,
        reply_markup=InlineKeyboardMarkup([buttons]) if buttons else None,
        parse_mode=enums.ParseMode.HTML
    )

# ============================== ADMIN LIST ==============================

async def get_user_list_page(client, page, users):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    result = []

    for u in users[start:end]:
        user = await client.get_users(u["user_id"])
        service = await services_data.find_one({"_id": ObjectId(u["service_id"])})

        result.append(
            f"""
<b>
👤 {user.first_name}
🆔 <a href="tg://user?id={user.id}">{user.id}</a>
🛠 {service['service_name']}
</b>
"""
        )
    return result
