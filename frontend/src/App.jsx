import { useState, useRef, useEffect } from 'react';
import rubinRaw from '../../rubin.txt?raw';
import './App.css';

const FLASK_URL = 'http://localhost:5000';
const HUM_URL = 'http://localhost:5001';

// Split once at module level — never changes
const LINES = rubinRaw.split('\n');

function LaunchPage({ onGo }) {
  const [lineStates, setLineStates] = useState(() => LINES.map(l => ' '.repeat(l.length)));
  const [done, setDone] = useState(false);

  useEffect(() => {
    // Build bottom-to-top order, shuffled within chunks of 12 for randomness
    const order = [...Array(LINES.length).keys()].reverse();
    for (let i = 0; i < order.length; i += 12) {
      const end = Math.min(i + 12, order.length);
      for (let j = end - 1; j > i; j--) {
        const k = i + Math.floor(Math.random() * (j - i + 1));
        [order[j], order[k]] = [order[k], order[j]];
      }
    }

    // Random direction per line: 1 = L→R, -1 = R→L
    const dirs = LINES.map(() => (Math.random() < 0.5 ? 1 : -1));

    // Each line's animation start tick (2 ticks apart in the shuffled order)
    const startTick = new Array(LINES.length).fill(0);
    order.forEach((lineIdx, pos) => { startTick[lineIdx] = pos * 1; });

    const CHARS_PER_TICK = 15;
    let tick = 0;

    const id = setInterval(() => {
      tick++;
      let allDone = true;

      setLineStates(LINES.map((line, i) => {
        if (tick < startTick[i]) { allDone = false; return ' '.repeat(line.length); }
        const chars = Math.min((tick - startTick[i]) * CHARS_PER_TICK, line.length);
        if (chars < line.length) allDone = false;
        if (dirs[i] === 1) return line.slice(0, chars);
        // R→L: pad left so columns stay anchored
        const start = line.length - chars;
        return ' '.repeat(start) + line.slice(start);
      }));

      if (allDone) { clearInterval(id); setDone(true); }
    }, 16);

    return () => clearInterval(id);
  }, []);

  return (
    <div className="launch">
      <div className="launch-content">
        <h1 className="launch-title">beats</h1>
        <pre className="launch-art">{lineStates.join('\n')}</pre>
        {done && (
          <button className="launch-go" onClick={onGo}>go</button>
        )}
      </div>
    </div>
  );
}

// Generator page — beat description + BPM input
function GeneratorPage({ onGenerate, onHum }) {
  const [description, setDescription] = useState('');
  const [bpm, setBpm] = useState('');
  const [duration, setDuration] = useState('90');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${FLASK_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, bpm: Number(bpm), duration: Number(duration) }),
      });
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
        <p className="field-label">describe your beat</p>
        <textarea
          className="gen-textarea"
          placeholder="dark, slow, heavy bass..."
          value={description}
          onChange={e => setDescription(e.target.value)}
          disabled={loading}
        />
      </div>
      <div className="gen-row">
        <div className="gen-field">
          <p className="field-label">bpm</p>
          <input
            className="gen-bpm"
            type="number"
            placeholder="120"
            value={bpm}
            onChange={e => setBpm(e.target.value)}
            disabled={loading}
          />
        </div>
        <div className="gen-field">
          <p className="field-label">duration (sec)</p>
          <input
            className="gen-bpm"
            type="number"
            placeholder="90"
            min="1"
            max="180"
            value={duration}
            onChange={e => setDuration(e.target.value)}
            disabled={loading}
          />
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      <button
        className="generate-btn"
        disabled={!description.trim() || !bpm || loading}
        onClick={handleGenerate}
      >
        {loading ? 'generating...' : 'generate'}
      </button>
      <button className="hum-btn" onClick={onHum} disabled={loading}>hum a melody</button>
    </div>
  );
}


function formatTime(s) {
  return `${Math.floor(s / 60)}:${Math.floor(s % 60).toString().padStart(2, '0')}`;
}

function TrackRow({ track, buffer, url, onToggle, onSeek }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !buffer) return;
    if (canvas.offsetWidth > 0) canvas.width = canvas.offsetWidth;
    const ctx = canvas.getContext('2d');
    const { width, height } = canvas;
    ctx.clearRect(0, 0, width, height);

    const data = buffer.getChannelData(0);
    const step = Math.max(1, Math.ceil(data.length / width));
    const playedX = track.duration > 0 ? (track.currentTime / track.duration) * width : 0;

    for (let x = 0; x < width; x++) {
      let max = 0;
      for (let j = 0; j < step; j++) {
        const v = Math.abs(data[x * step + j] || 0);
        if (v > max) max = v;
      }
      const barH = Math.max(1, max * height * 0.9);
      ctx.fillStyle = x <= playedX ? '#000' : '#d0d0d0';
      ctx.fillRect(x, (height - barH) / 2, 1, barH);
    }

    ctx.fillStyle = '#000';
    ctx.fillRect(Math.floor(playedX), 0, 1, height);
  }, [track.currentTime, buffer, track.duration]);

  function handleClick(e) {
    const rect = canvasRef.current.getBoundingClientRect();
    onSeek(Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width)));
  }

  return (
    <div className="track-row">
      <div className="track-meta">
        <span className="track-num">{String(track.id).padStart(2, '0')}</span>
        <button className="track-play" onClick={onToggle}>
          {track.isPlaying ? '‖' : '▶'}
        </button>
        <span className="track-time">
          {formatTime(track.currentTime)} / {formatTime(track.duration)}
        </span>
      </div>
      {track.error
        ? <p className="track-error">{track.error}</p>
        : <canvas ref={canvasRef} className="track-canvas" onClick={handleClick} />
      }
      <button className="track-download" onClick={() => {
        const ts = new Date().toISOString().slice(0,19).replace('T','_').replace(/:/g,'-');
        fetch(url)
          .then(r => r.blob())
          .then(blob => {
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `${ts}-beat${track.id}.mp3`;
            a.click();
            URL.revokeObjectURL(a.href);
          });
      }}>↓</button>
    </div>
  );
}

function PlayerPage({ audioUrl, onGenerateMore }) {
  const audioCtxRef = useRef(null);
  const bufferRef = useRef(null);
  const rafRef = useRef(null);
  // single active source: { id, node, startedAt, offsetAt, duration }
  const activeRef = useRef(null);
  const genRef = useRef(0); // incremented each startNode call; onended ignores stale firings

  const [tracks, setTracks] = useState(() =>
    audioUrl ? [{ id: 1, duration: 0, isPlaying: false, currentTime: 0 }] : []
  );

  useEffect(() => {
    if (!audioUrl) return;
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    audioCtxRef.current = ctx;

    fetch(audioUrl)
      .then(r => { if (!r.ok) throw new Error(`fetch failed: ${r.status}`); return r.arrayBuffer(); })
      .then(ab => ctx.decodeAudioData(ab))
      .then(buf => {
        bufferRef.current = buf;
        setTracks(prev => prev.map(t => ({ ...t, duration: buf.duration })));
      })
      .catch(e => setTracks(prev => prev.map(t => ({ ...t, error: e.message }))));

    const loop = () => {
      const a = activeRef.current;
      if (a) {
        const currentTime = Math.min(a.offsetAt + (ctx.currentTime - a.startedAt), a.duration);
        setTracks(prev => prev.map(t => t.id === a.id ? { ...t, currentTime } : t));
      }
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);

    return () => { ctx.close(); cancelAnimationFrame(rafRef.current); };
  }, []);

  function stopActive() {
    const a = activeRef.current;
    if (!a) return null;
    genRef.current++; // invalidate onended from this node so it doesn't reset currentTime
    try { a.node.stop(); } catch (_) {}
    activeRef.current = null;
    const ctx = audioCtxRef.current;
    return { id: a.id, currentTime: Math.min(a.offsetAt + (ctx.currentTime - a.startedAt), a.duration) };
  }

  function startNode(id, offsetAt, duration) {
    const ctx = audioCtxRef.current;
    const buf = bufferRef.current;
    if (!ctx || !buf) return;
    const gen = ++genRef.current;
    const node = ctx.createBufferSource();
    node.buffer = buf;
    node.connect(ctx.destination);
    node.start(0, offsetAt);
    activeRef.current = { id, node, startedAt: ctx.currentTime, offsetAt, duration };
    node.onended = () => {
      if (genRef.current !== gen) return; // superseded by a newer startNode call
      activeRef.current = null;
      setTracks(p => p.map(t => t.id === id ? { ...t, isPlaying: false, currentTime: 0 } : t));
    };
  }

  function togglePlay(id) {
    const ctx = audioCtxRef.current;
    if (!ctx || !bufferRef.current) return;
    ctx.resume();

    if (activeRef.current?.id === id) {
      const stopped = stopActive();
      setTracks(prev => prev.map(t => t.id === id ? { ...t, isPlaying: false, currentTime: stopped.currentTime } : t));
    } else {
      const stopped = stopActive();
      const track = tracks.find(t => t.id === id);
      startNode(id, track?.currentTime ?? 0, track?.duration ?? 0);
      setTracks(prev => prev.map(t => {
        if (t.id === id) return { ...t, isPlaying: true };
        if (stopped && t.id === stopped.id) return { ...t, isPlaying: false, currentTime: stopped.currentTime };
        return t;
      }));
    }
  }

  function seek(id, ratio) {
    const track = tracks.find(t => t.id === id);
    if (!track || !bufferRef.current) return;
    const offsetAt = ratio * track.duration;
    const wasActive = activeRef.current?.id === id;
    stopActive();
    if (wasActive) startNode(id, offsetAt, track.duration);
    setTracks(prev => prev.map(t =>
      t.id === id ? { ...t, currentTime: offsetAt, isPlaying: wasActive } : t
    ));
  }

  return (
    <div className="player">
      <p className="player-title">beats</p>
      {!audioUrl && <p className="error">no audio loaded — go back and generate a beat.</p>}
      <div className="track-list">
        {tracks.map(track => (
          <TrackRow
            key={track.id}
            track={track}
            buffer={bufferRef.current}
            url={audioUrl}
            onToggle={() => togglePlay(track.id)}
            onSeek={r => seek(track.id, r)}
          />
        ))}
      </div>
      <button className="generate-more-btn" onClick={onGenerateMore}>generate more</button>
    </div>
  );
}

function HumPage({ onBack, onGenerate }) {
  const [file, setFile] = useState(null);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
        <p className="field-label">upload your hum (.mp3)</p>
        <input
          type="file"
          accept=".mp3"
          onChange={e => { setFile(e.target.files[0]); setError(null); }}
          disabled={loading}
        />
      </div>
      <div className="gen-field">
        <p className="field-label">describe the sound</p>
        <textarea
          className="gen-textarea"
          placeholder="dark, lo-fi, warm bass..."
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          disabled={loading}
        />
      </div>
      {error && <p className="error">{error}</p>}
      <button className="generate-btn" disabled={!file || !prompt.trim() || loading} onClick={handleGenerate}>
        {loading ? 'generating...' : 'generate'}
      </button>
      <button className="hum-btn" onClick={onBack} disabled={loading}>← back</button>
    </div>
  );
}

function App() {
  const [screen, setScreen] = useState('launch');
  const [audioUrl, setAudioUrl] = useState(null);

  const goToPlayer = (url) => { setAudioUrl(url); setScreen('player'); };

  if (screen === 'launch') return <LaunchPage onGo={() => setScreen('generator')} />;
  if (screen === 'hum') return <HumPage onBack={() => setScreen('generator')} onGenerate={goToPlayer} />;
  if (screen === 'generator') return <GeneratorPage onGenerate={goToPlayer} onHum={() => setScreen('hum')} />;
  return <PlayerPage audioUrl={audioUrl} onGenerateMore={() => setScreen('generator')} />;
}

export default App;
