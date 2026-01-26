import asyncio
import time
from datetime import datetime
from math import ceil
from typing import List

import pytz
from bson import ObjectId
from bson.decimal128 import Decimal128

from pyrogram import filters, enums
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

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

# =========================================================
# START COMMAND
# =========================================================

@Bot.on_message(filters.private & filters.command("start"))
async def start_command(client: Bot, message: Message):

    user_id = message.from_user.id
    first = message.from_user.first_name

    # save new user
    if not await present_user(user_id):
        await new_user(user_id)
        await client.send_message(
            chat_id=log_chat_id,
            text=f"👤 New User Started Bot\n\n{first} | {user_id}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("View User", url=f"tg://user?id={user_id}")]]
            ),
        )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🛒 Buy Service", callback_data="buy"),
                InlineKeyboardButton("📦 My Subscription", callback_data="mysub"),
            ],
            [
                InlineKeyboardButton("🆘 Help", callback_data="help"),
            ],
        ]
    )

    text = f"""<b><blockquote>MadxBotz ~ Cloud Paid Service</blockquote>

Hello {first} 👋

I am the Subscription Management Bot.

Use buttons below 👇

<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>"""

    await message.reply_photo(
        photo=IMG_URL,
        caption=text,
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML,
    )

# =========================================================
# CALLBACK HANDLER
# =========================================================

@Bot.on_callback_query()
async def callback_handler(client: Bot, callback_query):

    user_id = callback_query.from_user.id
    data = callback_query.data
    await callback_query.answer()

    if data == "buy":
        await client.send_message(user_id, "🛒 Send /buyservice to purchase a plan")

    elif data == "mysub":
        await client.send_message(user_id, "📦 Send /mysub to check your subscription")

    elif data == "help":
        await client.send_message(user_id, "🆘 Contact admin for help")

# =========================================================
# ADD SUB (ADMIN)
# =========================================================

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("addsub"))
async def addsub_handler(client: Bot, message: Message):

    parts = message.text.split()
    if len(parts) != 2:
        return await message.reply_text("Usage: /addsub user_id")

    user_id = int(parts[1])
    services = [s async for s in services_data.find()]

    if not services:
        return await message.reply_text("No services available.")

    buttons = [
        [
            InlineKeyboardButton(
                s["service_name"],
                callback_data=f"manadd_{s['_id']}_{user_id}",
            )
        ]
        for s in services
    ]

    await message.reply_text(
        "Select a service:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

# =========================================================
# REMOVE SUB (ADMIN)
# =========================================================

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("remsub"))
async def remsub_command(client: Bot, message: Message):

    parts = message.text.split()
    if len(parts) != 3:
        return await message.reply("Usage: /remsub user_id service_id")

    user_id = int(parts[1])
    service_id = parts[2]

    await rem_subscription_user(user_id, service_id)

    await client.send_message(
        user_id,
        "❌ Your subscription has been cancelled. Contact support.",
    )

    await client.send_message(
        log_chat_id,
        f"Subscription removed\nUser: {user_id}",
    )

    await message.reply("Subscription removed successfully ✅")

# =========================================================
# MY SUBSCRIPTION
# =========================================================

SUBSCRIPTIONS_PER_PAGE = 1

@Bot.on_message(filters.private & filters.command("mysub"))
async def my_sub_command(client: Bot, message: Message):

    user_id = message.from_user.id
    subs = await subscriptions_data.find({"user_id": user_id}).to_list(None)

    if not subs:
        return await message.reply_photo(
            photo=IMG_URL,
            caption="<b>No active subscription found.</b>",
            parse_mode=enums.ParseMode.HTML,
        )

    await send_subscription_page(client, message, subs, 1)

async def send_subscription_page(client, message, subs, page):

    sub = subs[page - 1]
    expiry = sub.get("expiry")

    if expiry:
        expiry_date = datetime.fromtimestamp(expiry, IST).strftime("%d-%b-%Y %I:%M %p")
        remaining = await get_remaining_time(expiry)
    else:
        expiry_date = "N/A"
        remaining = "N/A"

    service = await services_data.find_one({"_id": ObjectId(sub["service_id"])})
    service_name = service["service_name"] if service else "Unknown"

    text = f"""<b><blockquote>Subscription Details</blockquote>

Service: {service_name}
Expiry: {expiry_date}
Remaining: {remaining}

<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>"""

    await message.reply_photo(
        photo=IMG_URL,
        caption=text,
        parse_mode=enums.ParseMode.HTML,
    )
