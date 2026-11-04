import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { completeInterview, getHistoryItem } from "../api/interviewApi";
import LoadingState, { ErrorState } from "../components/LoadingState.jsx";
import { formatDate, formatScore, scoreTone } from "../utils/formatters";
import { downloadMarkdownReport, printReport } from "../utils/reportGenerator";

const KIND_LABEL = { followup: "Follow-up", simpler: "Simpler question" };

export default function InterviewResult() {
  const { id } = useParams();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setDetail(await getHistoryItem(id));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleFinish() {
    setActionError("");
    try {
      setDetail(await completeInterview(id));
    } catch (err) {
      setActionError(err.message);
    }
  }

  async function handleDownload() {
    setActionError("");
    try {
      await downloadMarkdownReport(id);
    } catch (err) {
      setActionError(err.message);
    }
  }

  function handlePrint() {
    setActionError("");
    try {
      printReport(detail);
    } catch (err) {
      setActionError(err.message);
    }
  }

  if (loading) return <LoadingState message="Loading results..." />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  const completed = detail.status === "completed";
  const tone = scoreTone(detail.overall_score);

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-title">{detail.role}</h1>
        <p className="page-subtitle">
          {detail.domain} | {detail.experience_level} | {detail.interview_type} |{" "}
          {formatDate(detail.created_at)}
        </p>
      </div>

      {actionError ? <div className="banner banner-error">{actionError}</div> : null}

      {!completed ? (
        <div className="banner banner-warn">
          <div>This interview is not finished yet.</div>
          <div className="row">
            <Link className="btn btn-secondary btn-small" to={`/interview/${id}`}>
              Resume interview
            </Link>
            <button className="btn btn-primary btn-small" onClick={handleFinish}>
              Finish with current answers
            </button>
          </div>
        </div>
      ) : (
        <div className="card score-header">
          <div className={`score-circle large tone-${tone}`}>
            <span>{formatScore(detail.overall_score)}</span>
            <small>/ 100</small>
          </div>
          <div className="stack-small">
            <h2>Overall score</h2>
            {detail.summary ? (
              <>
                <p className="muted">
                  Answered {detail.summary.answered} of {detail.summary.total_questions} questions.
                </p>
                {detail.summary.weak_topics.length ? (
                  <div>
                    <strong>Topics to revise</strong>
                    <div className="tag-list">
                      {detail.summary.weak_topics.map((topic) => (
                        <span className="tag tag-red" key={topic}>
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
              </>
            ) : null}
            <div className="row">
              <button className="btn btn-primary btn-small" onClick={handleDownload}>
                Download report (.md)
              </button>
              <button className="btn btn-secondary btn-small" onClick={handlePrint}>
                Print / save as PDF
              </button>
              <Link className="btn btn-ghost btn-small" to="/roadmap">
                Skill roadmap
              </Link>
            </div>
          </div>
        </div>
      )}

      <div className="stack">
        {detail.results.map((item, index) => (
          <div className="card qa-card" key={item.question.id}>
            <div className="row between">
              <span className="qa-number">Question {index + 1}</span>
              <span className="row">
                <span className="badge badge-gray">{item.question.topic}</span>
                {KIND_LABEL[item.question.kind] ? (
                  <span className="badge badge-amber">{KIND_LABEL[item.question.kind]}</span>
                ) : null}
              </span>
            </div>

            <h3 className="qa-question">{item.question.text}</h3>

            {item.evaluation ? (
              <>
                <div>
                  <div className="qa-label">Your answer</div>
                  <p className="qa-answer">{item.answer_text}</p>
                </div>
                <div>
                  <div className="qa-label">Correct answer</div>
                  <p className="qa-correct">
                    {item.evaluation.feedback.stronger_answer || "Not available."}
                  </p>
                </div>
              </>
            ) : (
              <p className="muted">Not answered.</p>
            )}
          </div>
        ))}
      </div>

      <div className="row">
        <Link className="btn btn-primary" to="/setup">
          Practise again
        </Link>
      </div>
    </div>
  );
}