from pyrogram import Client, filters
from pyrogram.types import Message
from bot import Bot
from database.database import verify_subscription, verify_subscription_sep
from config import *
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)


@Bot.on_message(filters.group & ~filters.user(ADMINS))
async def check_subscription_in_group(client: Client, message: Message):

    current_chat_id = message.chat.id

    if message.from_user is None:
        return

    user_id = message.from_user.id

    if user_id in ADMINS or user_id in AUTHS:
        return

    is_subscribed, expiration_date = await verify_subscription_sep(
        user_id, current_chat_id
    )

    if not is_subscribed:
        try:
            # Check the user's status in the current chat
            member = await client.get_chat_member(current_chat_id, user_id)
            if member.status not in [
                ChatMemberStatus.BANNED,
                ChatMemberStatus.RESTRICTED,
                ChatMemberStatus.LEFT,
            ]:
                # Ban the user from the current chat only
                await client.ban_chat_member(current_chat_id, user_id)
                print(
                    f"User {user_id} removed from group {current_chat_id} due to expired subscription."
                )
            else:
                print(
                    f"User {user_id} is not present in group {current_chat_id} (status: {member.status})."
                )
        except Exception as e:
            print(
                f"Failed to check or remove user {user_id} from group {current_chat_id}: {e}"
            )

        try:
            await client.send_message(
                user_id,
                f"""
<b><blockquote>Subscription End Notification</blockquote>

Your subscription has expired today,
and you have been removed from the group.
To renew your subscription, please
send /buyservice for Subscribe new Service.

Thank you for choosing us!

<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>""",
            )

            reply_markup = [
                [
                    InlineKeyboardButton("View User", url=f"tg://user?id={user_id}"),
                ]
            ]
            try:
                telegram_user = await client.get_users(user_id)
                first_name = telegram_user.first_name
                username = (
                    telegram_user.username if telegram_user.username else "No Username"
                )
            except Exception as e:
                first_name = "Unknown"
                username = "None"
                print(f"Failed to fetch additional user details: {e}")

            await client.send_message(
                log_chat_id,
                f"""<b>{first_name} | {user_id} has been removed automatically from group {current_chat_id} as their subscription expired.</b>
                """,
                reply_markup=InlineKeyboardMarkup(reply_markup),
            )
        except Exception as e:
            print(f"Failed to send message to user {user_id}: {e}")
    else:
        print(
            f"User {user_id} is still subscribed. Subscription valid until {expiration_date}."
        )
