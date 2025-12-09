from pyrogram import __version__
from bot import Bot
from config import *
import asyncio
import re
from pyrogram import Client, filters, enums
import time
import pytz
from datetime import datetime
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from database.database import subscriptions_data, services_data

IST = pytz.timezone("Asia/Kolkata")


@Client.on_message(
    filters.private & filters.user(ADMINS) & filters.command("addservice")
)
async def add_service_handler(client, message: Message):
    try:
        # Step 1: Ask for service name
        service_name_msg = await client.ask(
            text="Please provide the service name:",
            chat_id=message.from_user.id,
            timeout=120,
        )
        service_name = service_name_msg.text.strip()

        # Step 2: Ask for service description
        service_description_msg = await client.ask(
            text="<b>Please provide a description for the service:</b>",
            chat_id=message.from_user.id,
            timeout=120,
        )
        service_description = service_description_msg.text.strip()

        # Step 3: Ask for group IDs
        group_ids_msg = await client.ask(
            text="<b>Now provide the group IDs (space or comma-separated):</b>",
            chat_id=message.from_user.id,
            timeout=120,
        )
        group_ids_input = group_ids_msg.text.strip()
        group_ids = re.split(r"[,\s]+", group_ids_input)

        # Step 4: Ask for plans
        plans_msg = await client.ask(
            text="<b>Now provide the plans in the format `1day:price, 7day:price, 1month:price`:</b>",
            chat_id=message.from_user.id,
            timeout=120,
        )
        plans_input = plans_msg.text.strip()

        # Step 5: Parse plans and store as duration and price pairs
        plans = plans_input.split(",")  # Split by commas
        parsed_plans = {}

        for plan in plans:
            try:
                duration, price = plan.split(":")
                duration = duration.strip()
                price = float(price.strip())  # Convert price to float

                parsed_plans[duration] = {"price": price}
            except Exception as e:
                await plans_msg.reply(
                    f"Error parsing plan: {plan}. Ensure the format is correct."
                )
                return

        # Step 6: Insert the service data into the database
        service_data = {
            "service_name": service_name,
            "description": service_description,  # Add the service description here
            "group_ids": group_ids,
            "plans": parsed_plans,
            "created_at": datetime.now(IST).timestamp(),
        }

        await services_data.insert_one(service_data)
        await plans_msg.reply(
            f"<b>Service '{service_name}' with plans and description has been successfully added!</b>"
        )

        print(
            f"Service '{service_name}' added with description: {service_description}, group IDs: {group_ids}, and plans: {parsed_plans}"
        )

    except asyncio.TimeoutError:
        await message.reply_text("<b>You took too long to provide the information.</b>")
    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")
        print(f"Error in add_service_handler: {e}")


@Client.on_message(filters.private & filters.command("buyservice"))
async def buy_service_handler(client, message: Message):
    try:
        # Step 1: Fetch all available services
        services = await services_data.find({}).to_list(length=None)

        if not services:
            await message.reply_text("<b>No services are available at the moment.</b>")
            return

        buttons = [
            [
                InlineKeyboardButton(
                    service["service_name"], callback_data=f"service_{service['_id']}"
                )
            ]
            for service in services
        ]

        await message.reply_photo(
            caption="<b><blockquote>MadxBotz ~ Cloud Paid Service</blockquote>\n\nPlease select a service:</b>",
            photo=IMG_URL,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        await message.reply_text(f"Error: {str(e)}")
