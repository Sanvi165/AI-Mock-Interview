import { formatTimer } from "../utils/formatters";

const KIND_LABEL = {
  followup: "Follow-up question",
  simpler: "Simpler question",
};

export default function QuestionCard({
  question,
  number,
  elapsed,
  timeLimit,
  timerRunning,
  ttsSupported,
  speaking,
  onSpeak,
  onStopSpeaking,
}) {
  const overTime = elapsed > timeLimit;
  return (
    <div className="card question-card">
      <div className="question-meta">
        <span className="badge badge-blue">Question {number}</span>
        <span className="badge badge-gray">{question.topic}</span>
        <span className="badge badge-gray">{question.difficulty}</span>
        {KIND_LABEL[question.kind] ? (
          <span className="badge badge-amber">{KIND_LABEL[question.kind]}</span>
        ) : null}
        <span className={`timer ${overTime ? "over" : ""}`} title="Suggested time per answer">
          {formatTimer(elapsed)} / {formatTimer(timeLimit)}
          {!timerRunning ? " (stopped)" : ""}
        </span>
      </div>

      <h2 className="question-text">{question.text}</h2>

      {ttsSupported ? (
        <div className="row">
          {speaking ? (
            <button className="btn btn-secondary btn-small" onClick={onStopSpeaking}>
              Stop reading
            </button>
          ) : (
            <button className="btn btn-secondary btn-small" onClick={onSpeak}>
              Read question aloud
            </button>
          )}
        </div>
      ) : (
        <p className="field-hint">Reading aloud is not supported in this browser.</p>
      )}
      {overTime ? (
        <p className="field-hint">
          The suggested time is over. You can still answer, but practise keeping answers concise.
        </p>
      ) : null}
    </div>
  );
}