from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route("/ping")
def ping():
    return jsonify({"status": "online"})

@app.route("/metadata")
def get_metadata():
    title = request.args.get("title", "").strip()
    artist = request.args.get("artist", "").strip()

    if not title:
        return jsonify({"error": "Missing title"}), 400

    query = f"{title} {artist}".strip().replace(" ", "%20")
    url = f"https://api.tunebat.com/api/tracks/search?term={query}"
    print(f"🎧 Fetching metadata for: {query}")

    try:
        res = requests.get(url)
        if res.status_code != 200:
            return jsonify({"error": "Failed to fetch"}), 502

        data = res.json().get("data", {}).get("items", [])
        if not data:
            return jsonify({"error": "Track not found"}), 404

        track = data[0]
        return jsonify({
            "title": track.get("n"),
            "artist": ", ".join(track.get("as", [])),
            "bpm": track.get("b"),
            "key": track.get("k"),
            "camelot": track.get("c"),
            "energy": round(float(track.get("e", 0)) * 100),
            "danceability": round(float(track.get("da", 0)) * 100),
            "valence": round(float(track.get("h", 0)) * 100),
            "artwork": track.get("ci", [{}])[0].get("iu", "")
        })

    except Exception as e:
        print(f"❌ Error fetching metadata: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
