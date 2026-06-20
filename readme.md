# 🎧 STT Annotator

A high-performance, lightweight, local web-based Speech-to-Text (STT) transcription annotation and correction tool. Designed specifically for reviewing and refining conversational Azerbaijani audio-to-text transcripts with manual editing controls and rule-based AI assistance.

---

## ✨ Features

- **Manual Annotation & Correction**:
  - Edit speaker segment text inline with real-time change tracking.
  - Interactive speaker toggle: click speaker labels to switch between `Operator` and `Müştəri`.
  - Editable timestamps (`MM:SS → MM:SS`) with format validation.
  - Add and delete segments on the fly.
- **AI-Powered Corrections (Gemini)**:
  - Supports the latest Gemini models: **Gemini 3.5 Flash**, **Gemini 3.1 Pro Preview**, **Gemini 2.5 Pro**, and **Gemini 2.5 Flash**.
  - Dynamic rules ingestion: reads transcription guidelines directly from `ai/rules.md` (e.g., standardizing spelling, filtering filler words, background noise tags like `[fon_küyü]`).
  - High-precision minimal edit constraints: only updates rule violations without changing core dialect/phrasing.
  - Visual change comparison: displays the original text alongside corrected segments.
- **Custom Audio Player**:
  - Auto-mapped audio streams synced with segment clicks.
  - Keyboard shortcuts for hands-free playback controls.
  - Playback speed controls (`0.5x` to `2x`) and volume sliders.
- **Workflow & Queue Management**:
  - Real-time batch progress bar tracks completion.
  - Separate, collapsible **Finished** panel containing reviewed files.
  - Quick **Re-queue (↩)** action to move files back into the active queue.

---

## 📁 Directory Structure

Organize your workspace as follows:

```text
stt-local/
├── audio/          ← Put .wav / .mp3 files here
├── transcripts/    ← Put .jsonl transcript files here
├── working/        ← Partial draft edits are saved here (auto-created)
├── finished/       ← Completed files are saved here (auto-created)
├── ai/
│   ├── rules.md    ← Markdown file containing spelling & formatting rules
│   └── correct.py  ← Gemini API integration wrapper
├── templates/
│   └── index.html  ← Frontend UI (Vanilla CSS/JS)
├── app.py          ← Flask Backend
├── .env            ← Environment file for your API keys (ignored by git)
└── readme.md       ← This instruction file
```

### Transcript File Format (`.jsonl`)
Transcripts must be in Newline-Delimited JSON (JSONL) format:
```json
{"start_time": "00:02", "end_time": "00:05", "speaker": "Operator", "text": "Alo, hər vaxtınız xeyir."}
{"start_time": "00:05", "end_time": "00:08", "speaker": "Müştəri", "text": "Salam, hər vaxtınız xeyir."}
```
*Note: Audio and transcript files are automatically matched by their base filename (e.g., `202501091637.jsonl` matches `202501091637.wav`).*

---

## 🚀 Setup & Installation

### 1. Clone the repository
```bash
git clone git@github.com:shahin1717/stt-annotator.git
cd stt-annotator
```

### 2. Install dependencies
Only Flask is required. All AI requests use native Python standard libraries (zero third-party SDK dependencies).
```bash
pip install flask
```

### 3. Add API Keys
Create a `.env` file in the root directory and add your Google Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 💻 Running the App

1. Place your raw audio files into the `audio/` directory.
2. Place your corresponding transcript `.jsonl` files into the `transcripts/` directory.
3. Run the Flask application:
   ```bash
   python app.py
   ```
4. Open your browser and navigate to:
   ```text
   http://localhost:5000
   ```

---

## ⌨️ Keyboard Shortcuts

These shortcuts are active only when you are **not** typing inside input fields or textareas:

| Key | Action |
| :--- | :--- |
| `Space` | Play / Pause audio |
| `Left Arrow (←)` | Seek back 5 seconds |
| `Right Arrow (→)` | Seek forward 5 seconds |

---

## 🔄 Recommended Workflow

1. **Upload Batch**: Drop raw `.jsonl` transcripts into `transcripts/` and `.wav` audios into `audio/`.
2. **Launch & Correct**: Open the web application. You can review segments manually or press **✨ AI Correct** to run the selected Gemini model over the rules.
3. **Verify & Save**: Listen to the audio to verify corrections. Click **✓ Save to Finished** to move the file into `finished/`.
4. **Final Export**: Once the queue is empty, grab your finalized transcript files from the `finished/` folder and upload them back to your storage system.