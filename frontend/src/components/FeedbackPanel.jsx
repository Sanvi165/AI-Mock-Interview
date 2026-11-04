import {
  CRITERIA_LABELS,
  formatScore,
  scoreTone,
  sourceLabel,
} from "../utils/formatters";

function ListSection({ title, items, asTags = false }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="feedback-section">
      <h4>{title}</h4>
      {asTags ? (
        <div className="tag-list">
          {items.map((item) => (
            <span className="tag" key={item}>
              {item}
            </span>
          ))}
        </div>
      ) : (
        <ul className="bullet-list">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function FeedbackPanel({ evaluation }) {
  if (!evaluation) return null;
  const { scores, feedback, metrics } = evaluation;
  const tone = scoreTone(evaluation.overall_score);
  const fillerText = Object.entries(metrics.filler_words || {})
    .map(([word, count]) => `${word} (${count})`)
    .join(", ");

  return (
    <div className="card feedback-panel">
      <div className="score-header">
        <div className={`score-circle tone-${tone}`}>
          <span>{formatScore(evaluation.overall_score)}</span>
          <small>/ 100</small>
        </div>
        <div>
          <h3>{evaluation.label}</h3>
          <span className={`badge ${evaluation.source === "gemini" ? "badge-green" : "badge-amber"}`}>
            Estimated: {sourceLabel(evaluation.source)}
          </span>
        </div>
      </div>

      {evaluation.warning ? <p className="field-hint">{evaluation.warning}</p> : null}

      <div className="feedback-section">
        <h4>Rubric scores (estimated, 0-10)</h4>
        <div className="rubric">
          {Object.keys(CRITERIA_LABELS).map((key) => (
            <div className="rubric-row" key={key}>
              <span>{CRITERIA_LABELS[key]}</span>
              <div className="rubric-bar">
                <div className="rubric-fill" style={{ width: `${scores[key] * 10}%` }} />
              </div>
              <strong>{scores[key]}</strong>
            </div>
          ))}
        </div>
      </div>

      <div className="feedback-section">
        <h4>Measured from your answer</h4>
        <div className="metric-list">
          <div className="metric">
            <strong>{metrics.word_count}</strong>
            <span>words</span>
          </div>
          <div className="metric">
            <strong>{metrics.filler_count}</strong>
            <span>filler words</span>
          </div>
          <div className="metric">
            <strong>{metrics.words_per_minute ?? "-"}</strong>
            <span>words/min</span>
          </div>
        </div>
        {fillerText ? <p className="field-hint">Filler words found: {fillerText}</p> : null}
        {metrics.words_per_minute === null ? (
          <p className="field-hint">Speaking pace is only measured for spoken answers.</p>
        ) : null}
      </div>

      <ListSection title="Strengths" items={feedback.strengths} />
      <ListSection title="Weaknesses" items={feedback.weaknesses} />
      <ListSection title="Missing concepts" items={feedback.missing_concepts} asTags />
      <ListSection title="Suggested improvements" items={feedback.improvements} />

      {feedback.stronger_answer ? (
        <div className="feedback-section">
          <h4>Example of a stronger answer</h4>
          <blockquote className="stronger-answer">{feedback.stronger_answer}</blockquote>
        </div>
      ) : null}
    </div>
  );
}