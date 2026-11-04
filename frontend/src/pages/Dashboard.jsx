import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getProgress } from "../api/interviewApi";
import StatCard from "../components/StatCard.jsx";
import ProgressChart from "../components/ProgressChart.jsx";
import LoadingState, { EmptyState, ErrorState } from "../components/LoadingState.jsx";
import { formatScore, scoreTone } from "../utils/formatters";

export default function Dashboard() {
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setProgress(await getProgress());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState message="Loading your dashboard..." />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  if (!progress || progress.completed_sessions === 0) {
    return (
      <EmptyState
        title="No completed interviews yet"
        message="Finish a mock interview to see your statistics and progress here."
      >
        <Link className="btn btn-primary" to="/setup">
          Start your first interview
        </Link>
      </EmptyState>
    );
  }

  const improvement = progress.improvement;
  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Your interview statistics and progress.</p>
      </div>

      <div className="grid grid-4">
        <StatCard
          label="Completed interviews"
          value={progress.completed_sessions}
          hint={`${progress.total_answers} answers given`}
        />
        <StatCard
          label="Average score"
          value={formatScore(progress.average_score)}
          tone={scoreTone(progress.average_score)}
          hint="out of 100"
        />
        <StatCard
          label="Best score"
          value={formatScore(progress.best_score)}
          tone={scoreTone(progress.best_score)}
        />
        <StatCard
          label="Change since first"
          value={improvement === null ? "-" : `${improvement > 0 ? "+" : ""}${formatScore(improvement)}`}
          tone={improvement === null ? "none" : improvement >= 0 ? "good" : "low"}
          hint={`Latest: ${formatScore(progress.latest_score)}`}
        />
      </div>

      <div className="grid grid-2">
        <div className="card">
          <h3 className="card-title">Score per interview</h3>
          <ProgressChart type="line" data={progress.sessions} />
        </div>
        <div className="card">
          <h3 className="card-title">Average score by topic</h3>
          <ProgressChart type="bar" data={progress.topics} />
        </div>
      </div>

      {progress.weakest_topic ? (
        <div className="banner banner-info">
          <div>
            <strong>Focus area:</strong> your weakest topic so far is {progress.weakest_topic}.
          </div>
          <Link className="btn btn-primary btn-small" to="/roadmap">
            Open skill roadmap
          </Link>
        </div>
      ) : null}

      <div className="row">
        <Link className="btn btn-primary" to="/setup">
          New interview
        </Link>
      </div>
    </div>
  );
}