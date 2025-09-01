# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import re, os

# ✅ Fix pattern to match both positive and negative IDs
id_pattern = re.compile(r'^-?\d+$')

API_ID = os.environ.get("API_ID", "25331263")
API_HASH = os.environ.get("API_HASH", "cab85305bf85125a2ac053210bcd1030")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your-bot-token-here")

# Force Subscription channel
FORCE_SUB = os.environ.get("FORCE_SUB", "@JBMultiusage_bot")

DB_NAME = os.environ.get("DB_NAME", "renamevjbot")
DB_URL = os.environ.get(
    "DB_URL",
    "mongodb+srv://rs92573993688:pVf4EeDuRi2o92ex@cluster0.9u29q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
)

FLOOD = int(os.environ.get("FLOOD", "10"))
START_PIC = os.environ.get("START_PIC", "https://te.legra.ph/file/119729ea3cdce4fefb6a1.jpg")

# ✅ Handle admin IDs properly
ADMIN = [int(admin) if id_pattern.match(admin) else admin for admin in os.environ.get("ADMIN", "1955406483").split()]

PORT = os.environ.get("PORT", "8080")
