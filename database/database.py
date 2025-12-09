import motor.motor_asyncio
import re
from datetime import datetime, timedelta
from config import DB_URI, DB_NAME
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters, enums
import pytz

IST = pytz.timezone("Asia/Kolkata")

dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]

users_data = database["users"]
services_data = database["services"]
subscriptions_data = database["subscriptions"]
temp_data = database["temps"]


async def full_userbase():
    return [user["_id"] async for user in users_data.find()]


async def del_user(user_id):
    await users_data.delete_one({"_id": user_id})


async def present_user(user_id: int):
    found = await users_data.find_one({"_id": user_id})
    return bool(found)


async def new_user(user_id):
    new_user_data = {
        "_id": user_id,
        "joined_at": datetime.now(IST).timestamp(),
    }
    await users_data.insert_one(new_user_data)


def calculate_expiry(expiry: str) -> datetime:
    pattern = r"(\d+)(week|day|year|month|hour|min)"
    match = re.match(pattern, expiry)

    if not match:
        raise ValueError(
            "<b>Invalid expiry format. Must be like 1week, 10day, 1year, 1month, 1hour, etc.</b>"
        )

    value, unit = match.groups()
    value = int(value)

    current_time_ist = datetime.now(IST)

    if unit == "week":
        return current_time_ist + timedelta(weeks=value)
    elif unit == "day":
        return current_time_ist + timedelta(days=value)
    elif unit == "year":
        return current_time_ist + timedelta(days=value * 365)
    elif unit == "month":
        return current_time_ist + timedelta(days=value * 30)
    elif unit == "hour":
        return current_time_ist + timedelta(hours=value)
    elif unit == "min":
        return current_time_ist + timedelta(minutes=value)

    return current_time_ist


async def add_or_update_subscription(
    user_id: int, service_id: str, expiry_str: str, razorpay_payment_id: str
):
    expiration_timestamp = calculate_expiry(expiry_str).timestamp()

    new_subscription_data = {
        "user_id": user_id,
        "service_id": service_id,
        "pay_id": razorpay_payment_id,
        "expiry": expiration_timestamp,
        "added_at": datetime.now(IST).timestamp(),
    }

    await subscriptions_data.insert_one(new_subscription_data)
    print(
        f"Subscription added for user {user_id} for service {service_id} until {datetime.fromtimestamp(expiration_timestamp, IST)}"
    )


async def rem_subscription_user(user_id: int, service_id: str):
    await subscriptions_data.delete_one({"user_id": user_id, "service_id": service_id})
    print(f"Subscription removed for user {user_id} for service {service_id}.")


async def check_sub_status(user_id: int, service_id: str):
    subscription = await subscriptions_data.find_one(
        {"user_id": user_id, "service_id": service_id}
    )

    if subscription:
        expiration_timestamp = subscription.get("expiry")
        current_time_ist = datetime.now(IST)

        if expiration_timestamp:
            expiration_date = datetime.fromtimestamp(expiration_timestamp, IST)

            if current_time_ist > expiration_date:
                await subscriptions_data.delete_one(
                    {"user_id": user_id, "service_id": service_id}
                )
                print(
                    f"Subscription expired for user {user_id} for service {service_id}."
                )
                return False, None
            else:
                return True, expiration_date.strftime("%d-%b-%Y %I:%M %p")
        else:
            return False, None
    else:
        print(
            f"No active subscription found for user {user_id} and service {service_id}."
        )
        return False, None


async def verify_subscription(client, user_id: int, service_id: str):
    print(
        f"Checking subscription status for user ID: {user_id} and service ID: {service_id}"
    )

    result = await check_sub_status(user_id, service_id)
    if result:
        is_subscribed, expiration_date = result
        if is_subscribed:
            print(
                f"User '{user_id}' is subscribed to service '{service_id}'. Expiration date: {expiration_date}."
            )
            return True, expiration_date
        else:
            print(f"User '{user_id}' is not subscribed to service '{service_id}'.")
            return False, None
    else:
        print(f"Subscription check failed for user {user_id} for service {service_id}.")
        return False, None


async def verify_subscription_sep(user_id: int, chat_id: int):

    service = await services_data.find_one({"group_ids": {"$in": [str(chat_id)]}})

    if not service:
        print(f"No service found for chat {chat_id}.")
        return False, None

    service_id = service.get("_id")

    if not service_id:
        print(f"Service ID not found for chat {chat_id}.")
        return False, None

    print(service_id)
    subscription = await subscriptions_data.find_one(
        {
            "user_id": int(user_id),
            "service_id": str(service_id),
        }
    )

    if not subscription:
        print(f"No subscription found for user {user_id} in service {service_id}.")
        return False, None

    expiry_timestamp = subscription.get("expiry")

    if not expiry_timestamp:
        print(f"User {user_id} has no expiry set in the subscription.")
        return False, None

    current_time_ist = datetime.now(IST)
    expiry_date = datetime.fromtimestamp(expiry_timestamp, IST)

    if current_time_ist > expiry_date:
        print(f"Subscription for user {user_id} has expired.")
        return False, None
    else:
        return True, expiry_date.strftime("%d-%b-%Y %I:%M %p")
