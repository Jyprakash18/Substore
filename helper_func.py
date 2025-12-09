import asyncio
import pytz
from config import *
import aiohttp
import traceback
from pyrogram import enums
from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.errors import UserNotParticipant, ChatAdminRequired
from plugins.funct_manage import remove_from_db

from database.database import services_data


IST = pytz.timezone("Asia/Kolkata")


async def check_subs_dtl(self):
    print(f"5 mins Checking Function is Starting.")
    while True:
        await asyncio.sleep(300)
        try:
            await remove_from_db(self)
            print(f"5 mins Checking Function Completed and Starting Next Cycle.")
        except Exception as e:
            print(f"Error checking subscriptions: {str(e)}")


async def ping_server():
    while True:
        await asyncio.sleep(120)
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.get(BASE_URL) as resp:
                    logging.info("Pinged server with response: {}".format(resp.status))
        except TimeoutError:
            logging.warning("Couldn't connect to the site URL..!")
        except Exception:
            traceback.print_exc()


async def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time


async def get_remaining_time(expiry_timestamp: int) -> str:
    expiry_date = datetime.fromtimestamp(expiry_timestamp, IST)
    current_time = datetime.now(IST)

    if expiry_date < current_time:
        return "Subscription expired"

    remaining_time = expiry_date - current_time
    days, seconds = remaining_time.days, remaining_time.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    remaining_time_str = f"{days} days, {hours} hours, {minutes} minutes"
    return remaining_time_str


async def is_user_banned(client: Client, group_id: int, user_id: int) -> bool:
    try:
        chat_member = await client.get_chat_member(chat_id=group_id, user_id=user_id)
        return chat_member.status in [
            enums.ChatMemberStatus.BANNED,
            enums.ChatMemberStatus.RESTRICTED,
        ]
    except UserNotParticipant:
        print(f"User is not a Participant {group_id}.")
        return False
    except ChatAdminRequired:
        print(f"Chat admin privileges required to check status for group {group_id}.")
        return False
    except Exception as e:
        print(f"Error checking if user is banned: {str(e)}")
        return False


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
