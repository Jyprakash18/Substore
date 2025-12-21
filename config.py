import os
import logging
from logging.handlers import RotatingFileHandler

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "7996302052:AAEvYi8mQUi7PLEM5B_bOMgUsKoKuiOCbb0")

APP_ID = int(os.environ.get("APP_ID", "29270492"))

API_HASH = os.environ.get("API_HASH", "c0ff4a728d5da8de25807766b2901111")

OWNER_ID = int(os.environ.get("OWNER_ID", "7990200132"))

PORT = os.environ.get("PORT", "8080")  # dont edit unless you deploying in vps

DB_URI = os.environ.get(
    "DATABASE_URL",
    "mongodb+srv://jay:hanuman@hanuman.tgwobmu.mongodb.net/?retryWrites=true&w=majority&appName=Hanuman",
)

DB_NAME = os.environ.get("DATABASE_NAME", "jayhanuman")
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_live_RrqnjjhwEqNTQO")
RAZORPAY_SECRET_KEY = os.environ.get("RAZORPAY_SECRET_KEY", "LMNXV8GEUJiyYAK3Gsy6eeTp")

TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

LOG_CHAT = list(
    map(
        int,
        os.environ.get(
            "LOG_CHAT",
            "-1003005264320",
        ).split(),
    )
)

log_chat_id = LOG_CHAT[0]

IMG_URL = os.environ.get("IMG_URL", "https://telegra.ph/file/0ed351c8605c23e8cae79.jpg")

POWERED_BY = os.environ.get("POWERED_BY", "@Dd_Lovely")

BASE_URL = os.environ.get("BASE_URL", "https://starfish-app-kj4sn.ondigitalocean.app/")


try:
    ADMINS = [int(x) for x in os.environ.get("ADMINS", "7990200132").split()]
except ValueError:
    raise Exception("Your Admins list does not contain valid integers.")

try:
    AUTHS = [int(x) for x in os.environ.get("AUTHS", "5694062287").split()]
except ValueError:
    raise Exception("Your Auths list does not contain valid integers.")

USER_REPLY_TEXT = f"<b>Available Commands\n\n/mysub - To Check Your Subscription Details.\n\n/plans - To Check Available Plans.\n\n<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>"

ADMINS.append(7990200132)
AUTHS.append(5694062287)
ADMINS.append(7990200132)

LOG_FILE_NAME = "madxbotz.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler(LOG_FILE_NAME, maxBytes=50000000, backupCount=10),
        logging.StreamHandler(),
    ],
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
