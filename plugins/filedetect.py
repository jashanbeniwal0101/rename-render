# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    # Get the replied message
    reply_message = message.reply_to_message
    
    # Check if reply was to ForceReply
    if reply_message and reply_message.reply_markup and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text.strip()
        await message.delete()

        # Get original file message
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message

        if not file or not file.media:
            return await message.reply_text("❌ File not found. Try again.")

        # Extract media
        media = getattr(file, file.media.value)

        # If user did not type extension, add it
        if "." not in new_name:
            if media.file_name and "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = f"{new_name}.{extn}"

        # Delete the force-reply message
        await reply_message.delete()

        # Build buttons
        buttons = [[InlineKeyboardButton("📁 Document", callback_data="upload_document")]]

        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            buttons.append([InlineKeyboardButton("🎥 Video", callback_data="upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            buttons.append([InlineKeyboardButton("🎵 Audio", callback_data="upload_audio")])

        # Send choice to user
        await message.reply_text(
            f"**Select the output file type**\n\n**📂 File Name:** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
