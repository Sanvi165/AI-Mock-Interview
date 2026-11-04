import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getRoadmap } from "../api/interviewApi";
import LoadingState, { EmptyState, ErrorState } from "../components/LoadingState.jsx";

const URGENCY_BADGE = { High: "badge-red", Medium: "badge-amber", Low: "badge-blue" };

export default function SkillRoadmap() {
  const [roadmap, setRoadmap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setRoadmap(await getRoadmap());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState message="Building your roadmap..." />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  if (roadmap.items.length === 0) {
    return (
      <EmptyState title="No roadmap yet" message={roadmap.message}>
        <Link className="btn btn-primary" to="/setup">
          Start an interview
        </Link>
      </EmptyState>
    );
  }

  return (
    <div className="stack">
      <div className="page-header">
        <h1 className="page-title">Skill gap roadmap</h1>
        <p className="page-subtitle">
          Topics to revise, weakest first, based on {roadmap.generated_from_answers} answer(s).
        </p>
      </div>

      {roadmap.items.map((item) => (
        <div className="card roadmap-item" key={item.topic}>
          <div className="roadmap-head">
            <div className="priority-number">{item.priority}</div>
            <div>
              <h3>{item.topic}</h3>
              <p className="muted">{item.reason}</p>
            </div>
            <span className={`badge ${URGENCY_BADGE[item.urgency] || "badge-gray"}`}>
              {item.urgency} priority
            </span>
          </div>

          <div className="grid grid-2">
            <div>
              <h4>What to study</h4>
              <ul className="bullet-list">
                {item.study_focus.map((focus) => (
                  <li key={focus}>{focus}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4>Practice questions</h4>
              <ul className="bullet-list">
                {item.practice_questions.map((question) => (
                  <li key={question}>{question}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      ))}

      <div className="row">
        <Link className="btn btn-primary" to="/setup">
          Practise these topics
        </Link>
      </div>
    </div>
  );
}