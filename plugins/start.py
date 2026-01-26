import asyncio
import time
from datetime import datetime
from pyrogram import Client, filters, __version__, enums
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from typing import List
import requests
from bot import Bot
from config import *
from pyrogram.enums import ChatMemberStatus
from helper_func import *
from bson import ObjectId
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
from math import ceil
import pytz


IST = pytz.timezone("Asia/Kolkata")


@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    user_id = message.from_user.id
    first = message.from_user.first_name
    username = message.from_user.username if message.from_user.username else None
    user_data = await present_user(user_id)

    if not user_data:
        await new_user(user_id)
        await client.send_message(
            chat_id=log_chat_id,
            text=f"New User Started The Bot\n\n{first} | {user_id}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "View User",
                            url=f"tg://user?id={user_id}",
                        )
                    ]
                ]
            ),
        )

    if "serid_" in message.text:
        _, service_id = message.text.split("_", 1)

        is_subscribed, expiration_date = await verify_subscription(
            client, user_id, service_id
        )

        if not is_subscribed:
            response = f"""
<b><blockquote>Hello {first}</blockquote>

You don't have any active subscriptions to generate an invite link.

Send /buyservice to buy a new subscription.

<blockquote>〽️ Powered by {POWERED_BY}</blockquote>
</b>"""
            await client.send_photo(
                chat_id=user_id,
                caption=response,
                photo=IMG_URL,
                parse_mode=enums.ParseMode.HTML,
            )
        else:
            reply_markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Generate Link",
                            callback_data=f"generate_{service_id}",
                        )
                    ]
                ]
            )

            caption_txt = f"""<b><blockquote>MadxBotz ~ Cloud Paid Service</blockquote>
            
Hello {first}

Your subscription is added and Click Below button to Generate Invite links for the Groups.
            
<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>"""

            await client.send_photo(
                chat_id=user_id,
                caption=caption_txt,
                photo=IMG_URL,
                parse_mode=enums.ParseMode.HTML,
                reply_markup=reply_markup,
            )
    else:
        response = f"""<b><blockquote>MadxBotz ~ Cloud Paid Service</blockquote>
        
Hello {first}

I am the Subscription Management Bot for MadxBotz Community.

Send /buyservice to subscribe for New Service.

If you need assistance with your subscription, please 
contact the admin or check your subscription details using
the /mysub command.

Thank you for choosing our community.

<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>"""

        # ===================== ADDED BUTTONS (L121 FIX) =====================
        main_menu_buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "👉 Checkout Plans 👈",
                        callback_data="checkout_plans"
                    )
                ],
                [
                    InlineKeyboardButton("👀 View Demo", url="https://t.me/YOUR_DEMO"),
                    InlineKeyboardButton("⭐ Reviews", url="https://t.me/YOUR_REVIEWS"),
                ],
                [
                    InlineKeyboardButton("📘 How to Buy", url="https://t.me/YOUR_HOW_TO_BUY"),
                    InlineKeyboardButton("✉️ Contact Owner", url="https://t.me/Ruban9124"),
                ],
                [
                    InlineKeyboardButton("🔥 Sex Talk 🔞", url="https://t.me/YOUR_18_PLUS"),
                    InlineKeyboardButton("🤖 Learn Bot Making", url="https://t.me/YOUR_BOT"),
                ],
                [
                    InlineKeyboardButton("📄 My Plan", callback_data="my_plan")
                ]
            ]
        )

        await client.send_photo(
            chat_id=user_id,
            caption=response,
            photo=IMG_URL,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=main_menu_buttons
        )

