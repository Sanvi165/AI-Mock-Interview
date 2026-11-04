export const CRITERIA_LABELS = {
  relevance: "Relevance",
  correctness: "Correctness",
  clarity: "Clarity",
  completeness: "Completeness",
  problem_solving: "Problem solving",
};

export function formatDate(iso) {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

export function formatTimer(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function formatScore(score) {
  if (score === null || score === undefined) return "-";
  return String(Math.round(score * 10) / 10);
}

// Returns a CSS tone name used for colours.
export function scoreTone(score) {
  if (score === null || score === undefined) return "none";
  if (score >= 70) return "good";
  if (score >= 45) return "ok";
  return "low";
}

export function sourceLabel(source) {
  if (source === "gemini") return "AI estimate";
  if (source === "fallback") return "Rule-based estimate (AI unavailable)";
  return "Rule-based estimate (demo mode)";
}

export function statusLabel(status) {
  return status === "completed" ? "Completed" : "In progress";
}