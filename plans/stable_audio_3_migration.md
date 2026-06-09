# Plan: Migrate from Stable Audio 2.5 (Replicate) → Stable Audio 3 (Stability AI)

## What changes

| | Old | New |
|---|---|---|
| Provider | Replicate | Stability AI direct |
| Model | `stability-ai/stable-audio-2.5` | `stable-audio-3` |
| Call style | `replicate.run(...)` — synchronous, returns URL | POST → get `id` → poll GET until 200 |
| Auth | `REPLICATE_API_TOKEN` | `STABILITY_KEY` |
| Max duration | 190s | 380s |
| Audio bytes | `http_requests.get(output.url).content` | response body directly (`accept: audio/*`) |

---

## Files to touch

### `backend/app.py`

1. **Remove** `import replicate`
2. **Add** `STABILITY_KEY = os.environ.get('STABILITY_KEY')` near the other env reads
3. **Update `SYSTEM_PROMPT`** — change "Stable Audio 2.5" → "Stable Audio 3" in the preamble
4. **Replace the core of `generate_one`** — swap out the `replicate.run(...)` + `.url` fetch block with:
   - POST to `https://api.stability.ai/v2beta/audio/stable-audio/text-to-audio`
     - headers: `authorization: Bearer {STABILITY_KEY}`, `accept: audio/*`
     - form data: `prompt`, `output_format: mp3`, `duration`
   - Assert `response.status_code == 202`, extract `generation_id`
   - Poll `GET https://api.stability.ai/v2beta/audio/results/{generation_id}`
     - `202` → still in progress, sleep 10s and retry
     - `200` → `response.content` is the audio bytes, save and return
     - anything else → raise
5. **Update duration cap** in `/generate` route: `max(1, min(int(...), 380))` — SA3 supports up to 380s

### `.env` / `.env_example`

- Add `STABILITY_KEY=` to `.env_example`
- Add your actual `STABILITY_KEY` value to `.env`

---

## Code sketch for `generate_one` inner block

```python
STABILITY_KEY = os.environ.get('STABILITY_KEY')
STABILITY_URL = 'https://api.stability.ai/v2beta/audio/stable-audio/text-to-audio'
STABILITY_POLL = 'https://api.stability.ai/v2beta/audio/results/{}'

# inside generate_one, replacing the replicate.run block:
res = http_requests.post(
    STABILITY_URL,
    headers={'authorization': f'Bearer {STABILITY_KEY}', 'accept': 'audio/*'},
    files={'none': ''},
    data={'prompt': prompt, 'output_format': 'mp3', 'duration': duration},
)
if res.status_code != 202:
    raise Exception(f'stability start failed: {res.json()}')

generation_id = res.json()['id']

while True:
    poll = http_requests.get(
        STABILITY_POLL.format(generation_id),
        headers={'authorization': f'Bearer {STABILITY_KEY}', 'accept': 'audio/*'},
    )
    if poll.status_code == 202:
        time.sleep(10)
    elif poll.status_code == 200:
        audio_bytes = poll.content
        break
    else:
        raise Exception(f'stability poll failed: {poll.json()}')
```

---

## Testing

1. Add `STABILITY_KEY` to `.env`
2. Start the Flask server
3. Generate a beat from the frontend — confirm audio comes back and saves to `generated/`
4. Check `logs/app.log` for `[stable-audio]` entries with no errors
