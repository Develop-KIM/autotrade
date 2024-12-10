from youtube_transcript_api import YouTubeTranscriptApi

def get_combined_transcript(video_id):
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ko'])
    
    # 모든 텍스트를 하나의 문자열로 결합
    combined_text = ' '.join(entry['text'] for entry in transcript)
    
    return combined_text

print(get_combined_transcript("3XbtEX3jUv4"))