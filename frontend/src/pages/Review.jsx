import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getHistoryItem } from "../api/interviewApi";
import LoadingState, { EmptyState, ErrorState } from "../components/LoadingState.jsx";
import { formatDate } from "../utils/formatters";

// Read-only revision page: question, your answer and the correct answer. Nothing else.
export default function Review() {
  const { id } = useParams();
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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

  if (loading) return <LoadingState message="Loading..." />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  // Only questions that were answered; unanswered ones are skipped.
  const answered = detail.results.filter((item) => item.evaluation);

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-title">{detail.role}</h1>
        <p className="page-subtitle">{formatDate(detail.created_at)}</p>
      </div>

      {answered.length === 0 ? (
        <EmptyState title="No answers yet" message="You have not answered any question in this interview." />
      ) : (
        <div className="stack">
          {answered.map((item, index) => (
            <div className="card qa-card" key={item.question.id}>
              <span className="qa-number">Question {index + 1}</span>
              <h3 className="qa-question">{item.question.text}</h3>

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
            </div>
          ))}
        </div>
      )}
    </div>
  );
}