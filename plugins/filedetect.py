# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message

    # Ensure it's a ForceReply
    if reply_message and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text.strip()
        await message.delete()

        # The actual media message is one level deeper
        file = reply_message.reply_to_message

        # Detect extension
        if not "." in new_name:
            if file and file.document and file.document.file_name:
                extn = file.document.file_name.rsplit('.', 1)[-1]
            elif file and file.video and file.video.file_name:
                extn = file.video.file_name.rsplit('.', 1)[-1]
            elif file and file.audio and file.audio.file_name:
                extn = file.audio.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = f"{new_name}.{extn}"

        await reply_message.delete()

        # Prepare buttons
        buttons = [[InlineKeyboardButton("📁 Document", callback_data="upload_document")]]

        if file.video or file.document:
            buttons.append([InlineKeyboardButton("🎥 Video", callback_data="upload_video")])
        if file.audio:
            buttons.append([InlineKeyboardButton("🎵 Audio", callback_data="upload_audio")])

        await message.reply_text(
            f"**Select the output file type**\n**• File Name :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
