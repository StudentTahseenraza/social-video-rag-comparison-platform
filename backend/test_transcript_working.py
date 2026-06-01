import yt_dlp
import json

def get_youtube_transcript(video_id):
    """Extract transcript using yt-dlp"""
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitlesformat': 'json3',
        'subtitleslangs': ['en'],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info
            info = ydl.extract_info(url, download=False)
            
            # Check for automatic captions
            if 'automatic_captions' in info and 'en' in info['automatic_captions']:
                captions = info['automatic_captions']['en']
                if captions:
                    print(f"✅ Found automatic captions!")
                    
                    # Get the first caption URL
                    caption_url = captions[0]['url']
                    print(f"Caption URL: {caption_url}")
                    
                    # Download caption content
                    import requests
                    response = requests.get(caption_url)
                    
                    if response.status_code == 200:
                        # Parse JSON3 format
                        data = response.json()
                        
                        if 'events' in data:
                            text_parts = []
                            for event in data['events']:
                                if 'segs' in event:
                                    for seg in event['segs']:
                                        if 'utf8' in seg:
                                            text_parts.append(seg['utf8'])
                            
                            transcript = ' '.join(text_parts)
                            print(f"\n✅ Transcript extracted!")
                            print(f"Length: {len(transcript)} characters")
                            print(f"\nPreview: {transcript[:500]}...")
                            return transcript
            
            # Check for regular subtitles
            if 'subtitles' in info and 'en' in info['subtitles']:
                subtitles = info['subtitles']['en']
                if subtitles:
                    print(f"✅ Found regular subtitles!")
                    caption_url = subtitles[0]['url']
                    
                    import requests
                    response = requests.get(caption_url)
                    
                    if response.status_code == 200:
                        if caption_url.endswith('.json'):
                            data = response.json()
                            if 'events' in data:
                                text_parts = []
                                for event in data['events']:
                                    if 'segs' in event:
                                        for seg in event['segs']:
                                            if 'utf8' in seg:
                                                text_parts.append(seg['utf8'])
                                
                                transcript = ' '.join(text_parts)
                                print(f"\n✅ Transcript extracted!")
                                print(f"Length: {len(transcript)} characters")
                                return transcript
            
            print("❌ No captions found for this video")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    video_id = "jNQXAC9IVRw"
    print(f"Getting transcript for video: {video_id}")
    print("This is the first YouTube video - 'Me at the zoo'")
    print("-" * 50)
    
    transcript = get_youtube_transcript(video_id)
    
    if transcript:
        print("\n" + "="*50)
        print("✅ SUCCESS! Transcript is ready for RAG pipeline")
        print("="*50)
    else:
        print("\n❌ Could not get transcript")
        print("Trying alternative video...")
        
        # Try a different video that definitely has captions
        video_id = "dQw4w9WgXcQ"  # Rick Astley - has captions
        print(f"\nTrying video: {video_id}")
        transcript = get_youtube_transcript(video_id)
        
        if transcript:
            print("\n✅ SUCCESS! Got transcript from Rick Astley video")