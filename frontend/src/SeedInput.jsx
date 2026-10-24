// Desktop-only seed audio picker/recorder. Reports {file, filename, noiseLevel} or null via onChange.
import { useState, useRef, useEffect } from 'react';

export default function SeedInput({ disabled, onChange, onError }) {
  const [seedFile, setSeedFile] = useState(null);
  const [seedLabel, setSeedLabel] = useState('');
  const [noiseLevel, setNoiseLevel] = useState(0.5);
  const [recording, setRecording] = useState(false);
  const [seedOpen, setSeedOpen] = useState(false);

  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const recordingStartRef = useRef(null);
  const sketchAudioRef = useRef(null);
  const [sketchUrl, setSketchUrl] = useState(null);
  const [sketchPlaying, setSketchPlaying] = useState(false);

  // keep parent in sync with current seed
  useEffect(() => {
    onChange(seedFile ? {
      file: seedFile,
      filename: seedLabel.startsWith('recording') ? 'sketch.webm' : seedFile.name,
      noiseLevel,
    } : null);
  }, [seedFile, seedLabel, noiseLevel]);

  function clearSeed() {
    // stop playback and revoke sketch blob URL
    if (sketchAudioRef.current) { sketchAudioRef.current.pause(); sketchAudioRef.current = null; }
    if (sketchUrl) { URL.revokeObjectURL(sketchUrl); setSketchUrl(null); }
    setSketchPlaying(false);
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
        const url = URL.createObjectURL(blob);
        setSketchUrl(url);
        setSeedFile(blob);
        setSeedLabel(`recording (${m}:${String(s).padStart(2, '0')})`);
        setRecording(false);
      };
      mr.start();
      mediaRecorderRef.current = mr;
      setRecording(true);
    } catch {
      onError('mic access denied');
    }
  }

  function stopSketch() {
    mediaRecorderRef.current?.stop();
  }

  return (
    <div className="gen-field">
      <p className="field-label seed-toggle" onClick={() => setSeedOpen(o => !o)}>
        seed audio <span className="field-optional">(optional)</span>
        <span className="seed-arrow">{seedOpen ? '▾' : '▸'}</span>
      </p>
      {seedOpen && <div className="seed-row">
        <div className="seed-inputs">
          <input
            ref={fileInputRef}
            type="file"
            accept=".mp3,.wav"
            style={{ display: 'none' }}
            onChange={handleFileChange}
            disabled={disabled}
          />
          {seedFile ? (
            <div className="seed-active">
              <span className="seed-name">{seedLabel}</span>
              {sketchUrl && (
                <button className="seed-play" disabled={disabled} onClick={() => {
                  if (!sketchAudioRef.current) {
                    const audio = new Audio(sketchUrl);
                    sketchAudioRef.current = audio;
                    audio.onended = () => { sketchAudioRef.current = null; setSketchPlaying(false); };
                  }
                  if (sketchPlaying) {
                    sketchAudioRef.current.pause();
                    sketchAudioRef.current.currentTime = 0;
                    sketchAudioRef.current = null;
                    setSketchPlaying(false);
                  } else {
                    sketchAudioRef.current.play();
                    setSketchPlaying(true);
                  }
                }}>{sketchPlaying ? '‖' : '▶'}</button>
              )}
              <button className="seed-clear" onClick={clearSeed} disabled={disabled}>×</button>
            </div>
          ) : (
            <div className="seed-buttons">
              <button className="seed-upload-btn" onClick={() => fileInputRef.current.click()} disabled={disabled}>
                + choose file
              </button>
              <button
                className={`seed-sketch-btn${recording ? ' recording' : ''}`}
                onClick={recording ? stopSketch : startSketch}
                disabled={disabled}
              >
                {recording ? 'stop' : 'record'}
              </button>
            </div>
          )}
        </div>
        {seedFile && (
          <div className="noise-field">
            <p className="field-label">diverge from seed: {noiseLevel.toFixed(2)}</p>
            <input
              type="range"
              className="noise-slider"
              min="0.1"
              max="1.0"
              step="0.05"
              value={noiseLevel}
              onChange={e => setNoiseLevel(Number(e.target.value))}
              disabled={disabled}
            />
          </div>
        )}
      </div>}
    </div>
  );
}
