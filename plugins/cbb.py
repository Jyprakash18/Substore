from pyrogram import __version__
from bot import Bot
from config import *
import asyncio
import re
from pyrogram import Client, filters, enums
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from pyrogram.enums import ChatMemberStatus
from plugins.start import (
    user_pagination_data,
    get_user_list_page,
    PAGE_SIZE,
    send_subscription_page,
)
from database.database import (
    subscriptions_data,
    services_data,
    temp_data,
    add_or_update_subscription,
    calculate_expiry,
)
from bson import ObjectId
from datetime import datetime
from helper_func import *
import razorpay
import pytz
import uuid
from plugins.useless import show_services

IST = pytz.timezone("Asia/Kolkata")
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET_KEY))


@Bot.on_callback_query()
async def cb_handler(client: Bot, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id

    if data == "close":
        await query.message.delete()
        try:
            await query.message.reply_to_message.delete()
        except:
            pass

    elif data.startswith("service_"):
        try:
            service_id = data.split("_")[1]
            service = await services_data.find_one({"_id": ObjectId(service_id)})

            if not service:
                await query.message.reply_text("Service not found.")
                return

            plans = service["plans"]
            buttons = [
                [
                    InlineKeyboardButton(
                        f"{plan} - ₹{details['price']}",
                        callback_data=f"plan_{service_id}_{plan}",
                    )
                ]
                for plan, details in plans.items()
            ]
            if service["description"]:
                ser_description = f"Description:\n\n{service['description']}"
            else:
                ser_description = "Description: N/A"

            await query.message.edit_text(
                f"<b><blockquote>MadxBotz ~ Cloud Paid Service</blockquote>\n\n"
                f"Service: <code>{service['service_name']}</code>\n\n"
                f"{ser_description}\n\n"
                "Please select a plan:</b>",
                reply_markup=InlineKeyboardMarkup(buttons),
            )

        except Exception as e:
            await query.message.reply_text(f"Error: {str(e)}")

    elif data.startswith("plan_"):
        try:
            _, service_id, plan_duration = data.split("_")
            service = await services_data.find_one({"_id": ObjectId(service_id)})

            if not service or plan_duration not in service["plans"]:
                await query.message.reply_text("Plan not found.")
                return

            price = service["plans"][plan_duration]["price"]

            reference_id = f"ref_{query.from_user.id}_{str(uuid.uuid4())[:6]}"

            payment_link_data = {
                "amount": int(price * 100),
                "currency": "INR",
                "accept_partial": False,
                "reference_id": reference_id,
                "description": f"Payment for {plan_duration} subscription",
                "customer": {
                    "name": "MadxBotz",
                    "contact": "7010947275",
                },
                "notify": {"sms": False, "email": False},
                "reminder_enable": False,
                "callback_url": f"{BASE_URL}payment-success",
                "callback_method": "get",
            }
            print(payment_link_data)

            payment_link = razorpay_client.payment_link.create(payment_link_data)
            print(payment_link)

            payment_url = payment_link["short_url"]
            print(payment_url)

            await query.message.edit_text(
                f"<b><blockquote>MadxBotz ~ Cloud Paid Service</blockquote>\n\nSelected Plan: {plan_duration} - ₹{price}\n\nClick below to proceed with the payment:</b>",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Pay Now", url=payment_url)]]
                ),
            )

            try:
                await temp_data.insert_one(
                    {
                        "user_id": query.from_user.id,
                        "service_id": service_id,
                        "plan_duration": plan_duration,
                        "order_id": payment_link["id"],
                        "created_at": datetime.now(IST).timestamp(),
                    }
                )
            except Exception as e:
                await query.message.reply_text(f"Insert Error: {str(e)}")

        except Exception as e:
            await query.message.reply_text(f"Error: {str(e)}")
            print(f"Error: {e}")

    elif data.startswith("generate_"):
        user_id = query.from_user.id
        service_id = query.data.split("_", 1)[1]

        service_data = await services_data.find_one({"_id": ObjectId(service_id)})
        if not service_data:
            await query.message.edit_text("Invalid service ID.")
            return

        group_ids = service_data.get("group_ids", [])
        banned_in_groups = []

        buttons = []
        for group_id in group_ids:
            try:
                group_info = await client.get_chat(group_id)
                group_name = group_info.title

                # Create invite link
                invite_link = await client.create_chat_invite_link(
                    chat_id=group_id, member_limit=1
                )

                # Use group name in the button text
                buttons.append(
                    [InlineKeyboardButton(f"{group_name}", url=invite_link.invite_link)]
                )
            except Exception as e:
                await query.message.edit_text(
                    f"Failed to create invite link for group {group_id}: {e}"
                )
                return

        # Unban user if necessary
        for group_id in group_ids:
            if await is_user_banned(client, group_id, user_id):
                try:
                    await client.unban_chat_member(group_id, user_id)
                    banned_in_groups.append(group_id)
                    print(f"User unbanned from group {group_id}")
                except Exception as e:
                    await query.message.edit_text(
                        f"Failed to unban user from group {group_id}: {e}"
                    )
                    return

        # Ensure buttons are passed as a list of rows, not nested
        if buttons:
            await query.message.edit_text(
                f"<b><blockquote>MadxBotz ~ Cloud Paid Service</blockquote>\n\nHere are your invite links to join chats:\n\n<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>",
                reply_markup=InlineKeyboardMarkup(buttons),  # Pass buttons directly
            )
        else:
            await query.message.edit_text("No invite links could be generated.")

    elif data.startswith("page_"):
        try:
            page = int(data.split("_")[1])
            users = user_pagination_data.get(user_id, [])

            if page < 0 or page >= (len(users) + PAGE_SIZE - 1) // PAGE_SIZE:
                await query.answer("No More Pages Available.")
                return

            user_list = await get_user_list_page(client, page, users)

            keyboard = []
            if page > 0:
                keyboard.append(
                    InlineKeyboardButton("Previous", callback_data=f"page_{page - 1}")
                )
            if (page + 1) * PAGE_SIZE < len(users):
                keyboard.append(
                    InlineKeyboardButton("Next", callback_data=f"page_{page + 1}")
                )

            reply_markup = InlineKeyboardMarkup([keyboard])

            await query.message.edit_text(
                text="\n".join(user_list) if user_list else "No users found.",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
            await query.answer()

        except (IndexError, ValueError) as e:
            print(f"Error in pagination_handler: {e}")
            await query.answer("An error occurred during pagination.")

    elif data.startswith("serviceview_"):
        service_id = query.data.split("_", 1)[1]

        service_data = await services_data.find_one({"_id": ObjectId(service_id)})
        if not service_data:
            await query.message.edit_text("Invalid service ID.")
            return

        service_name = service_data.get("service_name", "Unnamed Service")
        group_ids = service_data.get("group_ids", [])
        created_at = service_data.get("created_at", "Unknown date")

        plans = service_data.get("plans", {})
        plans_list = "\n".join(
            [
                f"• {duration} - ₹{details['price']}"
                for duration, details in plans.items()
            ]
        )

        group_list = (
            "\n".join([f"• {gid}" for gid in group_ids])
            if group_ids
            else "No groups available."
        )

        response_text = (
            f"<b>Service: {service_name}</b>\n\n"
            f"<b>Service ID:</b> <code>{service_id}</code>\n"
            f"<b>Created At:</b> {created_at}\n\n"
            f"<b>Plans:</b>\n{plans_list}\n\n"
            f"<b>Groups:</b>\n{group_list}"
        )

        await query.message.edit_text(
            response_text,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Back", callback_data="services_back")]]
            ),
        )

    elif data == "services_back":
        await show_services(client, query.message)

    elif data.startswith("sub_page_"):
        page_number = int(data.split("_")[-1])

        user_subs = await subscriptions_data.find({"user_id": user_id}).to_list(
            length=None
        )

        await send_subscription_page(client, query.message, user_subs, page_number)

        await query.answer()

    elif data.startswith("manadd_"):
        parts = data.split("_")
        service_id = parts[1]
        prem_user_id = int(parts[2])

        # Prompt for expiry time
        expiry_message = await client.ask(
            chat_id=query.from_user.id,
            text="<b>Enter the subscription duration (e.g., 1month, 2weeks):</b>",
            timeout=120,
        )
        expiry = expiry_message.text.strip()

        # Calculate expiry timestamp
        try:
            expiry_timestamp = calculate_expiry(expiry).timestamp()
        except ValueError as e:
            await query.message.reply_text(f"Invalid expiry format: {str(e)}")
            return

        # Define a fixed pay_id for the subscription
        pay_id = "Paid Using UPI"

        # Add or update subscription in the database
        await add_or_update_subscription(prem_user_id, service_id, expiry, pay_id)

        # Confirm to the admin
        await client.send_message(
            chat_id=query.from_user.id,
            text=f"Subscription added with service ID: {service_id}.",
        )

        # Notify the subscribed user with join link
        await client.send_message(
            chat_id=prem_user_id,
            text="New Subscription Added.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Create Join Link",
                            url=f"https://t.me/MadxSubbot?start=serid_{service_id}",
                        )
                    ]
                ]
            ),
        )

        # Log the new subscription
        await client.send_message(
            chat_id=log_chat_id,
            text=f"New subscription added for user {prem_user_id} to service {service_id}.",
            disable_web_page_preview=True,
        )
