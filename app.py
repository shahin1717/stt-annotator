"""
STT Annotator — local version
------------------------------
Folder structure expected:
  anywhere/
    audio/        ← dump Verint Zənglər contents here
    transcripts/  ← dump your Shahin E JSON files here
    finished/     ← corrected files go here (auto-created)

Run:
    pip install flask
    python app.py
Then open http://localhost:5000
"""

from flask import Flask, jsonify, request, send_file, render_template
import os, json, shutil, glob

app = Flask(__name__)

BASE     = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR       = os.path.join(BASE, "audio")
TRANSCRIPT_DIR  = os.path.join(BASE, "transcripts")
FINISHED_DIR    = os.path.join(BASE, "finished")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(FINISHED_DIR, exist_ok=True)

# ── Pages ──────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

# ── API ────────────────────────────────────────────────────────────────────
@app.route("/api/samples")
def samples():
    """List all JSON files in transcripts/ that aren't already in finished/."""
    done = {os.path.basename(f) for f in glob.glob(os.path.join(FINISHED_DIR, "*.json*"))}
    files = sorted([
        f for f in os.listdir(TRANSCRIPT_DIR)
        if (f.endswith(".json") or f.endswith(".jsonl")) and f not in done
    ])
    return jsonify(files)

@app.route("/api/transcript/<name>")
def get_transcript(name):
    # try exact name first, then with .jsonl extension
    for fname in [name, name.replace(".json", ".jsonl")]:
        path = os.path.join(TRANSCRIPT_DIR, fname)
        if os.path.exists(path):
            return open(path, encoding="utf-8").read(), 200, {"Content-Type": "application/json"}
    return "Not found", 404

@app.route("/api/audio/<name>")
def get_audio(name):
    """Find audio file matching the base name (any extension)."""
    base = name.replace(".jsonl", "").replace(".json", "")
    for f in os.listdir(AUDIO_DIR):
        if os.path.splitext(f)[0] == base:
            return send_file(os.path.join(AUDIO_DIR, f))
    return "Audio not found", 404

@app.route("/api/save", methods=["POST"])
def save():
    data = request.json
    name    = data["name"]
    content = data["content"]
    out = os.path.join(FINISHED_DIR, name)
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    return jsonify({"ok": True})

if __name__ == "__main__":
    print("\n✓ STT Annotator running → http://localhost:5000\n")
    print(f"  audio/       → {AUDIO_DIR}")
    print(f"  transcripts/ → {TRANSCRIPT_DIR}")
    print(f"  finished/    → {FINISHED_DIR}\n")
    app.run(debug=False, port=5000)