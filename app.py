from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import unicodedata
import re
import os

app = Flask(__name__)
CORS(app)

def normalize(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r"[‘’'\"“”]", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip()

def fetch_tunebat_info(query):
    url = f"https://tunebat.com/search?q={query.replace(' ', '%20')}"
    print(f"🔍 Searching: {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=15000)

            # 🔁 Increase wait timeout to 10s (from 5s)
            page.wait_for_selector("a[href^='/Info/']", timeout=10000)
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            browser.close()

            for link in soup.select("a[href^='/Info/']"):
                href = link.get("href")
                if href:
                    return "https://tunebat.com" + href
    except Exception as e:
        print(f"❌ fetch_tunebat_info() error: {e}")
        return None

def extract_metadata(info_url):
    print(f"🎯 Loading: {info_url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(info_url, timeout=15000)
        page.wait_for_selector("p", timeout=5000)
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        browser.close()

        def get_value(label):
            try:
                el = soup.find("p", string=label)
                val = el.find_next_sibling("p")
                return val.text.strip() if val else None
            except:
                return None

        return {
            "bpm": get_value("BPM"),
            "key": get_value("Key"),
            "camelot": get_value("Camelot"),
            "energy": get_value("Energy"),
            "danceability": get_value("Danceability"),
            "valence": get_value("Happiness")
        }

@app.route("/metadata")
def metadata():
    title = request.args.get("title", "")
    artist = request.args.get("artist", "")
    if not title:
        return jsonify({"error": "Missing title"}), 400

    full_query = normalize(f"{title} {artist}".strip())
    fallback_query = normalize(title)

    info_url = fetch_tunebat_info(full_query) or fetch_tunebat_info(fallback_query)
    if not info_url:
        print("❌ No song URL found after both queries.")
        return jsonify({"error": "Track not found"}), 404


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
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
