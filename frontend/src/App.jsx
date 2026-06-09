import { useState, useRef, useEffect } from 'react';
import rubinRaw from '../../rubin.txt?raw';
import './App.css';

const FLASK_URL = 'http://localhost:5001';

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

  useEffect(() => {
    function handleKey(e) {
      if (e.key === 'Enter') onGo();
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onGo]);

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
function GeneratorPage({ onGenerate }) {
  const [description, setDescription] = useState('');
  const [bpm, setBpm] = useState('');
  const [duration, setDuration] = useState('90');
  const [variations, setVariations] = useState('1');
  const [loading, setLoading] = useState(false);
  const [loadingText, setLoadingText] = useState('generate');
  const [error, setError] = useState(null);
  const [seedFile, setSeedFile] = useState(null);
  const [seedLabel, setSeedLabel] = useState('');
  const [noiseLevel, setNoiseLevel] = useState(0.5);
  const [recording, setRecording] = useState(false);

  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const recordingStartRef = useRef(null);

  useEffect(() => {
    if (!loading) { setLoadingText('generate'); return; }
    const frames = ['generating.', 'generating..', 'generating...'];
    let i = 0;
    const id = setInterval(() => { i = (i + 1) % frames.length; setLoadingText(frames[i]); }, 400);
    return () => clearInterval(id);
  }, [loading]);

  function clearSeed() {
    setSeedFile(null);
    setSeedLabel('');
    setNoiseLevel(0.5);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }

  function handleFileChange(e) {
    const f = e.target.files[0];
    if (!f) return;
    clearSeed();
    setSeedFile(f);
    setSeedLabel(f.name);
  }

  async function startSketch() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      recordingStartRef.current = Date.now();
      mr.ondataavailable = e => chunksRef.current.push(e.data);
      mr.onstop = () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const secs = Math.round((Date.now() - recordingStartRef.current) / 1000);
        const m = Math.floor(secs / 60);
        const s = secs % 60;
        clearSeed();
        setSeedFile(blob);
        setSeedLabel(`sketch (${m}:${String(s).padStart(2, '0')})`);
        setRecording(false);
      };
      mr.start();
      mediaRecorderRef.current = mr;
      setRecording(true);
    } catch {
      setError('mic access denied');
    }
  }

  function stopSketch() {
    mediaRecorderRef.current?.stop();
  }

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      let res;
      if (seedFile) {
        const form = new FormData();
        form.append('description', description);
        form.append('bpm', Number(bpm));
        form.append('duration', Number(duration));
        form.append('variations', Number(variations));
        form.append('seed', seedFile, seedLabel.startsWith('sketch') ? 'sketch.webm' : seedFile.name);
        form.append('noise_level', noiseLevel);
        res = await fetch(`${FLASK_URL}/generate`, { method: 'POST', body: form });
      } else {
        res = await fetch(`${FLASK_URL}/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ description, bpm: Number(bpm), duration: Number(duration), variations: Number(variations) }),
        });
      }
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'generation failed');
      onGenerate(data.audio_urls);
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
          placeholder="_"
          value={description}
          onChange={e => setDescription(e.target.value)}
          disabled={loading}
        />
      </div>
      <div className="gen-field">
        <p className="field-label">seed audio <span className="field-optional">(optional)</span></p>
        <div className="seed-row">
          <div className="seed-inputs">
            <input
              ref={fileInputRef}
              type="file"
              accept=".mp3,.wav"
              style={{ display: 'none' }}
              onChange={handleFileChange}
              disabled={loading}
            />
            {seedFile ? (
              <div className="seed-active">
                <span className="seed-name">{seedLabel}</span>
                <button className="seed-clear" onClick={clearSeed} disabled={loading}>×</button>
              </div>
            ) : (
              <div className="seed-buttons">
                <button className="seed-upload-btn" onClick={() => fileInputRef.current.click()} disabled={loading}>
                  + choose file
                </button>
                <button
                  className={`seed-sketch-btn${recording ? ' recording' : ''}`}
                  onClick={recording ? stopSketch : startSketch}
                  disabled={loading}
                >
                  {recording ? 'stop' : 'sketch'}
                </button>
              </div>
            )}
          </div>
          {seedFile && (
            <div className="noise-field">
              <p className="field-label">noise level {noiseLevel.toFixed(2)}</p>
              <input
                type="range"
                className="noise-slider"
                min="0.1"
                max="1.0"
                step="0.05"
                value={noiseLevel}
                onChange={e => setNoiseLevel(Number(e.target.value))}
                disabled={loading}
              />
            </div>
          )}
        </div>
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
            max="380"
            value={duration}
            onChange={e => setDuration(e.target.value)}
            onBlur={e => setDuration(String(Math.min(380, Math.max(1, Number(e.target.value) || 1))))}
            disabled={loading}
          />
        </div>
        <div className="gen-field">
          <p className="field-label">variations</p>
          <input
            className="gen-bpm"
            type="number"
            placeholder="1"
            min="1"
            max="4"
            value={variations}
            onChange={e => setVariations(e.target.value)}
            onBlur={e => setVariations(String(Math.min(4, Math.max(1, Number(e.target.value) || 1))))}
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
        {loadingText}
      </button>
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
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            setTimeout(() => URL.revokeObjectURL(a.href), 100);
          });
      }}>↓</button>
    </div>
  );
}

function PlayerPage({ audioUrls, onGenerateMore }) {
  const audioCtxRef = useRef(null);
  const buffersRef  = useRef({});  // id -> AudioBuffer
  const rafRef      = useRef(null);
  const activeRef   = useRef(null);
  const genRef      = useRef(0);

  const [tracks, setTracks] = useState(() =>
    (audioUrls || []).map((_, i) => ({ id: i + 1, duration: 0, isPlaying: false, currentTime: 0 }))
  );

  useEffect(() => {
    if (!audioUrls?.length) return;
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    audioCtxRef.current = ctx;

    audioUrls.forEach((url, i) => {
      const id = i + 1;
      fetch(url)
        .then(r => { if (!r.ok) throw new Error(`fetch failed: ${r.status}`); return r.arrayBuffer(); })
        .then(ab => ctx.decodeAudioData(ab))
        .then(buf => {
          buffersRef.current[id] = buf;
          setTracks(prev => prev.map(t => t.id === id ? { ...t, duration: buf.duration } : t));
        })
        .catch(e => setTracks(prev => prev.map(t => t.id === id ? { ...t, error: e.message } : t)));
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
    genRef.current++;
    try { a.node.stop(); } catch (_) {}
    activeRef.current = null;
    const ctx = audioCtxRef.current;
    return { id: a.id, currentTime: Math.min(a.offsetAt + (ctx.currentTime - a.startedAt), a.duration) };
  }

  function startNode(id, offsetAt, duration) {
    const ctx = audioCtxRef.current;
    const buf = buffersRef.current[id];
    if (!ctx || !buf) return;
    const gen = ++genRef.current;
    const node = ctx.createBufferSource();
    node.buffer = buf;
    node.connect(ctx.destination);
    node.start(0, offsetAt);
    activeRef.current = { id, node, startedAt: ctx.currentTime, offsetAt, duration };
    node.onended = () => {
      if (genRef.current !== gen) return;
      activeRef.current = null;
      setTracks(p => p.map(t => t.id === id ? { ...t, isPlaying: false, currentTime: 0 } : t));
    };
  }

  function togglePlay(id) {
    const ctx = audioCtxRef.current;
    if (!ctx || !buffersRef.current[id]) return;
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
    if (!track || !buffersRef.current[id]) return;
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
      {!audioUrls?.length && <p className="error">no audio loaded — go back and generate a beat.</p>}
      <div className="track-list">
        {tracks.map(track => (
          <TrackRow
            key={track.id}
            track={track}
            buffer={buffersRef.current[track.id]}
            url={audioUrls?.[track.id - 1]}
            onToggle={() => togglePlay(track.id)}
            onSeek={r => seek(track.id, r)}
          />
        ))}
      </div>
      <button className="generate-more-btn" onClick={onGenerateMore}>generate more</button>
    </div>
  );
}

function App() {
  const [screen, setScreen] = useState('launch');
  const [audioUrls, setAudioUrls] = useState([]);

  const goToPlayer = (urls) => { setAudioUrls(Array.isArray(urls) ? urls : [urls]); setScreen('player'); };

  if (screen === 'launch') return <LaunchPage onGo={() => setScreen('generator')} />;
  if (screen === 'generator') return <GeneratorPage onGenerate={goToPlayer} />;
  return <PlayerPage audioUrls={audioUrls} onGenerateMore={() => setScreen('generator')} />;
}

export default App;
