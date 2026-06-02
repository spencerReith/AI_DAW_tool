# Agentic Prompt Writing Spec

## Overview

Before sending a generation request to Replicate, the backend passes the user's raw input through Claude. Claude rewrites it into a structured Stable Audio 2.5 prompt using the format defined in `stable_audio_prompt_guide.md` — and nothing else. The rewritten prompt is printed in the Flask terminal, then sent to Replicate.

---

## Flow

```
User input (description + BPM)
        │
        ▼
Flask /generate endpoint
        │
        ▼
Claude API (prompt rewriter)
        │  — takes: raw description, BPM
        │  — returns: structured Stable Audio prompt string
        │
        ▼
Print rewritten prompt to Flask terminal
        │
        ▼
Replicate API (stability-ai/stable-audio-2.5)
        │  — input: { prompt: <rewritten>, duration: <n> }
        │
        ▼
Return audio URL to frontend
```

---

## Claude's Job

Claude receives the user's description and BPM and returns a single prompt string — nothing else. No explanation, no alternatives, no commentary. Just the prompt.

Claude rewrites the input using the Stable Audio prompt structure:

```
Format | Genre | Subgenre | Instruments | Moods | Styles | BPM
```

It uses only the fields that are relevant to the user's description. It does not add elements the user didn't imply. BPM is always included since the user provides it explicitly.

---

## System Prompt

```
You are a prompt engineer for Stability AI's Stable Audio 2.5 model.

Your only job is to rewrite a user's beat description into a structured Stable Audio prompt.

Use this format, including only the fields that apply:
Format: Band | Genre: <genre> | Subgenre: <subgenre> | Instruments: <list> | Moods: <list> | BPM: <bpm>

Rules:
- Output the prompt string only. No explanation, no punctuation outside the prompt, no markdown.
- Do not invent elements the user did not describe or imply.
- BPM must always be included using the value provided.
- Base your word choices strictly on the vocabulary and examples in the Stable Audio prompt guide.
- Prefer specific instrument names over vague terms (e.g. "808 kick" over "bass drum").
- Keep it concise. Do not pad with unnecessary adjectives.
```

---

## User Message

```
Description: <user's raw description>
BPM: <bpm>
```

---

## Implementation (backend/app.py)

- Use the `anthropic` Python SDK
- Model: `claude-opus-4-8` (most capable, best prompt quality)
- Call Claude synchronously before calling Replicate
- Print the rewritten prompt to the terminal before the Replicate call
- If the Claude call fails, fall back to the raw description + BPM string and log the error

---

## Example

**User input:**
```
Description: dark trap beat, heavy 808s
BPM: 140
```

**Claude output:**
```
Genre: Trap | Instruments: 808 Kick, Syncopated Percussion, lush synthesizer pads, tap delay marimba arp | Moods: Ethereal, Atmospheric, Hypnotic | BPM: 140
```

**Replicate input:**
```json
{
  "prompt": "Genre: Trap | Instruments: 808 Kick, Syncopated Percussion, lush synthesizer pads, tap delay marimba arp | Moods: Ethereal, Atmospheric, Hypnotic | BPM: 140",
  "duration": 90
}
```
