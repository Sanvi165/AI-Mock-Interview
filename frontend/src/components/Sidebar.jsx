import { useCallback, useEffect, useState } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import { deleteHistoryItem, getHistory } from "../api/interviewApi";
import { formatScore } from "../utils/formatters";
import { useAuth } from "../context/AuthContext.jsx";

const GROUP_ORDER = ["Today", "Yesterday", "Previous 7 days", "Older"];

const NAV_ITEMS = [
  { to: "/roadmap", label: "Skill roadmap" },
  { to: "/history", label: "All interviews" },
];

function groupLabel(iso) {
  const created = new Date(iso);
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfCreated = new Date(created.getFullYear(), created.getMonth(), created.getDate());
  const days = Math.round((startOfToday - startOfCreated) / 86400000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days <= 7) return "Previous 7 days";
  return "Older";
}

export default function Sidebar({ open, onClose }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [error, setError] = useState(false);

  const load = useCallback(async () => {
    try {
      setSessions(await getHistory());
      setError(false);
    } catch {
      setError(true);
    }
  }, []);

  // Reload the list on every page change (so new interviews appear) and close the mobile menu.
  useEffect(() => {
    load();
    if (onClose) onClose();
  }, [load, onClose, location.pathname]);

  async function handleDelete(id) {
    if (!window.confirm("Delete this interview and all its answers permanently?")) return;
    try {
      await deleteHistoryItem(id);
      setSessions((previous) => previous.filter((s) => s.id !== id));
      if (location.pathname.endsWith(`/${id}`)) navigate("/setup");
    } catch (err) {
      window.alert(err.message);
    }
  }

  const groups = {};
  sessions.forEach((session) => {
    const label = groupLabel(session.created_at);
    if (!groups[label]) groups[label] = [];
    groups[label].push(session);
  });

  return (
    <aside className={`sidebar ${open ? "open" : ""}`}>
      <div className="side-head">
        <NavLink to="/" className="side-brand">
          <span className="brand-mark">AI</span> Mock Interview
        </NavLink>
        <button className="side-close" onClick={onClose} aria-label="Close menu">
          Close
        </button>
      </div>

      <NavLink to="/setup" className="side-new">
        + New interview
      </NavLink>

      <nav className="side-nav-list">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `side-nav ${isActive ? "active" : ""}`}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="side-label">Recents</div>
      <div className="side-scroll">
        {error ? <p className="side-empty">Could not load your interviews.</p> : null}
        {!error && sessions.length === 0 ? (
          <p className="side-empty">No interviews yet. Start your first one!</p>
        ) : null}

        {GROUP_ORDER.filter((label) => groups[label]).map((label) => (
          <div key={label} className="side-group">
            <div className="side-group-title">{label}</div>
            {groups[label].map((s) => (
              <div className="side-item" key={s.id}>
                <NavLink
                 to={`/review/${s.id}`}
                 className={({ isActive }) =>
                `side-link ${isActive || location.pathname === `/interview/${s.id}` ? "active" : ""}`
                  }>
                  <span className="side-title">{s.role}</span>
                  <span className="side-meta">
                    {s.interview_type} |{" "}
                    {s.status === "completed" ? `${formatScore(s.overall_score)}/100` : "In progress"}
                  </span>
                </NavLink>
                <button
                  className="side-delete"
                  title="Delete this interview"
                  aria-label="Delete this interview"
                  onClick={() => handleDelete(s.id)}
                >
                  x
                </button>
              </div>
            ))}
          </div>
        ))}
      </div>

      <div className="side-bottom">
        <NavLink
          to="/privacy"
          className={({ isActive }) => `side-nav ${isActive ? "active" : ""}`}
        >
          Privacy and data
        </NavLink>
        
        <div className="side-user">
          <span className="side-user-name" title={user?.email}>
            {user?.username}
          </span>
          <button type="button" className="side-logout" onClick={logout}>
            Log out
          </button>
        </div>
      </div>
    </aside>
  );
}