import { Link } from "react-router-dom";

const FEATURES = [
  {
    title: "Questions on your topics",
    text: "Tell the app your role, branch and topics. It generates questions based on exactly what you write.",
  },
  {
    title: "Adaptive follow-ups",
    text: "Answer well and get a deeper follow-up. Struggle and get a simpler question on the same topic.",
  },
  {
    title: "Rubric-based evaluation",
    text: "Every answer is scored on relevance, correctness, clarity, completeness and problem solving.",
  },
  {
    title: "Correct answers",
    text: "See an example of a stronger answer for every question and compare it with yours.",
  },
  {
    title: "Skill gap roadmap",
    text: "Weak topics become a prioritized study list with practice questions.",
  },
  {
    title: "Speech and video",
    text: "Questions can be read aloud, answers can be spoken, and you can record yourself (optional).",
  },
  {
    title: "History and progress",
    text: "Review past interviews from the sidebar and track your scores in charts.",
  },
  {
    title: "Downloadable report",
    text: "Download your interview report as Markdown or print it as a PDF.",
  },
];

const STEPS = [
  "Enter your role, branch and topics.",
  "Answer one question at a time by typing or speaking.",
  "Get instant feedback, then adaptive follow-up questions.",
  "Finish, review your answers and follow your roadmap.",
];

export default function Home() {
  return (
    <div className="stack">
      <section className="hero card">
        <h1>Practise interviews. Get honest feedback. Improve.</h1>
        <p>
          An AI-powered mock interview app for students and job seekers. Enter your role and
          topics, answer the questions, and get feedback you can act on.
        </p>
        <div className="row hero-actions">
          <Link className="btn btn-primary" to="/setup">
            Start a mock interview
          </Link>
        </div>
      </section>

      <section>
        <h2 className="section-title">What you can do</h2>
        <div className="grid grid-4">
          {FEATURES.map((feature) => (
            <div className="card feature-card" key={feature.title}>
              <h3>{feature.title}</h3>
              <p className="muted">{feature.text}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="section-title">How it works</h2>
        <div className="grid grid-4">
          {STEPS.map((step, index) => (
            <div className="card" key={step}>
              <div className="step-number">{index + 1}</div>
              <p>{step}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}