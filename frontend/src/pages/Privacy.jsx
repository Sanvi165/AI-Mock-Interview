import { useEffect, useState } from "react";
import { deleteAllHistory, getHealth } from "../api/interviewApi";

export default function Privacy() {
  const [mode, setMode] = useState("checking");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    getHealth()
      .then((data) => setMode(data.ai_mode))
      .catch(() => setMode("offline"));
  }, []);

  async function handleDeleteAll() {
    const confirmed = window.confirm(
      "Permanently delete ALL saved interviews, answers, scores and feedback? This cannot be undone."
    );
    if (!confirmed) return;
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const result = await deleteAllHistory();
      setMessage(`Deleted ${result.deleted} interview(s) and all related data.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="stack narrow">
      <div className="page-header">
        <h1 className="page-title">Privacy and data</h1>
        <p className="page-subtitle">What this app stores, what leaves your computer, and how to delete it.</p>
      </div>

      <div className="card stack-small">
        <h3 className="card-title">What is stored</h3>
        <p>
          Your interview setups, questions, typed or transcribed answers, scores and feedback are saved
          in a database file (<code>interview.db</code>) on the computer running the backend. There is
          no account system and no cloud database.
        </p>
      </div>

      <div className="card stack-small">
        <h3 className="card-title">What is sent to other services</h3>
        <ul className="bullet-list">
          <li>
            <strong>AI service:</strong>{" "}
            {mode === "gemini"
              ? "An AI key is configured, so your role details, questions and answers are sent to the AI provider to generate questions and feedback."
              : "Not active right now (demo mode). If you add an AI key, your questions and answers will be sent to the AI provider."}
          </li>
          <li>
            <strong>Speech recognition:</strong> in Chrome and Edge, the browser's built-in speech
            recognition may send your voice audio to the browser vendor's servers. Type your answers if
            you do not want that.
          </li>
          <li>
            <strong>Reading questions aloud</strong> uses your browser's text-to-speech on your device.
          </li>
        </ul>
      </div>

      <div className="card stack-small">
        <h3 className="card-title">Video recording</h3>
        <p>
          Recording is optional and needs your explicit permission. The recording stays in your browser
          and is never uploaded or saved by this app. If you do not download it before finishing, it is
          lost. This app does not analyse faces, emotions or personality.
        </p>
      </div>

      <div className="card stack-small">
        <h3 className="card-title">Delete your data</h3>
        <p>
          You can delete a single interview from the History page, or remove everything below.
        </p>
        {message ? <div className="banner banner-success">{message}</div> : null}
        {error ? <div className="banner banner-error">{error}</div> : null}
        <div>
          <button className="btn btn-danger" onClick={handleDeleteAll} disabled={busy}>
            {busy ? "Deleting..." : "Delete all my interview data"}
          </button>
        </div>
      </div>
    </div>
  );
}