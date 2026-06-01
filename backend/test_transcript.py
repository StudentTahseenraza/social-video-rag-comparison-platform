import asyncio
import sys

print("Python path:", sys.executable)

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    print("✅ Module imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

async def test_transcript():
    video_id = "jNQXAC9IVRw"  # Me at the zoo
    
    print(f"\nTesting YouTube Transcript API...")
    print(f"Video ID: {video_id}")
    
    try:
        # Get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        
        if transcript_list:
            print(f"\n✅ SUCCESS! Got {len(transcript_list)} transcript segments")
            print(f"First segment: {transcript_list[0]['text'][:100]}...")
            
            full_text = ' '.join([entry['text'] for entry in transcript_list])
            print(f"\nTotal transcript length: {len(full_text)} characters")
            print(f"\nTranscript preview: {full_text[:300]}...")
        else:
            print("❌ No transcript found")
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_transcript())