import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteHistoryItem, getHistory } from "../api/interviewApi";
import LoadingState, { EmptyState, ErrorState } from "../components/LoadingState.jsx";
import { formatDate, formatScore, scoreTone, statusLabel } from "../utils/formatters";

export default function InterviewHistory() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setSessions(await getHistory());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleDelete(id) {
    if (!window.confirm("Delete this interview and all its answers permanently?")) return;
    setActionError("");
    try {
      await deleteHistoryItem(id);
      setSessions((previous) => previous.filter((s) => s.id !== id));
    } catch (err) {
      setActionError(err.message);
    }
  }

  if (loading) return <LoadingState message="Loading your interviews..." />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  if (sessions.length === 0) {
    return (
      <EmptyState
        title="No interviews saved yet"
        message="Completed and in-progress interviews appear here and in the sidebar."
      >
        <Link className="btn btn-primary" to="/setup">
          Start an interview
        </Link>
      </EmptyState>
    );
  }

  return (
    <div className="stack">
      <div className="page-header row between">
        <div>
          <h1 className="page-title">All interviews</h1>
          <p className="page-subtitle">{sessions.length} saved interview(s).</p>
        </div>
        <Link className="btn btn-primary" to="/setup">
          New interview
        </Link>
      </div>

      {actionError ? <div className="banner banner-error">{actionError}</div> : null}

      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Role</th>
              <th>Type</th>
              <th>Answered</th>
              <th>Score</th>
              <th>Status</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.id}>
                <td>{formatDate(s.created_at)}</td>
                <td>
                  {s.role}
                  <div className="field-hint">{s.domain}</div>
                </td>
                <td>{s.interview_type}</td>
                <td>
                  {s.answered_count} / {s.question_count}
                </td>
                <td>
                  <span className={`badge badge-score tone-${scoreTone(s.overall_score)}`}>
                    {formatScore(s.overall_score)}
                  </span>
                </td>
                <td>{statusLabel(s.status)}</td>
                <td>
                  <div className="row">
                    {s.status === "completed" ? (
                      <Link className="btn btn-secondary btn-small" to={`/result/${s.id}`}>
                        Review
                      </Link>
                    ) : (
                      <Link className="btn btn-secondary btn-small" to={`/interview/${s.id}`}>
                        Resume
                      </Link>
                    )}
                    <button className="btn btn-ghost btn-small" onClick={() => handleDelete(s.id)}>
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}