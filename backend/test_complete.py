import asyncio
from youtube_transcript_api import YouTubeTranscriptApi

async def get_youtube_transcript(video_id):
    """Get transcript using correct API"""
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list_transcripts(video_id)
        
        # Find English transcript
        transcript = None
        for t in transcript_list:
            if t.language_code == 'en':
                transcript = t
                break
        
        if not transcript:
            transcript = transcript_list.find_transcript(['en'])
        
        data = transcript.fetch()
        full_text = ' '.join([entry['text'] for entry in data])
        return full_text
        
    except Exception as e:
        print(f"Error: {e}")
        return None

async def main():
    video_id = "jNQXAC9IVRw"
    print(f"Getting transcript for {video_id}...")
    
    transcript = await get_youtube_transcript(video_id)
    
    if transcript:
        print(f"\n✅ SUCCESS!")
        print(f"Length: {len(transcript)} characters")
        print(f"\nPreview:\n{transcript[:500]}...")
    else:
        print("\n❌ Failed to get transcript")

if __name__ == "__main__":
    asyncio.run(main())