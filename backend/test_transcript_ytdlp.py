import yt_dlp
import asyncio

async def get_transcript_ytdlp():
    url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
    
    ydl_opts = {
        'quiet': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'vtt',
        'skip_download': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Check for subtitles
            if 'subtitles' in info and info['subtitles']:
                print("✅ Found subtitles!")
                print(f"Available languages: {list(info['subtitles'].keys())}")
            elif 'automatic_captions' in info and info['automatic_captions']:
                print("✅ Found automatic captions!")
                print(f"Available languages: {list(info['automatic_captions'].keys())}")
            else:
                print("❌ No captions found")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(get_transcript_ytdlp())