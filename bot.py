import os
import yt_dlp
import tempfile
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from mutagen.id3 import APIC, error
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "8587370514:AAESn5CkMuVocjPvWM3w9bYOfooN0vUJBR4")

# --- Helper Function for Download ---
def download_media(url, format_type="best", quality=None):
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        "outtmpl": output_path,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    if format_type == "audio":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        if quality:
            ydl_opts["format"] = f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        if format_type == "audio":
            file_path = os.path.splitext(file_path)[0] + ".mp3"
            try:
                audio = MP3(file_path, ID3=EasyID3)
                audio["artist"] = info.get("uploader", "Unknown")
                audio["title"] = info.get("title", "Unknown")
                audio.save()
                if info.get("thumbnail"):
                    audio = MP3(file_path, ID3=EasyID3)
                    audio.tags.add(
                        APIC(
                            encoding=3,
                            mime="image/jpeg",
                            type=3,
                            desc="Cover",
                            data=ydl.urlopen(info["thumbnail"]).read(),
                        )
                    )
                    audio.save()
            except error:
                pass
        return file_path, info.get("title", "Unknown")

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎬 Send me any YouTube, TikTok, or Instagram link to download video or audio!")

# --- Handle Links ---
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not any(x in url for x in ["youtube.com", "youtu.be", "tiktok.com", "instagram.com"]):
        await update.message.reply_text("❌ Unsupported link! Send a YouTube, TikTok, or Instagram video link.")
        return

    keyboard = [
        [InlineKeyboardButton("🎥 1080p", callback_data=f"video|1080|{url}"),
         InlineKeyboardButton("🎥 720p", callback_data=f"video|720|{url}")],
        [InlineKeyboardButton("🎥 480p", callback_data=f"video|480|{url}"),
         InlineKeyboardButton("🎥 360p", callback_data=f"video|360|{url}")],
        [InlineKeyboardButton("🎥 240p", callback_data=f"video|240|{url}")],
        [InlineKeyboardButton("🎧 Audio (MP3)", callback_data=f"audio|mp3|{url}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select format:", reply_markup=reply_markup)

# --- Handle Button Press ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("|")
    format_type, quality, url = data[0], data[1], data[2]

    await query.edit_message_text("⬇️ Downloading, please wait...")

    try:
        if format_type == "audio":
            file_path, title = download_media(url, "audio")
            await query.message.reply_audio(audio=open(file_path, "rb"), title=title)
        else:
            file_path, title = download_media(url, "video", quality)
            await query.message.reply_video(video=open(file_path, "rb"), caption=title)

        os.remove(file_path)
    except Exception as e:
        await query.message.reply_text(f"❌ Error: {e}")

# --- MAIN APP ---
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
