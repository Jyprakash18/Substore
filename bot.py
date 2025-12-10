from aiohttp import web
from plugins import web_server
from plugins import routes
import asyncio
import pyrogram
import pyrogram.utils
from pyrogram import Client
from pyrogram.enums import ParseMode
import sys
from datetime import datetime
from helper_func import ping_server, check_subs_dtl
from plugins.funct_manage import remove_expired_subscriptions

from config import *


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={"root": "plugins"},
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN,
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()
        for chat_id in LOG_CHAT:
            await self.send_message(chat_id, "Bot Restarted")
        self.LOGGER(__name__).info(
            f"Bot Running..!\n\nCreated by \nhttps://t.me/MadxBotz "
        )
        self.LOGGER(__name__).info(
            f""" \n\n
███╗   ███╗ █████╗ ██████╗ ██╗  ██╗██████╗  ██████╗ ████████╗███████╗
████╗ ████║██╔══██╗██╔══██╗╚██╗██╔╝██╔══██╗██╔═══██╗╚══██╔══╝╚══███╔╝
██╔████╔██║███████║██║  ██║ ╚███╔╝ ██████╔╝██║   ██║   ██║     ███╔╝ 
██║╚██╔╝██║██╔══██║██║  ██║ ██╔██╗ ██╔══██╗██║   ██║   ██║    ███╔╝  
██║ ╚═╝ ██║██║  ██║██████╔╝██╔╝ ██╗██████╔╝╚██████╔╝   ██║   ███████╗
╚═╝     ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚═════╝  ╚═════╝    ╚═╝   ╚══════╝"""
        )
        self.username = usr_bot_me.username
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()
        asyncio.create_task(ping_server())
        asyncio.create_task(check_subs_dtl(self))
        asyncio.create_task(remove_expired_subscriptions())

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")
