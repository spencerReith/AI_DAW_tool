# Feature Spec: Multi-Variation Beat Generation

## Overview

The user can request 1–4 variations of the same beat in a single generation. Each variation runs through the full pipeline (Claude prompt rewrite → Stable Audio) in parallel. All results land in the PlayerPage as separate numbered tracks.

---

## UI Changes

### GeneratorPage
- Add a **variations** number input alongside BPM and duration
- Range: 1–4, default: 1
- Same styling as the existing BPM/duration inputs

### PlayerPage
- Update to accept an **array of audio URLs** instead of a single URL
- Each URL becomes a separate numbered `TrackRow`
- No other UX changes — play/pause/seek/download already work per-row

---

## Backend Changes (`/generate` in `app.py`)

### Request
- Add `variations` field (int, 1–4, default 1)

### Pipeline (per variation, all run in parallel)
1. Call Claude with the same user description + BPM to get a **rewritten prompt** — Claude is called once per variation independently, no changes to the Claude setup
2. Call Stable Audio on Replicate with that rewritten prompt
3. Download and save the result to `generated/`

### Response
- Return `audio_urls`: array of local URLs (one per variation)
- Existing single-variation response shape (`audio_url`) replaced with `audio_urls` array

---

## Data Flow

```
User: description + BPM + duration + variations (1–4)
  │
  ├─ [parallel] → Claude rewrite #1 → Stable Audio #1 → save → URL 1
  ├─ [parallel] → Claude rewrite #2 → Stable Audio #2 → save → URL 2
  ├─ [parallel] → Claude rewrite #3 → Stable Audio #3 → save → URL 3
  └─ [parallel] → Claude rewrite #4 → Stable Audio #4 → save → URL 4
                                                              │
                                              PlayerPage (tracks 01–04)
```

---

## Files to Change

| File | Change |
|------|--------|
| `backend/app.py` | Parallelise generation with `asyncio` or `concurrent.futures`, return `audio_urls` array |
| `frontend/src/App.jsx` — `GeneratorPage` | Add variations input (1–4) |
| `frontend/src/App.jsx` — `PlayerPage` | Accept `audioUrls` array, initialise one track per URL |
| `frontend/src/App.jsx` — `App` | Pass array through to PlayerPage |

---

## Constraints

- Max 4 variations (Replicate cost + wait time)
- Claude agent is unchanged — just called N times independently
- All N Replicate calls fire in parallel
- If one variation fails, the others still return — failed tracks show an error in their row
