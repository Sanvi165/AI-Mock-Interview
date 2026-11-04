import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { completeInterview, getInterview, submitAnswer } from "../api/interviewApi";
import QuestionCard from "../components/QuestionCard.jsx";
import FeedbackPanel from "../components/FeedbackPanel.jsx";
import RecorderPanel from "../components/RecorderPanel.jsx";
import LoadingState, { ErrorState } from "../components/LoadingState.jsx";
import useSpeech from "../hooks/useSpeech";

const TIME_LIMIT_SECONDS = 180; // suggested time per answer (soft limit)
const LETTERS = ["A", "B", "C", "D"];

const ADAPTIVE_BADGE = {
  followup: { cls: "badge-amber", text: "Adaptive: deeper follow-up" },
  simpler: { cls: "badge-amber", text: "Adaptive: simpler question" },
  next: { cls: "badge-blue", text: "Next question" },
  finish: { cls: "badge-green", text: "All questions answered" },
};

// Aptitude answers: short "Correct" message, or "Wrong" with the right answer and the working.
function McqResultCard({ mcq }) {
  return (
    <div className={`card mcq-result ${mcq.is_correct ? "good" : "bad"}`}>
      <h3>{mcq.is_correct ? "Correct" : "Wrong"}</h3>
      {mcq.is_correct ? (
        mcq.quick ? <p>{mcq.quick}</p> : null
      ) : (
        <>
          <p>
            The correct answer is <strong>{mcq.correct_text}</strong>
          </p>
          <p className="mcq-explanation">{mcq.explanation}</p>
        </>
      )}
    </div>
  );
}

export default function InterviewSession() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const startWarning = location.state?.warning || "";

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [session, setSession] = useState(null);
  const [current, setCurrent] = useState(null);
  const [answeredCount, setAnsweredCount] = useState(0);
  const [questionCount, setQuestionCount] = useState(0);

  const [answer, setAnswer] = useState(""); // typed text, or the chosen letter for aptitude
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [actionError, setActionError] = useState("");
  const [recordingUnsaved, setRecordingUnsaved] = useState(false);
  const [autoRead, setAutoRead] = useState(false);

  const usedSpeechRef = useRef(false);

  const appendSpokenText = useCallback((text) => {
    usedSpeechRef.current = true;
    setAnswer((previous) => (previous ? `${previous.trimEnd()} ${text}` : text));
  }, []);

  const speech = useSpeech({ onFinalText: appendSpokenText });
  const { speak, stopSpeaking, stopListening, startListening, listening } = speech;

  const loadSession = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const data = await getInterview(id);
      if (data.status === "completed") {
        navigate(`/result/${id}`, { replace: true });
        return;
      }
      setSession(data);
      setAnsweredCount(data.answered_count);
      setQuestionCount(data.question_count);
      setCurrent(data.questions.find((q) => !q.answered) || null);
    } catch (err) {
      setLoadError(err.message);
    } finally {
      setLoading(false);
    }
  }, [id, navigate]);

  useEffect(() => {
    loadSession();
  }, [loadSession]);

  // Timer: counts up while a question is waiting for an answer.
  const timerRunning = Boolean(current) && !result;
  useEffect(() => {
    if (!timerRunning) return undefined;
    const interval = setInterval(() => setElapsed((seconds) => seconds + 1), 1000);
    return () => clearInterval(interval);
  }, [timerRunning, current]);

  // Optional automatic reading of each new question.
  useEffect(() => {
    if (autoRead && current && !result) speak(current.text);
  }, [autoRead, current, result, speak]);

  const isMcq = Boolean(current && current.options);

  async function handleSubmit() {
    const text = answer.trim();
    if (!text) {
      setActionError(
        isMcq ? "Please choose one of the options." : "Please type or speak an answer before submitting."
      );
      return;
    }
    setActionError("");
    if (listening) stopListening();
    stopSpeaking();
    setSubmitting(true);
    try {
      const response = await submitAnswer(id, {
        question_id: current.id,
        answer_text: text,
        time_taken_seconds: elapsed,
        speech_used: usedSpeechRef.current,
      });
      setResult(response);
      setAnsweredCount(response.answered_count);
      setQuestionCount(response.question_count);
    } catch (err) {
      setActionError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleFinish() {
    if (recordingUnsaved) {
      const proceed = window.confirm(
        "Your video recording has not been downloaded and will be lost. Finish anyway?"
      );
      if (!proceed) return;
    }
    if (listening) stopListening();
    stopSpeaking();
    setFinishing(true);
    setActionError("");
    try {
      await completeInterview(id);
      navigate(`/result/${id}`);
    } catch (err) {
      setActionError(err.message);
      setFinishing(false);
    }
  }

  function handleNext() {
    if (result && result.next_question) {
      setCurrent(result.next_question);
      setAnswer("");
      setElapsed(0);
      setResult(null);
      setActionError("");
      usedSpeechRef.current = false;
    } else {
      handleFinish();
    }
  }

  if (loading) return <LoadingState message="Loading your interview..." />;
  if (loadError) return <ErrorState message={loadError} onRetry={loadSession} />;
  if (finishing) return <LoadingState message="Calculating your results..." />;

  const isAptitude = session.interview_type === "Aptitude";
  const isGd = session.interview_type === "GD";
  const title = isAptitude
    ? `Aptitude: ${session.role}`
    : isGd
    ? "Group discussion"
    : `${session.role} - ${session.interview_type} interview`;
  const badge = result ? ADAPTIVE_BADGE[result.adaptive_action] : null;

  return (
    <div className="stack">
      <div className="page-header row between">
        <div>
          <h1 className="page-title">{title}</h1>
          {!isAptitude && !isGd ? (
            <p className="page-subtitle">
              {session.domain} | {session.experience_level}
            </p>
          ) : null}
        </div>
        {answeredCount >= 1 ? (
          <button className="btn btn-secondary" onClick={handleFinish} disabled={submitting}>
            Finish interview now
          </button>
        ) : null}
      </div>

      {startWarning ? <div className="banner banner-info">{startWarning}</div> : null}
      {actionError ? (
        <div className="banner banner-error" role="alert">
          {actionError}
        </div>
      ) : null}

      <div className="session-layout">
        <div className="stack">
          {!current && !result ? (
            <div className="card center-text stack">
              <h2>All questions are answered</h2>
              <p className="muted">Finish the interview to see your results and roadmap.</p>
              <div>
                <button className="btn btn-primary" onClick={handleFinish}>
                  Finish interview
                </button>
              </div>
            </div>
          ) : null}

          {current ? (
            <QuestionCard
              question={current}
              number={Math.min(answeredCount + (result ? 0 : 1), questionCount)}
              elapsed={elapsed}
              timeLimit={TIME_LIMIT_SECONDS}
              timerRunning={timerRunning}
              ttsSupported={speech.ttsSupported}
              speaking={speech.speaking}
              onSpeak={() => speak(current.text)}
              onStopSpeaking={stopSpeaking}
            />
          ) : null}

          {/* Aptitude: four options to choose from */}
          {isMcq ? (
            <div className="card form">
              <div className="option-list" role="radiogroup" aria-label="Answer options">
                {current.options.map((text, index) => {
                  const letter = LETTERS[index];
                  let state = "";
                  if (result && result.mcq) {
                    if (letter === result.mcq.correct_option) state = "correct";
                    else if (!result.mcq.is_correct && result.mcq.chosen.startsWith(`${letter})`)) state = "wrong";
                  } else if (answer === letter) {
                    state = "selected";
                  }
                  return (
                    <button
                      type="button"
                      key={letter}
                      className={`option-btn ${state}`}
                      onClick={() => {
                        if (!result && !submitting) setAnswer(letter);
                      }}
                    >
                      <span className="option-letter">{letter}</span>
                      <span>{text}</span>
                    </button>
                  );
                })}
              </div>
              {!result ? (
                <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting || !answer}>
                  {submitting ? "Checking..." : "Submit answer"}
                </button>
              ) : null}
            </div>
          ) : null}

          {/* Job interview and GD: type or speak the answer */}
          {current && !result && !isMcq ? (
            <div className="card form">
              <div className="field">
                <label htmlFor="answer">Your answer</label>
                <textarea
                  id="answer"
                  rows={8}
                  maxLength={5000}
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Type your answer here, or use the microphone to speak it."
                  disabled={submitting}
                />
                {speech.interim ? <div className="interim-text">Hearing: {speech.interim}</div> : null}
                <div className="char-count">{answer.length} / 5000</div>
              </div>

              {speech.error ? <div className="field-error">{speech.error}</div> : null}
              {!speech.sttSupported ? (
                <div className="field-hint">
                  Speech recognition is not supported in this browser (use Chrome or Edge). Please
                  type your answer.
                </div>
              ) : null}

              <div className="row">
                {speech.sttSupported ? (
                  listening ? (
                    <button className="btn btn-danger" onClick={stopListening} disabled={submitting}>
                      Stop microphone
                    </button>
                  ) : (
                    <button className="btn btn-secondary" onClick={startListening} disabled={submitting}>
                      Speak your answer
                    </button>
                  )
                ) : null}
                <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
                  {submitting ? "Evaluating your answer..." : "Submit answer"}
                </button>
              </div>
            </div>
          ) : null}

          {result ? (
            <>
              {result.mcq ? (
                <McqResultCard mcq={result.mcq} />
              ) : (
                <FeedbackPanel evaluation={result.evaluation} />
              )}
              <div className="card row between">
                <div>
                  {result.mcq ? (
                    result.next_question ? null : <p className="muted">{result.adaptive_reason}</p>
                  ) : (
                    <>
                      <span className={`badge ${badge.cls}`}>{badge.text}</span>
                      <p className="muted">{result.adaptive_reason}</p>
                    </>
                  )}
                </div>
                <button className="btn btn-primary" onClick={handleNext}>
                  {result.next_question ? "Next question" : "Finish interview"}
                </button>
              </div>
            </>
          ) : null}
        </div>

        <aside className="stack">
          <div className="card">
            <h3 className="card-title">Progress</h3>
            <p>
              <strong>{answeredCount}</strong> {answeredCount === 1 ? "question" : "questions"} answered
            </p>
            <p className="field-hint">
              Keep going as long as you like. Click "Finish interview now" when you want your results.
            </p>
            {speech.ttsSupported ? (
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={autoRead}
                  onChange={(e) => {
                    setAutoRead(e.target.checked);
                    if (!e.target.checked) stopSpeaking();
                  }}
                />
                Read each question aloud automatically
              </label>
            ) : null}
          </div>
          {!isAptitude ? (
            <RecorderPanel onStatusChange={(status) => setRecordingUnsaved(status.unsaved)} />
          ) : null}
        </aside>
      </div>
    </div>
  );
}