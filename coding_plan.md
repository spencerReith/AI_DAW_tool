# Coding Plan — AI Accompaniment Tool (V1 POC)

## Step 1 — Project Scaffolding
- Init Electron + React app (e.g. `electron-vite` or `create-react-app` + electron wrapper)
- Set up folder structure: `/frontend`, `/backend`, `/electron`
- Configure Electron main process to launch the app window
- Verify: app window opens with a blank React page

## Step 2 — Python / Flask Backend Bootstrap
- Init Python project in `/backend` with a `requirements.txt`
- Install: `flask`, `mido`, `music21`
- Create a minimal Flask server with a `/health` endpoint
- Verify: `python app.py` starts the server and `/health` returns 200

## Step 3 — Electron ↔ Python Bridge
- On Electron app launch, spawn the Flask server as a child subprocess
- Proxy API calls from the renderer process through Electron's main process (IPC) to Flask
- Verify: React frontend can call `/health` and receive a response end-to-end

## Step 4 — MIDI File Ingestion (Frontend)
- Build the Drop Zone screen (Screen 1)
- Implement drag-and-drop + "Browse file" fallback using the File API
- Accept only `.mid` / `.midi` files; show an error for other types
- On file drop, send the file to the Flask backend via a POST request
- Verify: dropping a `.mid` file logs a success response; dropping a `.txt` shows an error

## Step 5 — MIDI Parsing (Backend)
- Build a `/parse` POST endpoint that receives the MIDI file
- Use `mido` to extract: tempo (BPM), time signature, key signature (if present)
- Return a JSON response: `{ bpm, time_signature, key }`
- Return `"key": null` if not found — do not infer
- Verify: POST a known MIDI file and confirm the returned values match expected metadata

## Step 6 — Session Summary Screen (Frontend)
- Build Screen 2 — display parsed BPM, time signature, key (or "Unknown")
- Show a warning banner if time signature is not 4/4
- Add accompaniment type selector: Drums · Bass · Melody
- Add optional vibe text input
- Add "Generate" button (disabled until an accompaniment type is selected)
- Verify: parsed data from Step 5 renders correctly; all controls work

## Step 7 — Replit Integration
Context: We are swapping the music generation backend from HuggingFace MusicGen to Replicate's Stable Audio 2.5. Here is exactly what needs to change:

1. Dependencies
Remove music21 from requirements.txt if it was only there for generation. Add:
replicate
python-dotenv
2. Environment
Create a .env file in /backend:
REPLICATE_API_TOKEN=your_token_here
Load it at the top of app.py:
pythonfrom dotenv import load_dotenv
load_dotenv()
3. The /generate endpoint
Replace any HuggingFace generation code with this pattern:
pythonimport replicate

input = {
    "prompt": constructed_prompt,  # e.g. "bass track, 120bpm, 4/4, A minor, dark lo-fi"
    "duration": 90                 # seconds, hardcode 90 for V1
}

output = replicate.run(
    "stability-ai/stable-audio-2.5",
    input=input
)

audio_url = output.url
Return { "audio_url": audio_url } to the frontend.
4. Key facts for implementation:

replicate.run() is synchronous and blocking — it handles polling internally. No need to implement your own polling loop.
Output is an MP3 URL on Replicate's CDN, not a WAV and not binary. Update any references to .wav output format to .mp3.
Duration max is 180 seconds (3 minutes). Hardcode 90 for V1.
The prompt is just a plain text string — BPM, key, and vibe all go in as text, no structured conditioning parameters.

5. What does NOT change:

MIDI parsing logic — untouched
Prompt construction logic — untouched, just pipe the output string into the prompt field above
Frontend flow — untouched, it still just receives a URL and downloads it



## Step 8 — Generating Screen + Result Screen (Frontend)
- Build Screen 3: spinner + estimated wait copy + cancel button
- Wire "Generate" button to call `/generate` and show Screen 3 while waiting
- On success, transition to Screen 4
- Build Screen 4: download `.wav` button, "Generate another variation" button, "Start over" link
- Verify: full end-to-end flow from file drop → generate → download works

## Step 9 — Polish & Error Handling
- Handle API errors gracefully (rate limits, timeouts, bad responses) — show user-facing error messages
- Handle malformed or empty MIDI files in the parser
- Ensure Flask subprocess is killed cleanly when Electron app closes
- Verify: intentionally trigger each error case and confirm the UI recovers without crashing
