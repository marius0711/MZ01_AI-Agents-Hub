from flask import Flask, request, jsonify
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
import youtube_transcript_api
print(">>> LOADED MODULE:", youtube_transcript_api.__file__)
print(">>> Has get_transcript:", hasattr(YouTubeTranscriptApi, "get_transcript"))
print(">>> Dir:", dir(YouTubeTranscriptApi))

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "youtube-transcript"})

@app.route('/transcript', methods=['GET'])
def get_transcript():
    video_id = request.args.get('video_id')

    if not video_id:
        return jsonify({"error": "Missing video_id parameter"}), 400

    try:
        # API-Instanz (DEINE Version verlangt das)
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)

        # Bestes Transkript auswählen
        chosen_transcript = None

        # 1. Deutsch
        for t in transcript_list:
            if t.language_code == "de":
                chosen_transcript = t
                break

        # 2. Englisch
        if not chosen_transcript:
            for t in transcript_list:
                if t.language_code == "en":
                    chosen_transcript = t
                    break

        # 3. Fallback: erstes
        if not chosen_transcript:
            chosen_transcript = list(transcript_list)[0]

        # Transkript laden
        transcript_data = chosen_transcript.fetch()

        # Text zusammenbauen (DEINE Library nutzt Attribute, nicht Dicts)
        full_text = " ".join(seg.text for seg in transcript_data)

        return jsonify({
            "success": True,
            "video_id": video_id,
            "language": chosen_transcript.language_code,
            "transcript": full_text,
            "word_count": len(full_text.split()),
            "segments_count": len(transcript_data)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "video_id": video_id
        }), 500






@app.route('/transcript/languages', methods=['GET'])
def get_available_languages():
    video_id = request.args.get('video_id')

    if not video_id:
        return jsonify({"error": "Missing video_id parameter"}), 400

    try:
        transcript_list = YouTubeTranscriptApi.list(video_id)

        languages = []
        for transcript in transcript_list.transcripts:
            languages.append({
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated
            })

        return jsonify({
            "video_id": video_id,
            "available_languages": languages
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    print("🚀 YouTube Transcript Service starting...")
    print("📍 Health check: http://localhost:5001/health")
    print("📝 Get transcript: http://localhost:5001/transcript?video_id=VIDEO_ID")
    print("🌍 Available languages: http://localhost:5001/transcript/languages?video_id=VIDEO_ID")
    app.run(host='0.0.0.0', port=5001, debug=True)