from bot import Bot
from pyrogram.types import Message
from pyrogram import filters
import platform
import psutil
import humanize
from config import *
from datetime import datetime
from helper_func import get_readable_time
import speedtest
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.database import services_data


@Bot.on_message(filters.command("stats"))
async def stats(bot: Bot, message: Message):
    now = datetime.now()
    delta = now - bot.uptime
    uptime = await get_readable_time(delta.seconds)

    system_info = {
        "System": platform.system(),
        "RAM Total": humanize.naturalsize(psutil.virtual_memory().total),
        "RAM Used": humanize.naturalsize(psutil.virtual_memory().used),
        "RAM Free": humanize.naturalsize(psutil.virtual_memory().available),
        "Storage Total": humanize.naturalsize(psutil.disk_usage("/").total),
        "Storage Used": humanize.naturalsize(psutil.disk_usage("/").used),
        "Storage Free": humanize.naturalsize(psutil.disk_usage("/").free),
    }

    st = speedtest.Speedtest()
    st.get_best_server()
    download_speed = st.download() / 1024 / 1024
    upload_speed = st.upload() / 1024 / 1024

    system_info_text = "\n".join(
        [f"<b>{key}: {value}</b>" for key, value in system_info.items()]
    )
    speedtest_info_text = f"<b>Download Speed:</b> {download_speed:.2f} Mbps\n<b>Upload Speed:</b> {upload_speed:.2f} Mbps"

    reply_message = f"Uptime : {uptime}\n\nServer Details:\n{system_info_text}\n\nSpeedtest Results:\n{speedtest_info_text}"

    await message.reply(reply_message)


@Bot.on_message(filters.command("ping"))
async def ping(bot: Bot, message: Message):
    start_time = datetime.now()
    reply = await message.reply("Pong")
    end_time = datetime.now()
    latency = (end_time - start_time).microseconds / 1000
    await reply.delete()
    await message.reply(
        f"<b>Bot's latency is {latency:.2f} ms\n\n<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>"
    )


@Bot.on_message(
    filters.private
    & ~filters.command(
        [
            "start",
            "stats",
            "ping",
            "myplan",
            "broadcast",
            "batch",
            "addservice",
            "buyservice",
            "id",
            "addsub",
            "remsub",
            "user_info",
            "mysub",
            "list_subs",
            "broadcast",
            "viewservices",
            "bc",
        ]
    )
)
async def useless(_, message: Message):

    user_id = message.chat.id

    if user_id == OWNER_ID:
        await message.reply_photo(
            caption=f"""<b><blockquote>MadxBotz ~ Subscription Bot</blockquote>

<blockquote>Available Commands</blockquote>

/start - Start the bot

/mysub - Get your Subscription Details

/id - Get your ID

/stats - To Check Bot Status

/addsub - Add New Sub (Admin Only)

/remsub - Remove  Sub (Admin Only)

/user_info - View User (Admin Only)

/list_subs - List All users ( Admin Only)

/buyservice - To Buy New Service

/addservice - To Add New Service

/viewservices - View added Service

<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>""",
            photo=IMG_URL,
        )
    else:
        await message.reply_photo(
            caption=f"""<b><blockquote>MadxBotz ~ Subscription Bot</blockquote>

<blockquote>Available Commands</blockquote>

/mysub - To Check Your Subscription Details.

/plans - To Check Available Plans.

/id - To Check your User ID.

<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>""",
            photo=IMG_URL,
        )


@Bot.on_message(filters.command("viewservices"))
async def show_services(client, message: Message):
    services_cursor = services_data.find({})
    services_list = await services_cursor.to_list(length=100)

    if not services_list:
        await message.reply_text("No services available at the moment.")
        return

    response_text = "<b>Available Services:</b>\n\n"
    buttons = []

    for service in services_list:
        service_name = service.get("service_name", "Unnamed Service")
        group_ids = service.get("group_ids", [])
        plans = service.get("plans", {})
        created_at = service.get("created_at", "Unknown date")
        service_id = str(service.get("_id"))

        buttons.append(
            [
                InlineKeyboardButton(
                    f"{service_name}", callback_data=f"serviceview_{service_id}"
                )
            ]
        )

        group_list = (
            "\n".join([f"• {gid}" for gid in group_ids])
            if group_ids
            else "No groups available."
        )

        plans_list = (
            "\n".join(
                [
                    f"• {plan_duration} - ₹{details['price']}"  # Access price directly
                    for plan_duration, details in plans.items()
                ]
            )
            if plans
            else "No plans available."
        )

        response_text += (
            f"• <b>{service_name}</b> (ID: <code>{service_id}</code>)\n"
            f"<b>Created At:</b> {created_at}\n"
            f"<b>Groups:</b>\n{group_list}\n"
            f"<b>Plans:</b>\n{plans_list}\n\n"
        )

    await message.reply_text(response_text, reply_markup=InlineKeyboardMarkup(buttons))
