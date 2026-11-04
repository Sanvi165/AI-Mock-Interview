import { useCallback, useEffect, useRef, useState } from "react";

const RECORDING_SUPPORTED =
  typeof navigator !== "undefined" &&
  Boolean(navigator.mediaDevices) &&
  typeof navigator.mediaDevices.getUserMedia === "function" &&
  typeof window.MediaRecorder !== "undefined";

function pickMimeType() {
  const options = ["video/webm;codecs=vp8,opus", "video/webm"];
  return options.find((type) => window.MediaRecorder.isTypeSupported(type)) || "";
}

/**
 * Optional webcam recording. The recording stays in the browser: it is never uploaded
 * and the backend never receives it. The user must tick the consent box first.
 * onStatusChange({ unsaved }) tells the page if a recording would be lost on leaving.
 */
export default function RecorderPanel({ onStatusChange }) {
  const [consent, setConsent] = useState(false);
  const [status, setStatus] = useState("idle"); // idle | ready | recording | stopped
  const [error, setError] = useState("");
  const [videoUrl, setVideoUrl] = useState(null);
  const [downloaded, setDownloaded] = useState(false);

  const streamRef = useRef(null);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);
  const previewRef = useRef(null);
  const urlRef = useRef(null);

  const stopTracks = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  // Attach the live camera stream to the preview element.
  useEffect(() => {
    if (previewRef.current && streamRef.current && (status === "ready" || status === "recording")) {
      previewRef.current.srcObject = streamRef.current;
    }
  }, [status]);

  // Tell the parent page whether there is an unsaved recording.
  useEffect(() => {
    if (onStatusChange) {
      onStatusChange({ unsaved: status === "recording" || (Boolean(videoUrl) && !downloaded) });
    }
  }, [status, videoUrl, downloaded, onStatusChange]);

  // Clean up when leaving the page.
  useEffect(
    () => () => {
      if (recorderRef.current) recorderRef.current.onstop = null;
      if (recorderRef.current && recorderRef.current.state !== "inactive") {
        recorderRef.current.stop();
      }
      stopTracks();
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    },
    [stopTracks]
  );

  async function enableCamera() {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      streamRef.current = stream;
      setStatus("ready");
    } catch (err) {
      if (err.name === "NotAllowedError") {
        setError("Camera/microphone permission was denied. You can continue without recording.");
      } else if (err.name === "NotFoundError") {
        setError("No camera or microphone was found. You can continue without recording.");
      } else {
        setError("Could not start the camera. You can continue without recording.");
      }
    }
  }

  function startRecording() {
    if (!streamRef.current) return;
    chunksRef.current = [];
    const mimeType = pickMimeType();
    const recorder = new window.MediaRecorder(
      streamRef.current,
      mimeType ? { mimeType } : undefined
    );
    recorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) chunksRef.current.push(event.data);
    };
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "video/webm" });
      const url = URL.createObjectURL(blob);
      urlRef.current = url;
      setVideoUrl(url);
      setDownloaded(false);
      stopTracks(); // turns the camera light off
      setStatus("stopped");
    };
    recorderRef.current = recorder;
    recorder.start();
    setStatus("recording");
  }

  function stopRecording() {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
  }

  function downloadRecording() {
    if (!videoUrl) return;
    const link = document.createElement("a");
    link.href = videoUrl;
    link.download = "mock-interview-recording.webm";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setDownloaded(true);
  }

  function discardRecording() {
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    urlRef.current = null;
    setVideoUrl(null);
    setDownloaded(false);
    setStatus("idle");
  }

  if (!RECORDING_SUPPORTED) {
    return (
      <div className="card recorder">
        <h3>Video recording (optional)</h3>
        <p className="field-hint">
          Video recording is not supported in this browser. You can still complete the interview.
        </p>
      </div>
    );
  }

  return (
    <div className="card recorder">
      <h3>Video recording (optional)</h3>
      <p className="field-hint">
        The recording stays on your computer. It is never uploaded or saved by this app. Download it
        before finishing the interview, or it will be lost.
      </p>

      {status === "idle" ? (
        <>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
            />
            I allow this page to use my camera and microphone for recording.
          </label>
          <button className="btn btn-secondary" disabled={!consent} onClick={enableCamera}>
            Turn on camera
          </button>
        </>
      ) : null}

      {status === "ready" || status === "recording" ? (
        <>
          <video ref={previewRef} className="preview" autoPlay muted playsInline />
          <div className="row">
            {status === "ready" ? (
              <button className="btn btn-primary btn-small" onClick={startRecording}>
                Start recording
              </button>
            ) : (
              <button className="btn btn-danger btn-small" onClick={stopRecording}>
                Stop recording
              </button>
            )}
            {status === "recording" ? <span className="badge badge-red">Recording</span> : null}
          </div>
        </>
      ) : null}

      {status === "stopped" && videoUrl ? (
        <>
          <video className="preview" src={videoUrl} controls playsInline />
          <div className="row">
            <button className="btn btn-primary btn-small" onClick={downloadRecording}>
              Download recording
            </button>
            <button className="btn btn-ghost btn-small" onClick={discardRecording}>
              Discard
            </button>
          </div>
          {downloaded ? <p className="field-hint">Downloaded.</p> : null}
        </>
      ) : null}

      {error ? <p className="field-error">{error}</p> : null}
    </div>
  );
}