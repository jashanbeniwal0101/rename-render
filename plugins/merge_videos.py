import os
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from helper.utils import progress_for_pyrogram

# Dictionary to store user's videos
user_videos = {}

@Client.on_message(filters.private & filters.video)
async def collect_videos(client, message):
    user_id = message.from_user.id

    # Download video to server
    file_path = await client.download_media(message)

    if user_id not in user_videos:
        user_videos[user_id] = []
    user_videos[user_id].append(file_path)

    total_size = sum(os.path.getsize(f) for f in user_videos[user_id]) / (1024 * 1024)
    total_count = len(user_videos[user_id])

    await message.reply_text(
        f"✅ Added Video: **{os.path.basename(file_path)}**\n\n"
        f"📂 Total Videos: {total_count}\n"
        f"📦 Total Size: {total_size:.2f} MB\n\n"
        "👉 Send more videos or press **Merge Videos** when ready.",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔀 Merge Videos", callback_data="merge")],
                [InlineKeyboardButton("❌ Cancel", callback_data="cancel_merge")]
            ]
        )
    )


@Client.on_callback_query(filters.regex("cancel_merge"))
async def cancel_merge(client, query):
    user_id = query.from_user.id
    user_videos.pop(user_id, None)
    await query.message.edit("❌ Merge cancelled, all videos cleared.")


@Client.on_callback_query(filters.regex("merge"))
async def start_merge(client, query):
    user_id = query.from_user.id
    if user_id not in user_videos or len(user_videos[user_id]) < 2:
        await query.answer("⚠️ You need at least 2 videos to merge!", show_alert=True)
        return

    await query.message.edit("⚙️ Checking and converting videos if needed...")

    converted_files = []
    for idx, input_file in enumerate(user_videos[user_id], start=1):
        converted_file = f"{user_id}_converted_{idx}.mp4"

        # Convert each video into uniform format
        cmd = f"ffmpeg -i '{input_file}' -c:v libx264 -preset veryfast -crf 23 -c:a aac -ar 44100 -ac 2 '{converted_file}' -y"
        process = await asyncio.create_subprocess_shell(cmd)
        await process.communicate()

        if os.path.exists(converted_file):
            converted_files.append(converted_file)
        else:
            await query.message.edit(f"❌ Failed to convert {os.path.basename(input_file)}")
            return

    # Create file list for concat
    list_file = f"{user_id}_list.txt"
    with open(list_file, "w") as f:
        for path in converted_files:
            f.write(f"file '{os.path.abspath(path)}'\n")

    output_file = f"merged_{user_id}.mp4"
    cmd = f"ffmpeg -f concat -safe 0 -i {list_file} -c copy '{output_file}' -y"

    await query.message.edit("🔄 Merging videos, please wait...")

    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await process.communicate()

    if not os.path.exists(output_file):
        await query.message.edit("❌ Merge failed.")
        return

    c_time = time.time()
    await client.send_video(
        chat_id=user_id,
        video=output_file,
        caption="✅ Here is your merged video.",
        progress=progress_for_pyrogram,
        progress_args=(query.message, c_time)
    )

    # Cleanup
    for f in user_videos[user_id]:
        if os.path.exists(f):
            os.remove(f)
    for f in converted_files:
        if os.path.exists(f):
            os.remove(f)
    if os.path.exists(list_file):
        os.remove(list_file)
    if os.path.exists(output_file):
        os.remove(output_file)

    user_videos.pop(user_id, None)
    await query.message.delete()
