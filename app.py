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

def to_seconds(t_str):
    if not t_str:
        return 0
    parts = t_str.split(":")
    m = int(parts[0]) if len(parts) > 0 else 0
    s = int(parts[1]) if len(parts) > 1 else 0
    return m * 60 + s

def to_time_str(secs):
    if secs < 0:
        secs = 0
    m = int(secs) // 60
    s = int(secs) % 60
    return f"{m:02d}:{s:02d}"

def get_original_segments(name):
    path = os.path.join(TRANSCRIPT_DIR, name)
    if not os.path.exists(path):
        if name.endswith(".json"):
            path = os.path.join(TRANSCRIPT_DIR, name.replace(".json", ".jsonl"))
        elif name.endswith(".jsonl"):
            path = os.path.join(TRANSCRIPT_DIR, name.replace(".jsonl", ".json"))
    if os.path.exists(path):
        return load_jsonl_segments(path)
    return None

def check_and_propagate_shifts(draft_segments, original_segments):
    if not original_segments:
        return draft_segments

    n_d = len(draft_segments)
    n_o = len(original_segments)
    
    dp = [[0.0] * (n_o + 1) for _ in range(n_d + 1)]
    parent = [[(0, 0)] * (n_o + 1) for _ in range(n_d + 1)]
    
    def get_match_score(d_idx, o_idx):
        d_seg = draft_segments[d_idx]
        o_seg = original_segments[o_idx]
        score = 0.0
        if d_seg.get("text") == o_seg.get("text") and d_seg.get("speaker") == o_seg.get("speaker") and d_seg.get("start_time") == o_seg.get("start_time") and d_seg.get("end_time") == o_seg.get("end_time"):
            score += 100.0
        elif d_seg.get("text") == o_seg.get("text"):
            score += 80.0
            
        if d_seg.get("start_time") == o_seg.get("start_time") and d_seg.get("end_time") == o_seg.get("end_time"):
            score += 40.0
            
        if d_seg.get("speaker") == o_seg.get("speaker"):
            score += 10.0
            
        w1 = set(d_seg.get("text", "").lower().split())
        w2 = set(o_seg.get("text", "").lower().split())
        if w1 and w2:
            intersection = w1.intersection(w2)
            score += (len(intersection) / max(len(w1), len(w2))) * 20.0
            
        score += 5.0 / (1.0 + abs(d_idx - o_idx))
        return score

    for i in range(1, n_d + 1):
        for j in range(1, n_o + 1):
            score = get_match_score(i-1, j-1)
            op1 = dp[i-1][j-1] + score
            op2 = dp[i-1][j]
            op3 = dp[i][j-1]
            
            best = max(op1, op2, op3)
            dp[i][j] = best
            
            if best == op1:
                parent[i][j] = (i-1, j-1)
            elif best == op2:
                parent[i][j] = (i-1, j)
            else:
                parent[i][j] = (i, j-1)
                
    mapping = {}
    i, j = n_d, n_o
    while i > 0 and j > 0:
        pi, pj = parent[i][j]
        if pi == i-1 and pj == j-1:
            if get_match_score(i-1, j-1) > 2.0:
                mapping[i-1] = j-1
            i, j = pi, pj
        elif pi == i-1:
            i = pi
        else:
            j = pj

    changed_or_propagated = [False] * n_d
    for d_idx in range(n_d):
        o_idx = mapping.get(d_idx)
        if o_idx is None:
            changed_or_propagated[d_idx] = True
        else:
            d_seg = draft_segments[d_idx]
            o_seg = original_segments[o_idx]
            if d_seg.get("start_time") != o_seg.get("start_time") or d_seg.get("end_time") != o_seg.get("end_time"):
                changed_or_propagated[d_idx] = True

    for idx in range(n_d - 1):
        if changed_or_propagated[idx]:
            prev_seg = draft_segments[idx]
            next_seg = draft_segments[idx + 1]
            
            prev_end = to_seconds(prev_seg.get("end_time", "00:00"))
            next_start = to_seconds(next_seg.get("start_time", "00:00"))
            
            if next_start < prev_end:
                next_end = to_seconds(next_seg.get("end_time", "00:00"))
                duration = max(0, next_end - next_start)
                
                new_start_str = to_time_str(prev_end)
                new_end_str = to_time_str(prev_end + duration)
                
                next_seg["start_time"] = new_start_str
                next_seg["end_time"] = new_end_str
                
                changed_or_propagated[idx + 1] = True

    return draft_segments


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
    
    try:
        segments = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line:
                segments.append(json.loads(line))
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to parse content: {str(e)}"}), 400

    original_segments = get_original_segments(name)
    adjusted_segments = check_and_propagate_shifts(segments, original_segments)
    
    content = "\n".join(json.dumps(s, ensure_ascii=False) for s in adjusted_segments)
    
    out = os.path.join(FINISHED_DIR, name)
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
        
    # Delete from working folder if it exists since it's now finalized
    w_path = os.path.join(WORKING_DIR, name)
    if os.path.exists(w_path):
        os.remove(w_path)
        
    return jsonify({"ok": True, "segments": adjusted_segments})

@app.route("/api/save_draft", methods=["POST"])
def save_draft():
    data = request.json
    name    = data["name"]
    content = data["content"]
    
    try:
        segments = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line:
                segments.append(json.loads(line))
    except Exception as e:
        return jsonify({"ok": False, "error": f"Failed to parse content: {str(e)}"}), 400

    original_segments = get_original_segments(name)
    adjusted_segments = check_and_propagate_shifts(segments, original_segments)
    
    content = "\n".join(json.dumps(s, ensure_ascii=False) for s in adjusted_segments)
    
    out = os.path.join(WORKING_DIR, name)
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    return jsonify({"ok": True, "segments": adjusted_segments})

@app.route("/api/ai/correct", methods=["POST"])
def ai_correct():
    data = request.json
    segments = data.get("segments", [])
    model = data.get("model", "gemini-3.5-flash")
    name = data.get("name")
    use_audio = data.get("use_audio", False)
    
    if name:
        original_segments = get_original_segments(name)
        segments = check_and_propagate_shifts(segments, original_segments)
        
    audio_path = None
    if use_audio and name:
        base = name.replace(".jsonl", "").replace(".json", "")
        for f in os.listdir(AUDIO_DIR):
            if os.path.splitext(f)[0] == base:
                audio_path = os.path.join(AUDIO_DIR, f)
                break
    
    from ai.correct import run_ai_correction
    ok, result = run_ai_correction(segments, model, audio_path=audio_path)
    
    if not ok:
        print(f"\n❌ [AI Error] correction failed for file '{name or 'unknown'}': {result}\n")
        return jsonify({"ok": False, "error": result})
        
    return jsonify({"ok": True, "segments": result})

@app.route("/api/ai/adjust_timestamps", methods=["POST"])
def adjust_timestamps():
    data = request.json
    segments = data.get("segments", [])
    name = data.get("name")
    
    if not name:
        return jsonify({"ok": False, "error": "Missing name"}), 400
        
    original_segments = get_original_segments(name)
    adjusted_segments = check_and_propagate_shifts(segments, original_segments)
    
    return jsonify({"ok": True, "segments": adjusted_segments})



if __name__ == "__main__":
    print("\n✓ STT Annotator running → http://localhost:5000\n")
    print(f"  audio/       → {AUDIO_DIR}")
    print(f"  transcripts/ → {TRANSCRIPT_DIR}")
    print(f"  finished/    → {FINISHED_DIR}\n")
    app.run(debug=False, port=5000)