// Deprecated: hum/melody-upload flow removed from main app
import { useState, useRef, useEffect } from 'react';

const HUM_URL = 'http://localhost:5001';

export function HumPage({ onBack, onGenerate }) {
  const [file, setFile] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState('generate');
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (!loading) { setLoadingText('generate'); return; }
    const frames = ['generating.', 'generating..', 'generating...'];
    let i = 0;
    const id = setInterval(() => { i = (i + 1) % frames.length; setLoadingText(frames[i]); }, 400);
    return () => clearInterval(id);
  }, [loading]);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    const form = new FormData();
    form.append('file', file);
    form.append('prompt', prompt);
    try {
      const res = await fetch(`${HUM_URL}/hum`, { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'generation failed');
      onGenerate(data.audio_url);
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  }

  return (
    <div className="generator">
      <p className="generator-title">beats</p>
      <div className="gen-field">
        <p className="field-label">upload your melody (.mp3)</p>
        <input
          ref={fileInputRef}
          type="file"
          accept=".mp3"
          style={{ display: 'none' }}
          onChange={e => { setFile(e.target.files[0]); setError(null); }}
          disabled={loading}
        />
        <button className="hum-upload-btn" onClick={() => fileInputRef.current.click()} disabled={loading}>
          {file ? file.name : '+ choose file'}
        </button>
      </div>
      <div className="gen-field">
        <p className="field-label">describe the sound</p>
        <textarea
          className="gen-textarea"
          placeholder="_"
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          disabled={loading}
        />
      </div>
      {error && <p className="error">{error}</p>}
      <button className="generate-btn" disabled={!file || !prompt.trim() || loading} onClick={handleGenerate}>
        {loadingText}
      </button>
      <button className="back-btn" onClick={onBack} disabled={loading}>← back</button>
    </div>
  );
}
