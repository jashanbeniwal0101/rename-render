# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on telegram @KingVJ01

import os
import re
import time
import logging
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from PIL import Image

import humanize
from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

from helper.utils import progress_for_pyrogram, convert
from helper.database import db

log = logging.getLogger(__name__)

# ensure downloads dir exists
os.makedirs("downloads", exist_ok=True)

# === Helpers ===
_RE_CODEBLOCK = re.compile(r'```(.*?)```', re.DOTALL)
_RE_AFTER_COLON = re.compile(r'[:\-]{1,2}\s*(.+)$', re.IGNORECASE | re.DOTALL)


def extract_new_filename_from_text(text: str) -> str:
    """
    Try to extract filename from message text. Priority:
      1) triple-backtick code block: ```name.ext```
      2) content after a ':-' or ':' pattern
      3) full text fallback (stripped)
    """
    if not text:
        return ""
    # 1) codeblock
    m = _RE_CODEBLOCK.search(text)
    if m:
        return m.group(1).strip()
    # 2) after colon/dash pattern
    m = _RE_AFTER_COLON.search(text)
    if m:
        return m.group(1).strip().strip('`" ')
    # 3) fallback
    return text.strip().strip('`" ')


def make_unique_path(path: str) -> str:
    """
    If path exists, append (1), (2), ... before extension to make unique.
    """
    base, ext = os.path.splitext(path)
    i = 1
    newpath = path
    while os.path.exists(newpath):
        newpath = f"{base}({i}){ext}"
        i += 1
    return newpath


# === Callback: cancel ===
@Client.on_callback_query(filters.regex(r'^(cancel)$'))
async def cancel_cb(client, callback_query):
    """Delete the message with inline buttons (and acknowledge the callback)."""
    try:
        await callback_query.message.delete()
    except Exception:
        pass
    await callback_query.answer()


# === Callback: rename (send ForceReply) ===
@Client.on_callback_query(filters.regex(r'^(rename)$'))
async def rename_cb(client, callback_query):
    """
    When user clicks 'rename' button:
      - delete the button message
      - send a ForceReply asking for the new filename (replying to the original media message)
    """
    try:
        # original message that contained the file is the message we replied to when sending buttons
        orig_msg = callback_query.message.reply_to_message
        if not orig_msg:
            await callback_query.answer("Original message not found.", show_alert=True)
            return

        # delete the buttons message (optional)
        try:
            await callback_query.message.delete()
        except Exception:
            pass

        # send ForceReply to the user, replying to the original file message
        await orig_msg.reply_text(
            "__𝙿𝚕𝚎𝚊𝚜𝚎 𝙴𝚗𝚝𝚎𝚛 𝙽𝚎𝚠 𝙵𝚒𝚕𝚎𝙽𝚊𝚖𝚎...__",
            reply_to_message_id=orig_msg.id,
            reply_markup=ForceReply(selective=True)
        )
        await callback_query.answer()
    except Exception as e:
        log.exception("rename_cb error: %s", e)
        await callback_query.answer("An error occurred.", show_alert=True)


# === Message handler: user replies to ForceReply with new filename ===
@Client.on_message(filters.private & filters.reply & filters.text)
async def handle_rename_reply(client, message):
    """
    This handles the user's reply to the ForceReply we sent in `rename_cb`.
    It:
      - validates the Flow
      - constructs a message that shows the chosen filename and inline buttons for output type
      - the inline-button message is replied to the original media message so callback handlers can access it
    """
    try:
        reply_to = message.reply_to_message  # this is the ForceReply message
        # ensure this was indeed a ForceReply we created
        if not reply_to or not getattr(reply_to, "reply_markup", None):
            return
        # The ForceReply should itself be replying to the original file message
        orig_file_msg = reply_to.reply_to_message
        if not orig_file_msg:
            # sometimes need to re-fetch
            fetched = await client.get_messages(message.chat.id, reply_to.id)
            orig_file_msg = fetched.reply_to_message if fetched else None
        if not orig_file_msg:
            await message.reply_text("Couldn't find original file message. Please try again.", quote=True)
            return

        new_name = message.text.strip()
        # remove surrounding backticks if user typed them
        new_name = new_name.strip('`" ')

        # delete the user's reply (keep chat clean)
        try:
            await message.delete()
        except Exception:
            pass

        # get media object safely
        if orig_file_msg.media == MessageMediaType.VIDEO:
            media = orig_file_msg.video
        elif orig_file_msg.media == MessageMediaType.DOCUMENT:
            media = orig_file_msg.document
        elif orig_file_msg.media == MessageMediaType.AUDIO:
            media = orig_file_msg.audio
        else:
            await client.send_message(message.chat.id, "Unsupported media type.", reply_to_message_id=orig_file_msg.id)
            return

        # ensure extension present
        if "." not in new_name:
            media_filename = getattr(media, "file_name", None)
            if media_filename and "." in media_filename:
                ext = media_filename.rsplit(".", 1)[1]
            else:
                ext = "mkv"
            new_name = f"{new_name}.{ext}"

        # delete the ForceReply message (tidy)
        try:
            await reply_to.delete()
        except Exception:
            pass

        # prepare buttons
        buttons = [[InlineKeyboardButton("📁 𝙳𝙾𝙲𝚄𝙼𝙴𝙽𝚃", callback_data="upload_document")]]
        if orig_file_msg.media in (MessageMediaType.VIDEO, MessageMediaType.DOCUMENT):
            buttons.append([InlineKeyboardButton("🎥 𝚅𝙸𝙳𝙴𝙾", callback_data="upload_video")])
        elif orig_file_msg.media == MessageMediaType.AUDIO:
            buttons.append([InlineKeyboardButton("🎵 𝙰𝚄𝙳𝙸𝙾", callback_data="upload_audio")])

        msg_text = f"**Select the output file type**\n**• File Name :-**```{new_name}```"
        await client.send_message(
            chat_id=message.chat.id,
            text=msg_text,
            reply_to_message_id=orig_file_msg.id,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        log.exception("handle_rename_reply error: %s", e)
        try:
            await message.reply_text("An internal error occurred while processing your filename.", quote=True)
        except Exception:
            pass


# === Callback: upload (document|video|audio) ===
@Client.on_callback_query(filters.regex(r'^upload_(document|video|audio)$'))
async def upload_cb(client, callback_query):
    """
    Handles the upload buttons. Steps:
      - extract the selected output type from callback_data
      - parse the new filename from the bot message text (we created it earlier)
      - download the original file (reply_to_message)
      - rename the downloaded file to new filename
      - optionally get duration/metadata
      - prepare/resize thumbnail
      - send file to the user who clicked (use callback_query.from_user.id)
    """
    try:
        await callback_query.answer()  # remove spinner asap
        out_type = callback_query.data.split("_", 1)[1]  # document|video|audio
        bot_msg = callback_query.message  # the bot message with buttons & filename
        user_id = callback_query.from_user.id  # IMPORTANT: use from_user.id, not message.chat.id

        # Extract filename from bot message text
        text = bot_msg.text or bot_msg.caption or ""
        new_filename = extract_new_filename_from_text(text)
        if not new_filename:
            await callback_query.message.edit("Filename not found. Please rename again.", reply_markup=None)
            return

        # sanitize filename a bit
        new_filename = new_filename.strip().replace("\n", " ").strip()
        # ensure downloads folder
        os.makedirs("downloads", exist_ok=True)
        file_dest = os.path.join("downloads", new_filename)
        file_dest = make_unique_path(file_dest)

        # original file message should be the message this bot message replied to
        file_msg = bot_msg.reply_to_message
        if not file_msg:
            await callback_query.message.edit("Original file message not found.", reply_markup=None)
            return

        # Show downloading status (edit the button message)
        ms = await bot_msg.edit("⚠️ __**Please wait...**__\n__Downloading file to my server...__")
        start_time = time.time()
        try:
            # download returns the path
            downloaded_path = await client.download_media(
                message=file_msg,
                file_name=None,  # let pyrogram choose
                progress=progress_for_pyrogram,
                progress_args=(ms, start_time)
            )
            if not downloaded_path:
                raise RuntimeError("Download returned empty path.")
        except Exception as e:
            log.exception("download_media error: %s", e)
            await ms.edit(f"❌ Download failed: {e}")
            return

        # rename downloaded file to our new filename (safe)
        try:
            # downloaded_path may be full path; just replace with our unique file_dest
            os.replace(downloaded_path, file_dest)
        except Exception:
            # as fallback try copy+remove
            try:
                import shutil
                shutil.move(downloaded_path, file_dest)
            except Exception as e:
                log.exception("rename/move error: %s", e)
                await ms.edit(f"❌ Error preparing file: {e}")
                # attempt cleanup
                try:
                    if os.path.exists(downloaded_path):
                        os.remove(downloaded_path)
                except Exception:
                    pass
                return

        # get duration metadata if possible
        duration = 0
        try:
            parser = createParser(file_dest)
            metadata = extractMetadata(parser) if parser else None
            if metadata and metadata.has("duration"):
                duration = metadata.get("duration").seconds
        except Exception:
            pass

        # get media object (from original message) safely
        media = file_msg.document or file_msg.video or file_msg.audio

        # filesize for caption: prefer media.file_size, else os.path.getsize
        try:
            file_size_bytes = getattr(media, "file_size", None) or os.path.getsize(file_dest)
        except Exception:
            file_size_bytes = None

        # caption from DB (if any)
        c_caption = await db.get_caption(user_id)
        if c_caption:
            try:
                caption = c_caption.format(
                    filename=new_filename,
                    filesize=humanize.naturalsize(file_size_bytes) if file_size_bytes else "Unknown",
                    duration=convert(duration)
                )
            except Exception as e:
                await ms.edit(f"❌ Caption formatting error: {e}")
                return
        else:
            caption = f"**{new_filename}**"

        # prepare thumbnail
        ph_path = None
        try:
            c_thumb = await db.get_thumbnail(user_id)
            if c_thumb:
                ph_path = await client.download_media(c_thumb)
            else:
                # try to fetch thumbnail from media itself
                thumb_file_id = None
                # video/document might have 'thumb' or 'thumbs'
                if getattr(media, "thumb", None):
                    # media.thumb could be PhotoSize
                    try:
                        thumb_file_id = media.thumb.file_id
                    except Exception:
                        thumb_file_id = None
                elif getattr(media, "thumbs", None):
                    try:
                        thumb_file_id = media.thumbs[0].file_id
                    except Exception:
                        thumb_file_id = None

                if thumb_file_id:
                    ph_path = await client.download_media(thumb_file_id)

            # if we have a path, convert and resize properly (assign result of resize)
            if ph_path and os.path.exists(ph_path):
                img = Image.open(ph_path).convert("RGB")
                img = img.resize((320, 320))
                img.save(ph_path, "JPEG")
        except Exception:
            log.exception("thumbnail preparation error")
            # don't fail the whole flow for thumbnail issues
            ph_path = None

        # upload step
        await ms.edit("⚠️ __**Please wait...**__\n__Uploading file...__")
        start_time = time.time()
        try:
            if out_type == "document":
                await client.send_document(
                    chat_id=user_id,
                    document=file_dest,
                    thumb=ph_path,
                    caption=caption,
                    progress=progress_for_pyrogram,
                    progress_args=(ms, start_time)
                )
            elif out_type == "video":
                await client.send_video(
                    chat_id=user_id,
                    video=file_dest,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration or None,
                    progress=progress_for_pyrogram,
                    progress_args=(ms, start_time)
                )
            elif out_type == "audio":
                await client.send_audio(
                    chat_id=user_id,
                    audio=file_dest,
                    caption=caption,
                    thumb=ph_path,
                    duration=duration or None,
                    progress=progress_for_pyrogram,
                    progress_args=(ms, start_time)
                )
            else:
                await ms.edit("❌ Unsupported output type.")
                return
        except Exception as e:
            log.exception("upload/send error: %s", e)
            await ms.edit(f"❌ Upload failed: {e}")
            # cleanup local files
            try:
                if os.path.exists(file_dest):
                    os.remove(file_dest)
                if ph_path and os.path.exists(ph_path):
                    os.remove(ph_path)
            except Exception:
                pass
            return

        # success -> cleanup and delete status message
        try:
            await ms.delete()
        except Exception:
            pass

        # remove local files
        try:
            if os.path.exists(file_dest):
                os.remove(file_dest)
            if ph_path and os.path.exists(ph_path):
                os.remove(ph_path)
        except Exception:
            pass

    except Exception as e:
        log.exception("upload_cb general error: %s", e)
        try:
            await callback_query.message.edit("An unexpected error occurred.", reply_markup=None)
        except Exception:
            pass
