from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import unicodedata
import re
import os

app = Flask(__name__)
CORS(app)  # Allow cross-origin access for browser extensions

HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

# Normalize text (e.g. GIVĒON → Giveon, remove quotes/punctuation)
def normalize(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r"[‘’'\"“”]", "", text)            # remove quotes
    text = re.sub(r"[^\w\s]", "", text)              # remove other punctuations
    return text.strip()

# Extract song metadata from song detail page
def extract_metadata(info_url):
    try:
        res = requests.get(info_url, headers=HEADERS)
        soup = BeautifulSoup(res.text, 'html.parser')

        def get_value(label):
            try:
                label_el = soup.find('p', string=label)
                value_el = label_el.find_next_sibling('p')
                return value_el.text.strip()
            except:
                return None

        return {
            "bpm": get_value("BPM"),
            "key": get_value("Key"),
            "camelot": get_value("Camelot"),
            "energy": get_value("Energy"),
            "danceability": get_value("Danceability"),
            "valence": get_value("Happiness"),
        }

    except Exception as e:
        print(f"❌ Error extracting metadata: {e}")
        return None

# Try fetching first valid /Info/ link from Tunebat search page
def fetch_info_url(query_string):
    norm_query = normalize(query_string)
    search_url = f"https://tunebat.com/search?q={requests.utils.quote(norm_query)}"
    print(f"🔍 Searching for: {query_string}")
    print(f"🔗 Tunebat URL: {search_url}")

    res = requests.get(search_url, headers=HEADERS)

    with open("tunebat_debug.html", "w", encoding="utf-8") as f:
        f.write(res.text)

    soup = BeautifulSoup(res.text, 'html.parser')
    result_links = soup.select("a[href^='/Info/']")

    for link in result_links:
        href = link.get("href", "")
        if href.startswith("/Info/"):
            return "https://tunebat.com" + href

    return None

@app.route("/metadata", methods=["GET"])
def get_metadata():
    title = request.args.get("title", "").strip()
    artist = request.args.get("artist", "").strip()

    if not title:
        return jsonify({"error": "Missing title"}), 400

    raw_full_query = f"{title} {artist}".strip()
    raw_title_only_query = title.strip()

    # Try full query first
    info_url = fetch_info_url(raw_full_query)

    # If not found, try title only
    if not info_url:
        print("⚠️ No valid result with full query, trying title only...")
        info_url = fetch_info_url(raw_title_only_query)

    if not info_url:
        print("❌ No valid song link found after fallback.")
        return jsonify({"error": "Track not found"}), 404

    print(f"✅ Track page: {info_url}")
    metadata = extract_metadata(info_url)

    if not metadata:
        return jsonify({"error": "Failed to extract metadata"}), 500

    metadata.update({
        "info_url": info_url,
        "title": title,
        "artist": artist
    })

    return jsonify(metadata)

@app.route("/ping")
def ping():
    return jsonify({"status": "online"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)