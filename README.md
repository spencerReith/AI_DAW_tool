# AI DAW Tool

An AI-powered digital audio workstation that uses Claude and Replicate to generate multi-track music from text prompts. Built with Electron + React (frontend) and Flask (backend).

## Prerequisites

- Python 3.10+
- Node.js 18+
- ffmpeg (installed automatically via `imageio-ffmpeg`)
- [Replicate](https://replicate.com) API key
- [Anthropic](https://console.anthropic.com) API key

## Setup

**1. Clone and create a `.env` file in the root:**
```
REPLICATE_API_TOKEN=your_key
ANTHROPIC_API_KEY=your_key
```

**2. Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**3. Frontend / Electron (in a new terminal)**
```bash
npm install
cd frontend && npm install && cd ..
npm run dev
```

The Electron app opens automatically once Vite is ready on `localhost:5173`.
