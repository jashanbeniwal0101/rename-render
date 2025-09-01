# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import logging
import logging.config
from pyrogram import Client 
from config import API_ID, API_HASH, BOT_TOKEN, FORCE_SUB, PORT
from aiohttp import web
from plugins.web_support import web_server

# Setup logging
logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)


class Bot(Client):

    def __init__(self):
        super().__init__(
            name="WebX-Renamer",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            workers=50,
            plugins={"root": "plugins"},  # Loads all plugin handlers
            sleep_threshold=5,
        )

    async def start(self):
        # Start Pyrogram client
        await super().start()
        me = await self.get_me()

        # Store some useful info
        self.mention = me.mention
        self.username = me.username 
        self.force_channel = FORCE_SUB

        # Force-subscribe check
        if FORCE_SUB:
            try:
                link = await self.export_chat_invite_link(FORCE_SUB)                  
                self.invitelink = link
            except Exception as e:
                logging.warning(e)
                logging.warning("⚠ Bot must be admin in force-sub channel!")             
                self.force_channel = None

        # Setup aiohttp web server
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

        logging.info(f"{me.first_name} ✅ BOT started successfully ✅")

    async def stop(self, *args):
        await super().stop()      
        logging.info("Bot Stopped 🙄")
        

# Start the bot
bot = Bot()
bot.run()
