import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { createInterview, getHealth } from "../api/interviewApi";
import LoadingState from "../components/LoadingState.jsx";

const LEVELS = ["Fresher", "Junior", "Mid-level", "Senior"];

// Only the job interview uses this list.
const TYPES = [
  { value: "Technical", label: "Technical" },
  { value: "HR", label: "HR / behavioural" },
  { value: "Situational", label: "Situational" },
  { value: "Mixed", label: "Mixed (technical + HR + situational)" },
];

// The topics you can pick in the Aptitude round.
const APTITUDE_TOPICS = [
  "Mixed aptitude",
  "Quantitative aptitude",
  "Logical reasoning",
  "Verbal ability",
  "Data interpretation",
];

// The order of the three rounds on the page.
const ROUNDS = [
  { id: "aptitude", number: 1, title: "Aptitude", text: "Maths, reasoning and verbal questions." },
  { id: "gd", number: 2, title: "Group discussion", text: "GD topics: write the points you would speak." },
  { id: "job", number: 3, title: "Job interview", text: "Questions for the job you are aiming for." },
];

const HEADINGS = {
  aptitude: {
    title: "Aptitude round",
    text: "Practise maths, logical reasoning and verbal questions. Choose a topic and start. Questions begin easy and get harder as you go.",
  },
  gd: {
    title: "Group discussion round",
    text: "Just start. You get a GD topic, write or speak the points you would say in the discussion, and then see a model answer.",
  },
  job: {
    title: "Which job do you want?",
    text: "Type the role you are aiming for. The app works out your branch and asks questions about the role, plus the core fundamentals interviewers usually ask.",
  },
};

export default function InterviewSetup() {
  const navigate = useNavigate();
  const [round, setRound] = useState("aptitude"); // change to "job" to open the job form first
  const [aptitudeTopic, setAptitudeTopic] = useState(APTITUDE_TOPICS[0]);
  const [form, setForm] = useState({
    role: "",
    experience_level: "Fresher",
    interview_type: "Technical",
  });
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState("checking");

  useEffect(() => {
    getHealth()
      .then((data) => setMode(data.ai_mode))
      .catch(() => setMode("offline"));
  }, []);

  function update(field, value) {
    setForm((previous) => ({ ...previous, [field]: value }));
    setErrors((previous) => ({ ...previous, [field]: "" }));
  }

  function validate() {
    const next = {};
    if (round === "job" && form.role.trim().length < 2) {
      next.role = "Enter the job you want to prepare for.";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  // Aptitude and GD do not use the experience level; the backend just needs a value.
  function buildRequest() {
    if (round === "aptitude") {
      return { role: aptitudeTopic, experience_level: "Fresher", interview_type: "Aptitude" };
    }
    if (round === "gd") {
      return { role: "Group Discussion", experience_level: "Fresher", interview_type: "GD" };
    }
    return {
      role: form.role.trim(),
      experience_level: form.experience_level,
      interview_type: form.interview_type,
    };
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitError("");
    if (!validate()) return;
    setLoading(true);
    try {
      const session = await createInterview(buildRequest());
      navigate(`/interview/${session.id}`, { state: { warning: session.warning } });
    } catch (err) {
      setSubmitError(err.message);
      setLoading(false);
    }
  }

  if (loading) return <LoadingState message="Preparing your questions..." />;

  return (
    <div className="stack narrow">
      <div className="mode-grid">
        {ROUNDS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`mode-card ${round === item.id ? "active" : ""}`}
            onClick={() => {
              setRound(item.id);
              setSubmitError("");
              setErrors({});
            }}
          >
            <span className="mode-number">{item.number}</span>
            <span className="mode-title">{item.title}</span>
            <span className="mode-text">{item.text}</span>
          </button>
        ))}
      </div>

      <div className="page-header">
        <h1 className="page-title">{HEADINGS[round].title}</h1>
        <p className="page-subtitle">{HEADINGS[round].text}</p>
      </div>

      {mode === "demo" ? (
        <div className="banner banner-warn">
          The AI is not connected yet, so questions cannot follow your choice. Add your Gemini key
          to backend/.env and restart the backend.
        </div>
      ) : null}
      {mode === "offline" ? (
        <div className="banner banner-error">
          The backend is not reachable. Start it with: uvicorn app.main:app --reload --port 8000
        </div>
      ) : null}

      <form className="card form" onSubmit={handleSubmit} noValidate>
        {round === "aptitude" ? (
          <div className="field">
            <label htmlFor="topic">Topic</label>
            <select id="topic" value={aptitudeTopic} onChange={(e) => setAptitudeTopic(e.target.value)}>
              {APTITUDE_TOPICS.map((topic) => (
                <option key={topic} value={topic}>
                  {topic}
                </option>
              ))}
            </select>
            <div className="field-hint">Mixed aptitude covers all four areas.</div>
          </div>
        ) : null}

        {round === "gd" ? (
          <p className="muted">Click the button below to explore GD topics and start practicing!</p>
        ) : null}

        {round === "job" ? (
          <>
            <div className="field">
              <label htmlFor="role">Job role</label>
              <input
                id="role"
                value={form.role}
                onChange={(e) => update("role", e.target.value)}
                maxLength={100}
                placeholder="e.g. Data Scientist, Design Engineer, Frontend Developer"
              />
              {errors.role ? <div className="field-error">{errors.role}</div> : null}
            </div>

            <div className="grid grid-2">
              <div className="field">
                <label htmlFor="level">Experience level</label>
                <select
                  id="level"
                  value={form.experience_level}
                  onChange={(e) => update("experience_level", e.target.value)}
                >
                  {LEVELS.map((level) => (
                    <option key={level} value={level}>
                      {level}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label htmlFor="type">Interview type</label>
                <select
                  id="type"
                  value={form.interview_type}
                  onChange={(e) => update("interview_type", e.target.value)}
                >
                  {TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </>
        ) : null}

        {submitError ? (
          <div className="banner banner-error" role="alert">
            {submitError}
          </div>
        ) : null}

        <button className="btn btn-primary" type="submit">
          Start {round === "job" ? "interview" : "round"}
        </button>
      </form>
    </div>
  );
}