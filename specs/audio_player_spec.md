# Audio Player — Interface Spec

## Overview

A minimal playback interface that appears after generation. Displays all generated beats as stacked rows — each one a waveform you can play, pause, and scrub through. No file loading, no global transport. Just listen.

---

## Layout

Stacked track layout — one row per generated beat, filling the viewport vertically.

```
┌──────────────────────────────────────────────────────┐
│  beats                                               │
├──────┬───────────────────────────────────────────────┤
│ META │  WAVEFORM CANVAS                  ← playhead  │
├──────┼───────────────────────────────────────────────┤
│ META │  WAVEFORM CANVAS                              │
├──────┼───────────────────────────────────────────────┤
│ META │  WAVEFORM CANVAS                              │
└──────┴───────────────────────────────────────────────┘
```

### Track Meta Panel (left, ~120px)
- Beat number (e.g. `01`, `02`) — large, muted
- Play / Pause button — minimal, text-based (`▶` / `‖`)
- Current time / duration in MM:SS — monospaced, updates live

### Waveform Canvas (fills remaining width)
- Waveform rendered on `<canvas>`, vertical bars center-out
- Unplayed portion: light gray (`#d0d0d0`)
- Played portion: black (`#000`)
- Playhead: thin black vertical line
- Click to seek, drag to scrub

---

## Core Features

### 1. Tracks
- Populated automatically from generation output (1 or more beats)
- No manual file loading — audio URLs come from the generator

### 2. Waveform Rendering
- Decoded via Web Audio API (`AudioContext.decodeAudioData`)
- Downsampled to fit canvas width (~1 bar per 2px)
- Redraws on resize

### 3. Playback
- Per-track play/pause
- Playing one track pauses any other (one active at a time)
- Playhead driven by `requestAnimationFrame`
- Click anywhere on waveform to seek

### 4. Time Display
- Live `MM:SS / MM:SS` in the meta panel

---

## Interactions

| Action | Result |
|---|---|
| Click waveform | Seek to that position |
| Drag on waveform | Scrub |
| Click play | Play track, pause others |
| Click pause | Pause, hold position |

---

## Visual Design

Matches the rest of the app — white, black, minimal.

```
Background:        #ffffff
Track row border:  1.5px solid #000 (bottom border between rows)
Waveform played:   #000000
Waveform unplayed: #d0d0d0
Playhead:          #000000
Beat number:       light gray, large
Text:              system-ui, black
Time display:      monospace
```

No hover states, no color accents, no animations on load. The waveform appearing is enough.

---

## Web Audio Graph (per track)

```
audio URL
    │
    ▼
AudioContext.decodeAudioData()
    │
    ▼
AudioBufferSourceNode  ──►  AudioContext.destination
```

A new `AudioBufferSourceNode` is created on each play (they're single-use). The decoded `AudioBuffer` is stored and reused for seeking.

---

## State Shape (per track)

```js
{
  id: number,
  audioUrl: string,
  duration: number,
  audioBuffer: AudioBuffer | null,
  isPlaying: boolean,
  currentTime: number,
  startedAt: number,    // AudioContext.currentTime when playback began
  offsetAt: number,     // seek offset in seconds
}
```
