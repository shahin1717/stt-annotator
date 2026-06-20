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
WORKING_DIR     = os.path.join(BASE, "working")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
os.makedirs(FINISHED_DIR, exist_ok=True)
os.makedirs(WORKING_DIR, exist_ok=True)

# ── Pages ──────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

def load_jsonl_segments(file_path):
    try:
        segments = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    segments.append(json.loads(line))
        return segments
    except Exception:
        return None

def is_different(f1_path, f2_path):
    s1 = load_jsonl_segments(f1_path)
    s2 = load_jsonl_segments(f2_path)
    if s1 is None or s2 is None:
        return True
    if len(s1) != len(s2):
        return True
    for seg1, seg2 in zip(s1, s2):
        for key in ["start_time", "end_time", "speaker", "text"]:
            if seg1.get(key) != seg2.get(key):
                return True
    return False

@app.route("/api/samples")
def samples():
    """List all JSON files in transcripts/ that aren't already in finished/ with draft status."""
    done = {os.path.basename(f) for f in glob.glob(os.path.join(FINISHED_DIR, "*.json*"))}
    working = {os.path.basename(f) for f in glob.glob(os.path.join(WORKING_DIR, "*.json*"))}
    
    files = []
    for f in sorted(os.listdir(TRANSCRIPT_DIR)):
        if (f.endswith(".json") or f.endswith(".jsonl")) and f not in done:
            is_working = False
            if f in working:
                w_path = os.path.join(WORKING_DIR, f)
                t_path = os.path.join(TRANSCRIPT_DIR, f)
                if os.path.exists(w_path) and os.path.exists(t_path):
                    if is_different(w_path, t_path):
                        is_working = True
                    else:
                        try:
                            os.remove(w_path)
                        except Exception:
                            pass
            
            files.append({
                "name": f,
                "status": "working" if is_working else "raw"
            })
    return jsonify(files)

@app.route("/api/transcript/<name>")
def get_transcript(name):
    # try exact name first, then with .jsonl extension
    for fname in [name, name.replace(".json", ".jsonl")]:
        f_path = os.path.join(FINISHED_DIR, fname)
        if os.path.exists(f_path):
            return open(f_path, encoding="utf-8").read(), 200, {"Content-Type": "application/json"}
        w_path = os.path.join(WORKING_DIR, fname)
        if os.path.exists(w_path):
            return open(w_path, encoding="utf-8").read(), 200, {"Content-Type": "application/json"}
        path = os.path.join(TRANSCRIPT_DIR, fname)
        if os.path.exists(path):
            return open(path, encoding="utf-8").read(), 200, {"Content-Type": "application/json"}
    return "Not found", 404

@app.route("/api/finished")
def get_finished():
    """List all JSON/JSONL files in finished/."""
    files = sorted([
        f for f in os.listdir(FINISHED_DIR)
        if (f.endswith(".json") or f.endswith(".jsonl"))
    ])
    return jsonify(files)

@app.route("/api/requeue", methods=["POST"])
def requeue():
    data = request.json
    name = data.get("name")
    if not name:
        return jsonify({"ok": False, "error": "Missing name parameter"}), 400
    path = os.path.join(FINISHED_DIR, name)
    if os.path.exists(path):
        os.remove(path)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "File not found in finished"}), 404

@app.route("/api/audio/<name>")
def get_audio(name):
    """Find audio file matching the base name (any extension)."""
    base = name.replace(".jsonl", "").replace(".json", "")
    for f in os.listdir(AUDIO_DIR):
        if os.path.splitext(f)[0] == base:
            return send_file(os.path.join(AUDIO_DIR, f))
    return "Audio not found", 404

@app.route("/api/rules")
def get_rules():
    rules_path = os.path.join(BASE, "ai", "rules.md")
    if os.path.exists(rules_path):
        with open(rules_path, encoding="utf-8") as f:
            return jsonify({"ok": True, "rules": f.read()})
    return jsonify({"ok": False, "error": "Rules file not found"}), 404

@app.route("/api/save", methods=["POST"])
def save():
    data = request.json
    name    = data["name"]
    content = data["content"]
    out = os.path.join(FINISHED_DIR, name)
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Delete from working folder if it exists since it's now finalized
    w_path = os.path.join(WORKING_DIR, name)
    if os.path.exists(w_path):
        os.remove(w_path)
        
    return jsonify({"ok": True})

@app.route("/api/save_draft", methods=["POST"])
def save_draft():
    data = request.json
    name    = data["name"]
    content = data["content"]
    out = os.path.join(WORKING_DIR, name)
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    return jsonify({"ok": True})

@app.route("/api/ai/correct", methods=["POST"])
def ai_correct():
    data = request.json
    segments = data.get("segments", [])
    model = data.get("model", "gemini-3.5-flash")
    
    from ai.correct import run_ai_correction
    ok, result = run_ai_correction(segments, model)
    
    if not ok:
        return jsonify({"ok": False, "error": result})
        
    return jsonify({"ok": True, "segments": result})

if __name__ == "__main__":
    print("\n✓ STT Annotator running → http://localhost:5000\n")
    print(f"  audio/       → {AUDIO_DIR}")
    print(f"  transcripts/ → {TRANSCRIPT_DIR}")
    print(f"  finished/    → {FINISHED_DIR}\n")
    app.run(debug=False, port=5000)