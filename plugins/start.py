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
        await client.send_photo(
            chat_id=user_id,
            caption=response,
            photo=IMG_URL,
            parse_mode=enums.ParseMode.HTML,
        )


@Bot.on_message(filters.private & filters.command("plans"))
async def plan_handler(client: Client, message: Message):
    user_id = message.from_user.id

    response = f"""<b><blockquote>MadxBotz ~ Cloud Paid Service</blockquote>
    
🤖 Mirror Leech Group 🚀

- Prename ⚡️
- Metadata 📛
- Remname 🟢
- Caption 🗓
- Dump🗑
- Unlimited Mirror☁️ / Leech 🌐
- No Task Limit ♾
- 4GB Leech 💯
- And So On...🔼

⏰ Join At Just 🤩

New Join - Rs. 30/Month 🆕
Renewal - Rs. 25/Month 

⚡️ Dm - @Ruban9124 For More Details 

✔️Demo Available for all service 🏪

<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>"""

    await client.send_photo(
        chat_id=user_id,
        caption=response,
        photo=IMG_URL,
    )


@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command("addsub"))
async def addsub_handler(client: Client, message: Message):
    try:
        command_parts = message.text.split()

        if len(command_parts) != 2:
            await message.reply_text("Usage: <code>/addsub user_id</code>")
            return

        user_id = int(command_parts[1])

        # Fetch available services from the database
        services = [service async for service in services_data.find()]
        if not services:
            await message.reply_text("No services are available.")
            return

        # Ask to select a service
        service_buttons = [
            [
                InlineKeyboardButton(
                    service["service_name"],
                    callback_data=f"manadd_{service['_id']}_{user_id}",
                )
            ]
            for service in services
        ]
        service_markup = InlineKeyboardMarkup(service_buttons)

        await message.reply_text(
            "Please choose a service for the subscription:", reply_markup=service_markup
        )

    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")
        print(f"Error in /addsub: {e}")


@Bot.on_message(filters.command("remsub") & filters.user(ADMINS) & filters.private)
async def remsub_command(client: Client, message: Message):
    command_args = message.text.split()

    if len(command_args) != 3:
        await message.reply("Usage: <code>/remsub user_id service_id</code>")
        return

    try:
        user_id = int(command_args[1])
        service_id = command_args[2]
    except ValueError:
        await message.reply("Invalid user_id. Please provide a valid numeric user_id.")
        return

    await rem_subscription_user(user_id, service_id)

    try:
        user = await client.get_users(user_id)
        user_first_name = user.first_name
        user_username = user.username if user.username else "Username"
        user_chat_id = user.id
    except Exception as e:
        await message.reply(f"Failed to fetch user details: {e}")
        return

    try:
        await client.send_message(
            chat_id=user_chat_id,
            text=f"Your subscription Has been cancelled 🥺 .\nPlease contact support for more details.",
        )
        await client.send_message(
            chat_id=log_chat_id,
            text=f"Subscription Has been Removed Manually for this User\n\n{user_first_name} | {user_chat_id}",
            reply_markup=InlineKeyboardMarkup(
                [
                    InlineKeyboardButton(
                        "View User",
                        url=f"tg://user?id={user_chat_id}",
                    ),
                ]
            ),
        )
    except Exception as e:
        print(f"Failed to send message to user {user_id}: {e}")

    await message.reply(
        f"Subscription removed for user {user_id}. A notification has been sent to them."
    )


@Bot.on_message(filters.command("user_info") & filters.user(ADMINS) & filters.private)
async def user_info_command(client: Client, message: Message):
    command_args = message.text.split()

    if len(command_args) != 2:
        await message.reply("Usage: <code>/user_info user_id</code>")
        return

    try:
        user_id = int(command_args[1])
    except ValueError:
        await message.reply("Invalid user_id. Please provide a valid numeric user_id.")
        return

    user = await subscriptions_data.find_one({"user_id": user_id})

    if not user:
        await message.reply("User not found in the database.")
        return

    # Fetching user details
    try:
        telegram_user = await client.get_users(user_id)
        first_name = telegram_user.first_name
        username = telegram_user.username if telegram_user.username else "No Username"
    except Exception as e:
        first_name = "Unknown"
        username = "None"
        print(f"Failed to fetch additional user details: {e}")

    # Extracting user info
    expiry_timestamp = user.get("expiry")

    if expiry_timestamp:
        remaining_time = await get_remaining_time(expiry_timestamp)
        expiry_formatted = datetime.fromtimestamp(expiry_timestamp, IST).strftime(
            "%d-%b-%Y %I:%M %p"
        )
    else:
        remaining_time = "N/A"
        expiry_formatted = "N/A"

    pay_img = user.get("pay_id", "N/A")
    pay_img_txt = pay_img if pay_img != "N/A" else "N/A"

    service_id = user.get("service_id")
    if service_id:
        service_data = await services_data.find_one({"_id": ObjectId(service_id)})
        if service_data:
            service_name = service_data.get("service_name", "Unknown Service")
        else:
            service_name = "Unknown Service"
    else:
        service_name = "N/A"

    user_info = f"""<b>
<u>User Details 👾</u>
        
⁍ User ID: <a href='tg://user?id={user_id}'>{user_id}</a>👨🏻‍💻
⁍ First Name: <a href='tg://user?id={user_id}'>{first_name}</a>👁‍🗨
⁍ Username: @{username} 📛

⁍ Service Name: {service_name} 🛠️
⁍ Subscription Status: Subscribed ✅️
⁍ Subscription Expiry: {expiry_formatted} ⏰
⁍ Remaining Time: {remaining_time}⏳️
⁍ Payment ID: {pay_img_txt}💲
</b>        
"""

    await client.send_message(
        chat_id=message.chat.id,
        text=user_info,
        reply_to_message_id=message.id,
        disable_web_page_preview=True,
    )


SUBSCRIPTIONS_PER_PAGE = 1


@Bot.on_message(filters.command("mysub") & filters.private)
async def my_sub_command(client: Client, message: Message):
    user_id = message.from_user.id

    user = await subscriptions_data.find({"user_id": user_id}).to_list(length=None)

    if not user:
        text_not = (
            f"<b>You don't have any Active Subscription.\n\n"
            f"May be it is Expired. So Purchase or Renew your required Service.\n\n"
            f"Check Available Services by using /buyservice\n\n"
            f"<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>"
        )

        await client.send_photo(
            chat_id=user_id,
            caption=text_not,
            photo=IMG_URL,
            reply_to_message_id=message.id,
            parse_mode=enums.ParseMode.HTML,
        )
        return

    await send_subscription_page(client, message, user, 1)


async def send_subscription_page(client, message, subscriptions, page_number):
    total_subs = len(subscriptions)
    total_pages = ceil(total_subs / SUBSCRIPTIONS_PER_PAGE)

    start = (page_number - 1) * SUBSCRIPTIONS_PER_PAGE
    end = start + SUBSCRIPTIONS_PER_PAGE
    current_subs = subscriptions[start:end]

    subscription_info = ""
    for sub in current_subs:
        expiry_timestamp = sub.get("expiry", 0)
        pay_img = sub.get("pay_id", "N/A")
        pay_img_txt = pay_img if pay_img != "N/A" else "N/A"

        if expiry_timestamp:
            expiry_date = datetime.fromtimestamp(expiry_timestamp).strftime(
                "%d-%b-%Y %I:%M %p"
            )
            remaining_time = await get_remaining_time(expiry_timestamp)
        else:
            expiry_date = "Not Subscribed"
            remaining_time = "N/A"

        # Fetch service name from the database using service_id
        service_id = sub.get("service_id")
        if service_id:
            service_data = await services_data.find_one({"_id": ObjectId(service_id)})
            service_name = (
                service_data.get("service_name", "Unknown Service")
                if service_data
                else "Unknown Service"
            )
        else:
            service_name = "N/A"

        # Add all subscription details to the subscription_info
        subscription_info += f"""<b><blockquote>Subscription Details</blockquote>

⁍ Service Name: {service_name} 🛠️

⁍ Subscription Status: Subscribed ✅️
⁍ Subscription Expiry: {expiry_date} ⏰
⁍ Remaining Time: {remaining_time} ⏳️
⁍ Payment ID: {pay_img_txt} 💲

<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>"""

    buttons = []

    # Add pagination buttons if necessary
    if page_number > 1:
        buttons.append(
            InlineKeyboardButton(
                "⬅️ Previous", callback_data=f"sub_page_{page_number - 1}"
            )
        )

    if page_number < total_pages:
        buttons.append(
            InlineKeyboardButton("Next ➡️", callback_data=f"sub_page_{page_number + 1}")
        )

    # Only add reply_markup if there are buttons
    reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None

    if message.reply_to_message:
        await client.edit_message_caption(
            chat_id=message.chat.id,
            message_id=message.reply_to_message.id,
            caption=subscription_info,
            reply_markup=reply_markup,  # Ensure reply_markup is only sent if not None
            parse_mode=enums.ParseMode.HTML,
        )
    else:
        await client.send_photo(
            chat_id=message.chat.id,
            caption=subscription_info,
            photo=IMG_URL,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML,
        )


# ******************************************************************************************************************************************

PAGE_SIZE = 2
user_pagination_data = {}

from bson.decimal128 import Decimal128

async def get_user_list_page(client, page: int, users: List[dict]) -> List[str]:
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    user_list = []

    for doc in users[start:end]:
        user_id = doc["user_id"]
        
        # Convert Decimal128 to int if necessary
        if isinstance(user_id, Decimal128):
            user_id = int(user_id.to_decimal())
        elif isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)
        elif not isinstance(user_id, int):
            raise TypeError(f"Invalid user_id type: {type(user_id)}")
        
        expiry_timestamp = doc.get("expiry")

        if expiry_timestamp is None:
            remaining_time = "Not Available"
            expiry_date_display = "Never"
        else:
            remaining_time = await get_remaining_time(expiry_timestamp)
            expiry_date_display = datetime.fromtimestamp(
                expiry_timestamp, IST
            ).strftime("%d-%b-%Y %I:%M %p")

        user = await client.get_users(user_id)
        first_name = user.first_name
        username = user.username if user.username else "None"

        pay_img = doc.get("pay_id", "N/A")
        pay_img_txt = pay_img if pay_img != "N/A" else "N/A"

        service_id = doc.get("service_id")
        if service_id:
            service_data = await services_data.find_one({"_id": ObjectId(service_id)})
            service_name = (
                service_data.get("service_name", "Unknown Service")
                if service_data
                else "Unknown Service"
            )
        else:
            service_name = "N/A"

        user_list.append(
            f"""<b>
⁍ User ID: <a href='tg://user?id={user_id}'>{user_id}</a>👨🏻‍💻
⁍ First Name: <a href='tg://user?id={user_id}'>{first_name}</a>👁‍🗨
⁍ Username: @{username} 📛

⁍ Service Name: {service_name} 🛠️
⁍ Subscription Expiry: {expiry_date_display} ⏰
⁍ Remaining Time: {remaining_time}⏳️
⁍ Payment ID: {pay_img_txt} 💲
</b>
"""
        )
    return user_list


@Client.on_message(
    filters.command("list_subs") & filters.user(ADMINS) & filters.private
)
async def list_users(client: Client, message):
    users = await subscriptions_data.find().to_list(length=None)
    user_id = message.from_user.id

    if users:
        user_pagination_data[user_id] = users
        user_list = await get_user_list_page(client, 0, users)

        if len(users) > PAGE_SIZE:
            keyboard = [InlineKeyboardButton("Next", callback_data="page_1")]
            reply_markup = InlineKeyboardMarkup([keyboard])
        else:
            reply_markup = None

        await client.send_photo(
            chat_id=message.chat.id,
            caption=f"<b><blockquote>Users Details</blockquote>\n</b>{''.join(user_list)}",
            photo=IMG_URL,
            reply_to_message_id=message.id,
            reply_markup=reply_markup,
        )
    else:
        await message.reply("No users found.")


# =====================================================================================##

WAIT_MSG = """"<b>ᴘʀᴏᴄᴇꜱꜱɪɴɢ ....⎔⬣ </b>"""

REPLY_ERROR = """<code> ⏣ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴀꜱ ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴇꜱꜱᴀɢᴇ ᴡɪᴛʜ ᴏᴜᴛ ᴀɴʏ ꜱᴘᴀᴄᴇꜱ ⏣ </code>"""

# =====================================================================================##


@Bot.on_message(
    filters.private & filters.command(["broadcast", "bc"]) & filters.user(ADMINS)
)
async def send_text(client: Bot, message: Message):
    start_time = time.time()

    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0

        sending = await message.reply(
            "<i>⧖ ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ ᴍᴇꜱꜱᴀɢᴇ.. ᴛʜɪꜱ ᴡɪʟʟ ᴛᴀᴋᴇ ꜱᴏᴍᴇ ᴛɪᴍᴇ ⧗</i>"
        )
        pls_wait = await message.reply("<b>Sending.....</b>")
        broadcast_options = {"disable_notification": False}

        async def update_status():
            nonlocal total, successful, blocked, deleted, unsuccessful
            elapsed_time = time.time() - start_time
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)

            status = f"""<b><u>Bʀᴏᴀᴅᴄᴀsᴛɪɴɢ Mᴇssᴀɢᴇ....</u>

⏣ ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ       : <code>{total}</code>

⏣ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ        : <code>{successful}</code>

⏣ ʙʟᴏᴄᴋᴇᴅ ᴜꜱᴇʀꜱ     : <code>{blocked}</code>

⏣ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛꜱ  : <code>{deleted}</code>

⏣ ᴜɴꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ       : <code>{unsuccessful}</code>

⏣ ᴛɪᴍᴇ ᴛᴀᴋᴇɴ         : <code>{minutes} : {seconds} ᴍɪɴᴜᴛᴇꜱ </code></b>"""
            await pls_wait.edit(status)

        async def periodic_update():
            while True:
                await update_status()
                await asyncio.sleep(5)

        update_task = asyncio.create_task(periodic_update())

        for chat_id in query:
            try:
                await broadcast_msg.forward(chat_id, **broadcast_options)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.forward(chat_id, **broadcast_options)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except Exception as ex:
                print(f"Error broadcasting to {chat_id}: {ex}")
                unsuccessful += 1
            finally:
                total += 1
                await asyncio.sleep(0.1)

        update_task.cancel()

        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)

        status = f"""<b><u>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</u>

⏣ ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ       : <code>{total}</code>

⏣ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ        : <code>{successful}</code>

⏣ ʙʟᴏᴄᴋᴇᴅ ᴜꜱᴇʀꜱ     : <code>{blocked}</code>

⏣ ᴅᴇʟᴇᴛᴇᴅ ᴀᴄᴄᴏᴜɴᴛꜱ  : <code>{deleted}</code>

⏣ ᴜɴꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ       : <code>{unsuccessful}</code>

⏣ ᴛɪᴍᴇ ᴛᴀᴋᴇɴ         : <code>{minutes} : {seconds} ᴍɪɴᴜᴛᴇꜱ </code></b>"""
        await pls_wait.edit(status)
        await sending.delete()
        pls_wait = await message.reply("<b>Broadcast Completed</b>")

    else:
        msg = await message.reply(
            "<i>No message to broadcast. Please reply to a message.</i>"
        )
        await asyncio.sleep(8)
        await msg.delete()
