import os
import json
import urllib.request
import urllib.error

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_env():
    env_path = os.path.join(BASE, ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

def call_gemini(system_instruction, user_content, model="gemini-3.5-flash"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY not found in environment or .env file"}
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {"parts": [{"text": user_content}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
            try:
                text_out = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except KeyError:
                return {"error": f"Invalid response structure from Gemini: {json.dumps(res_data)}"}
            
            # Strip markdown code blocks if present
            if text_out.startswith("```"):
                lines = text_out.splitlines()
                if len(lines) > 2:
                    if lines[-1].strip() == "```":
                        text_out = "\n".join(lines[1:-1])
                    else:
                        text_out = "\n".join(lines[1:])
                text_out = text_out.strip()
                
            return {"success": True, "data": json.loads(text_out)}
    except urllib.error.HTTPError as e:
        try:
            err_msg = e.read().decode("utf-8")
        except Exception:
            err_msg = str(e)
        return {"error": f"API error: {e.code} - {err_msg}"}
    except Exception as e:
        return {"error": f"Connection error: {str(e)}"}

def run_ai_correction(segments, model="gemini-3.5-flash"):
    load_env()
    
    rules_path = os.path.join(BASE, "ai", "rules.md")
    rules_content = ""
    if os.path.exists(rules_path):
        with open(rules_path, encoding="utf-8") as f:
            rules_content = f.read()
            
    system_instruction = f"""
You are an expert Azerbaijani speech-to-text transcript corrector.
Your task is to apply the transcription rules below to a JSON array of transcript segments.

Rules:
{rules_content}

CRITICAL INSTRUCTIONS (Strictness & Minimal Changes):
1. It is NOT mandatory to find and correct errors in every segment. Only make a correction if a segment explicitly violates one of the rules.
2. Do NOT perform stylistic editing, paraphrase, or make unnecessary corrections to grammatically correct or standard Azerbaijani speech.
3. If a segment's text and speaker conform to the rules, keep them EXACTLY as they are. Preserve original wording, word order, and phrasing unless it violates a specific rule (e.g., dialect normalization, number formatting, punctuation cleanup).
4. Be extremely careful and conservative. Minimize changes.

SEGMENT STRUCTURE — DEFAULT vs EXCEPTIONS:
By default, do NOT change start_time or end_time, and do NOT add, merge, or omit segments — preserve the original segment structure and chronological ordering.

The ONLY exceptions, where changing the segment structure is required:
- Unclear/unintelligible audio: replace that segment's text with "[unclear]" (do not guess the words). If you judge the unclear portion needs separating from surrounding clear speech within the same original segment, you may split it into multiple segments with sub-divided timestamps, keeping the total span identical to the original segment's start_time/end_time.
- Foreign-language phrases: same handling as unclear — split out a sub-segment with text "[another_language]" only if the foreign phrase is part of a larger mixed-language original segment.
- Segments exceeding 30 seconds (end_time - start_time > 30s): split into multiple consecutive segments, each ≤ 30 seconds, with new internally-consistent timestamps that together span the exact original start_time to end_time. Do not invent gaps or overlaps.
- Entirely unintelligible segments: if a segment is unclear in its entirety with no usable content, you may omit it from the output rather than including "[unclear]" as its only content — but do this rarely and only when justified by the rules.

Outside of these four cases, segment count, order, and timestamps must remain identical to the input.

OUTPUT FORMAT:
Return ONLY a clean, valid JSON array containing the corrected segments. No explanations, no markdown, no extra text.
"""
    
    user_content = json.dumps(segments)
    res = call_gemini(system_instruction, user_content, model)
    
    if "error" in res:
        return False, res["error"]
        
    return True, res["data"]
