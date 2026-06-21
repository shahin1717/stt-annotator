import os
import json
import urllib.request
import urllib.error
import re
import time

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

def get_audio_mime_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".wav":
        return "audio/wav"
    elif ext == ".mp3":
        return "audio/mp3"
    elif ext in [".ogg", ".oga"]:
        return "audio/ogg"
    elif ext == ".aac":
        return "audio/aac"
    elif ext == ".flac":
        return "audio/flac"
    elif ext == ".webm":
        return "audio/webm"
    return "audio/wav"

def call_gemini(system_instruction, user_content, audio_path=None, model="gemini-3.5-flash"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY not found in environment or .env file"}
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    parts = []
    if audio_path and os.path.exists(audio_path):
        try:
            import base64
            with open(audio_path, "rb") as f:
                audio_data = base64.b64encode(f.read()).decode("utf-8")
            mime = get_audio_mime_type(audio_path)
            parts.append({
                "inlineData": {
                    "mimeType": mime,
                    "data": audio_data
                }
            })
            print(f"[AI Info] Multimodal mode enabled. Sending audio file: {audio_path}")
        except Exception as e:
            print(f"[AI Warning] Failed to load audio file for Gemini: {str(e)}")
            
    parts.append({"text": user_content})
    
    payload = {
        "systemInstruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [
            {"parts": parts}
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
    
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                
                if not res_data.get("candidates"):
                    return {"error": f"No candidates returned by Gemini: {json.dumps(res_data)}"}
                
                candidate = res_data["candidates"][0]
                if "content" not in candidate:
                    finish_reason = candidate.get("finishReason", "UNKNOWN")
                    return {"error": f"Gemini generation blocked. Reason/Status: {finish_reason}. Response: {json.dumps(res_data)}"}
                
                try:
                    text_out = candidate["content"]["parts"][0]["text"].strip()
                except (KeyError, IndexError):
                    return {"error": f"Invalid content structure in candidate response: {json.dumps(res_data)}"}
                
                # Semantic JSON parsing
                try:
                    parsed_data = json.loads(text_out)
                    return {"success": True, "data": parsed_data}
                except json.JSONDecodeError:
                    cleaned_text = text_out
                    if cleaned_text.startswith("```"):
                        lines = cleaned_text.splitlines()
                        if len(lines) > 2:
                            if lines[-1].strip() == "```":
                                cleaned_text = "\n".join(lines[1:-1])
                            else:
                                cleaned_text = "\n".join(lines[1:])
                        cleaned_text = cleaned_text.strip()
                    
                    try:
                        parsed_data = json.loads(cleaned_text)
                        return {"success": True, "data": parsed_data}
                    except json.JSONDecodeError:
                        # Fallback: extract JSON array or object using regex
                        match = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', text_out)
                        if match:
                            try:
                                parsed_data = json.loads(match.group(1))
                                return {"success": True, "data": parsed_data}
                            except json.JSONDecodeError:
                                pass
                        return {"error": f"Failed to parse Gemini response as JSON. Raw response content: {text_out}"}
        except urllib.error.HTTPError as e:
            # Retry transient rate limits (429) or server errors (503/504)
            if e.code in [429, 503, 504] and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            
            try:
                err_msg = e.read().decode("utf-8")
                # Parse error response to check for resource exhaustion
                try:
                    err_json = json.loads(err_msg)
                    msg_detail = err_json.get("error", {}).get("message", "")
                    status_str = err_json.get("error", {}).get("status", "")
                    if status_str == "RESOURCE_EXHAUSTED" or "Quota exceeded" in msg_detail:
                        return {
                            "error": f"Quota Exceeded / Model Restricted (429). If using a Free Tier API Key, please switch the model dropdown to a Flash model (like 'Gemini 3.5 Flash' or 'Gemini 2.5 Flash') instead of 'Pro'.\n\nDetails: {msg_detail}"
                        }
                except Exception:
                    pass
            except Exception:
                err_msg = str(e)
            return {"error": f"API error: {e.code} - {err_msg}"}
        except Exception as e:
            if attempt < 2:
                time.sleep(1)
                continue
            return {"error": f"Connection error: {str(e)}"}

def run_ai_correction(segments, model="gemini-3.5-flash", audio_path=None):
    load_env()
    
    rules_path = os.path.join(BASE, "ai", "rules.md")
    rules_content = ""
    if os.path.exists(rules_path):
        with open(rules_path, encoding="utf-8") as f:
            rules_content = f.read()
            
    if audio_path:
        structure_instruction = """
SEGMENT STRUCTURE — TIMESTAMPS & ALIGNMENT (Multimodal Audio Mode):
Since you are provided with BOTH the raw audio file and the draft transcript, you MUST align and correct the segment timestamps to match the audio:
1. Listen to the audio and verify that the segment timestamps (start_time and end_time) match the timing of the actual spoken words.
2. If a segment's start_time or end_time is incorrect, offset, or covers long silent pauses (e.g., if a speaker finishes talking and there is 10 seconds of silence, do NOT let the segment drag into the silence—end it immediately when the speaker stops talking), adjust the timestamps to wrap tightly around the actual spoken speech.
3. Ensure all segment timestamps remain chronologically sequential and do not overlap (except for speaker overlaps where both speak at once).
"""
    else:
        structure_instruction = """
SEGMENT STRUCTURE — DEFAULT vs EXCEPTIONS (Text-Only Mode):
By default, do NOT change start_time or end_time, and do NOT add, merge, or omit segments — preserve the original segment structure and chronological ordering.

The ONLY exceptions, where changing the segment structure is allowed:
- A segment's (end_time - start_time) is STRICTLY GREATER than 30 seconds: split into multiple consecutive segments, each ≤ 30 seconds, spanning the exact original range. This does NOT apply to segments under 30 seconds — never split, merge, or restructure a segment that is already within the 30-second limit, regardless of its content.
- Unclear/unintelligible audio mixed with clear speech in one segment: you may split out the unclear portion as its own segment with text "[unclear]".
- Foreign-language phrase mixed with native speech in one segment: you may split out that portion as its own segment with text "[another_language]".
- Entirely unintelligible segment: may be omitted from output if it has no usable content.

Outside of these four cases, segment count, order, and timestamps must remain identical to the input.
"""
            
    system_instruction = f"""
You are an expert Azerbaijani speech-to-text transcript corrector.
Your task is to apply the transcription rules below to a JSON array of transcript segments.

Rules:
{rules_content}

CRITICAL INSTRUCTIONS (Strictness & Minimal Changes):
1. Do NOT edit a segment unless it CLEARLY and UNAMBIGUOUSLY violates one of the numbered rules above. When in doubt, leave it unchanged.
2. Do NOT perform stylistic editing, paraphrasing, rewording, or "improving" grammatically correct or standard Azerbaijani speech — even if an alternative phrasing sounds more natural to you.
3. Do NOT add, remove, or change punctuation/capitalization/words unless a specific rule explicitly requires it for that exact case. Casual spoken word order and repetition (e.g. "günləri" vs "gün") are NOT errors unless they match a documented dialect-normalization pattern in the rules.
4. If you are not 100% certain a change is required by a specific rule, do not make it. Silence (no edit) is always the safe default — over-editing is a worse outcome than under-editing.
5. The vast majority of segments in a real transcript should come back byte-for-byte identical to the input. If you find yourself editing most or all segments, you are being too aggressive — stop and reconsider.

{structure_instruction}

OUTPUT FORMAT:
Return ONLY a clean, valid JSON array containing the corrected segments. No explanations, no markdown, no extra text.
"""
    
    user_content = json.dumps(segments)
    res = call_gemini(system_instruction, user_content, audio_path, model)
    
    if "error" in res:
        print(f"\n[AI Error] Gemini call failed for model '{model}':")
        print(f"Details: {res['error']}\n")
        return False, res["error"]
        
    return True, res["data"]
