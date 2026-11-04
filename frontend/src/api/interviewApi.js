// All backend calls live here. Components never call fetch() directly.
const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const TOKEN_KEY = "mock_interview_token";

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function setToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // storage unavailable: the user will simply have to log in again next time
  }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignore
  }
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  } catch {
    throw new Error(
      "Cannot reach the backend. Make sure it is running: uvicorn app.main:app --reload --port 8000"
    );
  }

  if (!response.ok) {
    // An expired or invalid login: forget it and tell the app to show the login page.
    if (response.status === 401 && token) {
      clearToken();
      window.dispatchEvent(new Event("auth-expired"));
    }
    let message = `Request failed (${response.status}).`;
    try {
      const data = await response.json();
      if (data && typeof data.detail === "string") message = data.detail;
    } catch {
      // response had no JSON body; keep the default message
    }
    throw new Error(message);
  }

  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("application/json") ? response.json() : response.text();
}

// ---------- account ----------
export async function register(username, email, password) {
  const data = await request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  });
  setToken(data.token);
  return data;
}

// identifier = username OR email
export async function login(identifier, password) {
  const data = await request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ identifier, password }),
  });
  setToken(data.token);
  return data;
}

export async function logout() {
  try {
    await request("/api/auth/logout", { method: "POST" });
  } finally {
    clearToken();
  }
}

export const getMe = () => request("/api/auth/me");

// ---------- interviews ----------
export const getHealth = () => request("/api/health");

export const createInterview = (setup) =>
  request("/api/interviews", { method: "POST", body: JSON.stringify(setup) });

export const getInterview = (id) => request(`/api/interviews/${id}`);

export const submitAnswer = (id, payload) =>
  request(`/api/interviews/${id}/answers`, { method: "POST", body: JSON.stringify(payload) });

export const completeInterview = (id) =>
  request(`/api/interviews/${id}/complete`, { method: "POST" });

export const getHistory = () => request("/api/history");

export const getHistoryItem = (id) => request(`/api/history/${id}`);

export const deleteHistoryItem = (id) => request(`/api/history/${id}`, { method: "DELETE" });

export const deleteAllHistory = () => request("/api/history", { method: "DELETE" });

export const seedDemoData = () => request("/api/history/demo-seed", { method: "POST" });

export const getReportText = (id) => request(`/api/history/${id}/report`);

export const getProgress = () => request("/api/progress");

export const getRoadmap = () => request("/api/progress/roadmap");