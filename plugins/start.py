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


IST = pytz.timezone("Asia/Kolkata")
service_name = "N/A"
@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    user_id = message.from_user.id
    first = message.from_user.first_name
    
    # 1. Check if the link has a "serid_"
    if "serid_" in message.text:
        try:
            _, service_id = message.text.split("_", 1)
            is_subscribed, expiration_date = await verify_subscription(client, user_id, service_id)

            if not is_subscribed:
                txt = f"""<b><blockquote>MadxBotz ~ Cloud Paid Service</blockquote>\n\nHello {first}\n\nYou don't have any active subscriptions.\n\n<blockquote>〽 Powered by {POWERED_BY}</blockquote></b>"""
                await client.send_photo(
                    chat_id=user_id,
                    caption=txt,
                    photo=IMG_URL,
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                btn = InlineKeyboardMarkup([[InlineKeyboardButton("Generate Link", callback_data=f"generate_{service_id}")]])
                txt = f"""<b><blockquote>MadxBotz ~ Cloud Paid Service</blockquote>\n\nHello {first}\n\nYour subscription is added! Click below.\n\n<blockquote>〽 Powered by {POWERED_BY}</blockquote></b>"""
                await client.send_photo(
                    chat_id=user_id,
                    caption=txt,
                    photo=IMG_URL,
                    parse_mode=enums.ParseMode.HTML,
                    reply_markup=btn
                )
        except Exception as e:
            print(f"Error in start link: {e}")
            return

    # 2. Normal /start command (Main Menu)
    else:
        txt = f"""<b><blockquote>MadxBotz ~ Cloud Paid Service</blockquote>\n\nHello {first}\n\nI am the Subscription Management Bot.\n\n<blockquote>〽 Powered by {POWERED_BY}</blockquote></b>"""
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("👉 Checkout Plans 👈", callback_data="checkout")],
            [InlineKeyboardButton("👀 View Demo", url="https://t.me/YourDemoLink"), InlineKeyboardButton("⭐ Reviews", url="https://t.me/YourReviewsLink")],
            [InlineKeyboardButton("📖 How to Buy", url="https://t.me/YourGuideLink"), InlineKeyboardButton("✉️ Contact Owner", url="https://t.me/YourUsername")],
            [InlineKeyboardButton("🔥 Sex Talk 🔞", url="https://t.me/YourChannel"), InlineKeyboardButton("🤖 Learn Bot Making", url="https://t.me/YourBotChannel")],
            [InlineKeyboardButton("📄 My Plan", callback_data="my_plan")]
        ])

        await client.send_photo(
            chat_id=user_id,
            caption=txt,
            photo=IMG_URL,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=buttons
        )
