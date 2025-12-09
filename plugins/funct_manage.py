from pyrogram import Client
from database.database import verify_subscription
from config import *
import pytz
from datetime import timedelta, datetime

from pyrogram import enums
from database.database import subscriptions_data, services_data
from helper_func import *
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)

IST = pytz.timezone("Asia/Kolkata")


def format_remaining_time(time_diff: timedelta) -> str:
    days = time_diff.days
    hours, remainder = divmod(time_diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    time_str = ""

    if days > 0:
        time_str += f"{days}d "
    if hours > 0:
        time_str += f"{hours}h "
    if minutes > 0:
        time_str += f"{minutes}m "
    if seconds > 0:
        time_str += f"{seconds}s"

    return time_str.strip() if time_str else "less than a second"


async def handle_expired_user(user_id: int, service_id: int):
    try:
        service = await services_data.find_one({"_id": service_id})
        if service is None:
            print(f"Service with ID {service_id} not found.")
            return

        result = await subscriptions_data.delete_one(
            {"user_id": user_id, "service_id": service_id}
        )

        if result.deleted_count > 0:
            print(
                f"Subscription data for user {user_id} and service {service_id} has been removed from the database."
            )
        else:
            print(
                f"No subscription data found for user {user_id} and service {service_id}."
            )

    except Exception as e:
        print(f"Error while handling expired user {user_id}: {e}")


async def remove_from_db(client: Client):
    now = datetime.now(IST)
    subscriptions = await subscriptions_data.find({}).to_list(length=None)

    for subscription in subscriptions:
        user_id = subscription.get("user_id")
        service_id = subscription.get("service_id")
        expiry_timestamp = subscription.get("expiry")
        expiry_date = (
            datetime.fromtimestamp(expiry_timestamp, IST) if expiry_timestamp else None
        )

        if expiry_date and expiry_date <= now:
            print(f"User {user_id} has expired, handling expiry.")
            await handle_expired_user(client, user_id, service_id)


async def remove_expired_subscriptions():
    now = datetime.now(IST)

    while True:
        try:
            result = await subscriptions_data.delete_many(
                {"expiry": {"$lte": now.timestamp()}}
            )
            print(
                f"Removed {result.deleted_count} expired subscriptions from the database."
            )
        except Exception as e:
            print(f"Error while removing expired subscriptions: {e}")
        await asyncio.sleep(300)
