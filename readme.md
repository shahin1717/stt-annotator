# STT Annotator — Recreation Prompt (Local Version)

> Paste this into any AI to recreate the project from scratch.

---

## What to Build

A local web app for correcting AI-generated speech transcripts. Two files only: `app.py` (Flask) and `templates/index.html`. No frontend frameworks, no database, no auth.

---

## Folder Structure

```
stt/
  audio/           ← .wav audio files
  transcripts/     ← .jsonl transcript files
  finished/        ← corrected files saved here (auto-created)
  app.py
  templates/
    index.html
```

---

## Transcript File Format

Newline-delimited JSON — one object per line (`.jsonl`):

```json
{"start_time": "00:02", "end_time": "00:03", "speaker": "Operator", "text": "Alo, hər vaxtınız xeyir."}
{"start_time": "00:03", "end_time": "00:04", "speaker": "Müştəri", "text": "Salam."}
{"start_time": "00:05", "end_time": "00:06", "speaker": "Operator", "text": "Hər vaxtınız xeyir, buyurun."}
```

Each segment has: `start_time`, `end_time`, `speaker`, `text`.

---

## File Matching Logic

Transcript `2025010916370848785.jsonl` matches audio `2025010916370848785.wav` by **base filename** — strip extension from both and compare.

---

## Flask Backend — `app.py`

### Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | Serve `index.html` |
| `GET` | `/api/samples` | List `.jsonl` files in `transcripts/` excluding files already in `finished/` |
| `GET` | `/api/transcript/<name>` | Return raw file content as text |
| `GET` | `/api/audio/<name>` | Find matching audio by base name, stream it |
| `POST` | `/api/save` | Body: `{name, content}` — write corrected content to `finished/<name>` |

### Notes
- `finished/` directory must be auto-created on startup if it doesn't exist
- Audio route strips `.jsonl` and `.json` from name before matching
- Samples route excludes filenames already present in `finished/`
- Run on port 5000

---

## Frontend — `templates/index.html`

Single file, **vanilla JS only**. No React, no Vue, no jQuery.

### Layout

Two-column CSS grid:
- **Left column** (300px): audio player card + file queue card
- **Right column** (flex): transcript editor card
- Collapse to single column on mobile (< 760px)

---

### Audio Player

- Play / Pause button
- Seek −5s and +5s buttons
- Clickable fake waveform progress bar (36 vertical bars, filled left to right as audio plays)
- Current time / total duration display (`M:SS / M:SS`)
- Playback speed toggle cycling: `0.5×` → `0.75×` → `1×` → `1.25×` → `1.5×` → `2×`
- Volume slider
- Progress bar showing overall batch progress (X done / Y total)
- Currently playing filename shown above waveform

### File Queue

- List all pending `.jsonl` files
- Active file highlighted in amber
- Click any file to load it
- Refresh button to reload list from server
- File count badge in top bar

### Transcript Editor

Each `.jsonl` line rendered as a conversation row containing:
- **Speaker label** (colored by role)
- **Timestamp** (`start_time → end_time`)
- **Editable textarea** for the transcript text

Speaker colors:
- `Operator` → blue (`#6B9FE4`)
- `Müştəri` → green (`#5DBF85`)

Behavior:
- Clicking a segment row seeks audio to that segment's `start_time` and starts playing
- The segment currently being played gets an amber border highlight
- Edited segments turn amber to indicate changes from original
- Counter shows "N segments edited" when changes exist

### Action Bar (bottom of transcript)

- **Save to Finished** button — POST to `/api/save` with corrected content, then auto-load next file
- **Skip** button — load next file without saving
- Edit count hint shown inline

### Keyboard Shortcuts

Disabled when focus is inside a `textarea` or `input`:

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `←` | Seek −5 seconds |
| `→` | Seek +5 seconds |

### Toast Notifications

Small notification bar at bottom center for:
- `✓ Saved` — green
- `→ Skipped` — neutral
- `✕ Error message` — red

Auto-dismiss after 2.8 seconds.

---

## Design System

```css
--bg:      #0F0F0F   /* page background */
--surface: #1C1C1E   /* cards */
--border:  #2C2C2E   /* borders, inactive buttons */
--text:    #F5F0E8   /* primary text (warm white) */
--muted:   #8E8E93   /* secondary text */
--accent:  #E8A44A   /* amber — active state, save button, highlights */
--adim:    #7A5520   /* dimmed amber — edited state background */
--op:      #6B9FE4   /* blue — Operator speaker */
--cu:      #5DBF85   /* green — Müştəri speaker */
--err:     #FF453A   /* red — errors */
--ok:      #30D158   /* green — success */
```

**Fonts** (Google Fonts):
- `Inter` — all UI text
- `JetBrains Mono` — timestamps, speed button, file numbers

---

## App Behavior

- On load: fetch sample list, auto-load first file
- After Save or Skip: auto-load next file in queue
- If on last file and saved: refresh queue from server
- Files already in `finished/` are excluded from queue — restarting mid-session resumes automatically
- If no audio match found for a transcript: show error toast, don't crash
- Audio `<audio>` element is hidden; all controls are custom

---

## Run Instructions

```bash
pip install flask
python app.py
# open http://localhost:5000
```

---

## Per-Session Workflow

1. Download assigned `.jsonl` files → put in `transcripts/`
2. Download matching audio files → put in `audio/`
3. Run `python app.py`
4. Open `http://localhost:5000`
5. Listen → fix text → Save to Finished
6. When done → upload `finished/` folder back to OneDrive