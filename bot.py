import yt_dlp

def download_audio_with_metadata(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(title)s.%(ext)s',
        'postprocessors': [
            {  # Convert to mp3
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {  # Embed thumbnail
                'key': 'EmbedThumbnail',
            },
            {  # Add metadata like title, artist, album
                'key': 'FFmpegMetadata',
            },
        ],
        'writethumbnail': True,
        'addmetadata': True,
        'prefer_ffmpeg': True,
        'quiet': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return info['title'] + '.mp3'

