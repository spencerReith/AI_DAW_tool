// Step 1: Launch page — beats title + Rick Rubin ASCII typewriter + go button
// Step 6: Drop Zone (Screen 1) + Session Summary (Screen 2)
// Step 7b: Colab URL input wired into generate request
import { useState, useRef, useEffect } from 'react';
import rubinRaw from '../../rubin.txt?raw';
import './App.css';

const FLASK_URL = 'http://localhost:5000';
const ACCOMPANIMENT_TYPES = ['Drums', 'Bass', 'Melody'];

// Split once at module level — never changes
const LINES = rubinRaw.split('\n');

function LaunchPage({ onGo }) {
  const [lineStates, setLineStates] = useState(() => LINES.map(() => ''));
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
        if (tick < startTick[i]) { allDone = false; return ''; }
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
      <h1 className="launch-title">beats</h1>
      <pre className="launch-art">{lineStates.join('\n')}</pre>
      {done && (
        <button className="launch-go" onClick={onGo}>go</button>
      )}
    </div>
  );
}

// Generator page — beat description + BPM input
function GeneratorPage({ onGenerate }) {
  const [description, setDescription] = useState('');
  const [bpm, setBpm] = useState('');

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
        />
      </div>
      <div className="gen-field">
        <p className="field-label">bpm</p>
        <input
          className="gen-bpm"
          type="number"
          placeholder="120"
          value={bpm}
          onChange={e => setBpm(e.target.value)}
        />
      </div>
      <button
        className="generate-btn"
        disabled={!description.trim() || !bpm}
        onClick={onGenerate}
      >
        generate
      </button>
    </div>
  );
}

const DUMMY_AUDIO = '/test_audio/replicate-prediction-eaza12tnaxrm80cs76tr9xtea4.mp3';

function formatTime(s) {
  return `${Math.floor(s / 60)}:${Math.floor(s % 60).toString().padStart(2, '0')}`;
}

function TrackRow({ track, buffer, onToggle, onSeek }) {
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
      <canvas ref={canvasRef} className="track-canvas" onClick={handleClick} />
    </div>
  );
}

function PlayerPage() {
  const audioCtxRef = useRef(null);
  const bufferRef = useRef(null);
  const rafRef = useRef(null);
  // single active source: { id, node, startedAt, offsetAt, duration }
  const activeRef = useRef(null);
  const genRef = useRef(0); // incremented each startNode call; onended ignores stale firings

  const [tracks, setTracks] = useState(() =>
    [1, 2, 3, 4].map(id => ({ id, duration: 0, isPlaying: false, currentTime: 0 }))
  );

  useEffect(() => {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    audioCtxRef.current = ctx;

    fetch(DUMMY_AUDIO)
      .then(r => r.arrayBuffer())
      .then(ab => ctx.decodeAudioData(ab))
      .then(buf => {
        bufferRef.current = buf;
        setTracks(prev => prev.map(t => ({ ...t, duration: buf.duration })));
      });

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
      {tracks.map(track => (
        <TrackRow
          key={track.id}
          track={track}
          buffer={bufferRef.current}
          onToggle={() => togglePlay(track.id)}
          onSeek={r => seek(track.id, r)}
        />
      ))}
    </div>
  );
}

function App() {
  const [screen, setScreen] = useState('launch');
  const [midiData, setMidiData] = useState(null);
  const [accompaniment, setAccompaniment] = useState(null);
  const [vibe, setVibe] = useState('');
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  function isValidMidi(file) {
    return file.name.endsWith('.mid') || file.name.endsWith('.midi');
  }

  // Step 4: send file to /parse; Step 5: backend returns parsed data
  async function handleFile(file) {
    if (!isValidMidi(file)) {
      setError('Please provide a .mid or .midi file.');
      return;
    }
    setError(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch(`${FLASK_URL}/parse`, { method: 'POST', body: form });
      const data = await res.json();
      setMidiData(data);
      setAccompaniment(null);
      setVibe('');
      setScreen('summary');
    } catch (e) {
      setError(`Request failed: ${e.message}`);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  // Step 7: send generate request to Flask, which calls Replicate
  async function handleGenerate() {
    setError(null);
    setScreen('generating');
    try {
      const res = await fetch(`${FLASK_URL}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...midiData, accompaniment, vibe }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Generation failed.');
      setScreen('result');
      setMidiData((d) => ({ ...d, resultUrl: data.audio_url }));
    } catch (e) {
      setError(e.message);
      setScreen('summary');
    }
  }

  if (screen === 'launch') {
    return <LaunchPage onGo={() => setScreen('generator')} />;
  }

  if (screen === 'generator') {
    return <GeneratorPage onGenerate={() => setScreen('player')} />;
  }

  if (screen === 'player') {
    return <PlayerPage />;
  }

  if (screen === 'drop') {
    return (
      <div className="app">
        <p className="app-name">AI DAW Tool</p>
        <div
          className="drop-zone"
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => inputRef.current.click()}
        >
          <p>Drop your MIDI file here</p>
          <p className="hint">or click to browse</p>
          <input
            ref={inputRef}
            type="file"
            accept=".mid,.midi"
            style={{ display: 'none' }}
            onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
          />
        </div>
        {error && <p className="error">{error}</p>}
      </div>
    );
  }

  // Step 8: Generating screen (Screen 3)
  if (screen === 'generating') {
    return (
      <div className="app">
        <p className="app-name">AI DAW Tool</p>
        <div className="generating">
          <div className="spinner" />
          <p>Generating your track…</p>
          <p className="hint">This can take a few minutes.</p>
        </div>
      </div>
    );
  }

  // Step 8: Result screen (Screen 4)
  if (screen === 'result') {
    return (
      <div className="app">
        <p className="app-name">AI DAW Tool</p>
        <div className="summary">
          <p className="meta">Your track is ready.</p>
          <a className="generate-btn" href={midiData.resultUrl} download="accompaniment.mp3">
            Download .mp3
          </a>
          <button className="generate-btn" style={{ marginTop: 0 }} onClick={handleGenerate}>
            Generate another variation
          </button>
          <button
            style={{ background: 'none', border: 'none', fontSize: 13, color: '#888', cursor: 'pointer', padding: 0 }}
            onClick={() => { setScreen('drop'); setMidiData(null); }}
          >
            ← Start over
          </button>
        </div>
      </div>
    );
  }

  // Screen 2 — Session Summary
  const { bpm, time_signature, key } = midiData;
  const metaParts = [bpm && `${bpm} BPM`, time_signature, key ?? 'Key unknown'].filter(Boolean);
  const nonStandard = time_signature !== '4/4';

  return (
    <div className="app">
      <p className="app-name">AI DAW Tool</p>
      <div className="summary">
        <p className="meta">{metaParts.join(' · ')}</p>

        {nonStandard && (
          <div className="warning">Non-standard time signature — generation may be less accurate.</div>
        )}

        <div>
          <p className="field-label">Accompaniment</p>
          <div className="accompaniment-selector">
            {ACCOMPANIMENT_TYPES.map((type) => (
              <button
                key={type}
                className={accompaniment === type ? 'selected' : ''}
                onClick={() => setAccompaniment(type)}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="field-label">Vibe (optional)</p>
          <input
            className="vibe-input"
            type="text"
            placeholder="dark, lo-fi, sparse..."
            value={vibe}
            onChange={(e) => setVibe(e.target.value)}
          />
        </div>

        {error && <p className="error">{error}</p>}

        <button
          className="generate-btn"
          disabled={!accompaniment}
          onClick={handleGenerate}
        >
          Generate
        </button>

        <button
          style={{ background: 'none', border: 'none', fontSize: 13, color: '#888', cursor: 'pointer', padding: 0 }}
          onClick={() => { setScreen('drop'); setMidiData(null); }}
        >
          ← Start over
        </button>
      </div>
    </div>
  );
}

export default App;
