import { useCallback, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext.jsx";
import Sidebar from "./components/Sidebar.jsx";
import Login from "./pages/Login.jsx";
import Home from "./pages/Home.jsx";
import InterviewSetup from "./pages/InterviewSetup.jsx";
import InterviewSession from "./pages/InterviewSession.jsx";
import InterviewResult from "./pages/InterviewResult.jsx";
import InterviewHistory from "./pages/InterviewHistory.jsx";
import SkillRoadmap from "./pages/SkillRoadmap.jsx";
import Privacy from "./pages/Privacy.jsx";
import Review from "./pages/Review.jsx";

function NotFound() {
  return (
    <div className="empty-state">
      <h2>Page not found</h2>
      <p className="muted">The page you are looking for does not exist.</p>
      <Link className="btn btn-primary" to="/">
        Go to Home
      </Link>
    </div>
  );
}

export default function App() {
  const { user, loading } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = useCallback(() => setMenuOpen(false), []);

  if (loading) {
    return (
      <div className="auth-page">
        <p className="muted">Loading...</p>
      </div>
    );
  }

  // Not logged in: show only the Sign up / Log in page.
  if (!user) return <Login />;

  return (
    <div className="app-shell">
      <Sidebar open={menuOpen} onClose={closeMenu} />
      {menuOpen ? <div className="sidebar-backdrop" onClick={closeMenu} /> : null}

      <div className="app-main">
        <div className="mobile-bar">
          <button className="menu-btn" onClick={() => setMenuOpen(true)} aria-label="Open menu">
            Menu
          </button>
          <span className="mobile-title">AI Mock Interview</span>
        </div>

        <main className="container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/setup" element={<InterviewSetup />} />
            <Route path="/interview/:id" element={<InterviewSession />} />
            <Route path="/result/:id" element={<InterviewResult />} />
            <Route path="/review/:id" element={<Review />} />
            <Route path="/history" element={<InterviewHistory />} />
            <Route path="/roadmap" element={<SkillRoadmap />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}