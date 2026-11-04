from app.demo import sample_data
from app.services import ai_service


def _strong_answer(question_text: str) -> str:
    entry = sample_data.find_bank_entry(question_text)
    padding = (
        " For example, in a project I would first apply this approach because it is reliable, "
        "and then I would test it step by step to confirm the result."
    ) * 2
    return entry["model_answer"] + padding


def test_health_reports_demo_mode(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "ai_mode": "demo"}


def test_create_interview_returns_questions(client, setup_payload):
    response = client.post("/api/interviews", json=setup_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["ai_source"] == "demo"
    assert len(body["questions"]) == 3
    assert body["status"] == "in_progress"
    assert "Demo mode" in body["warning"]


def test_invalid_setup_returns_readable_422(client, setup_payload):
    setup_payload["num_questions"] = 0
    response = client.post("/api/interviews", json=setup_payload)
    assert response.status_code == 422
    assert "num_questions" in response.json()["detail"]


def test_empty_answer_is_rejected(client, setup_payload):
    session = client.post("/api/interviews", json=setup_payload).json()
    response = client.post(
        f"/api/interviews/{session['id']}/answers",
        json={"question_id": session["questions"][0]["id"], "answer_text": "   "},
    )
    assert response.status_code == 422
    assert "empty" in response.json()["detail"].lower()


def test_unknown_session_returns_404(client):
    assert client.get("/api/interviews/9999").status_code == 404
    assert client.get("/api/history/9999").status_code == 404


def test_full_interview_flow_and_history(client, setup_payload):
    session = client.post("/api/interviews", json=setup_payload).json()
    session_id = session["id"]
    next_question = session["questions"][0]

    answered = 0
    while next_question and answered < 10:
        response = client.post(
            f"/api/interviews/{session_id}/answers",
            json={
                "question_id": next_question["id"],
                "answer_text": _strong_answer(next_question["text"])
                if sample_data.find_bank_entry(next_question["text"])
                else "I would explain the idea step by step because it is useful, for example in a project.",
                "time_taken_seconds": 30,
            },
        )
        assert response.status_code == 200, response.text
        answered += 1
        next_question = response.json()["next_question"]

    assert answered >= 3

    completed = client.post(f"/api/interviews/{session_id}/complete")
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    assert completed.json()["overall_score"] > 0

    history = client.get("/api/history").json()
    assert len(history) == 1 and history[0]["status"] == "completed"

    detail = client.get(f"/api/history/{session_id}").json()
    assert len(detail["results"]) == answered
    assert detail["results"][0]["evaluation"]["feedback"]["stronger_answer"]

    report = client.get(f"/api/history/{session_id}/report")
    assert report.status_code == 200
    assert "# Mock Interview Report" in report.text


def test_strong_answer_triggers_followup(client, setup_payload):
    session = client.post("/api/interviews", json=setup_payload).json()
    question = session["questions"][0]
    response = client.post(
        f"/api/interviews/{session['id']}/answers",
        json={"question_id": question["id"], "answer_text": _strong_answer(question["text"])},
    )
    body = response.json()
    assert body["adaptive_action"] == "followup"
    assert body["next_question"]["kind"] == "followup"


def test_weak_answer_triggers_simpler_question(client, setup_payload):
    session = client.post("/api/interviews", json=setup_payload).json()
    question = session["questions"][0]
    response = client.post(
        f"/api/interviews/{session['id']}/answers",
        json={"question_id": question["id"], "answer_text": "I do not know."},
    )
    body = response.json()
    assert body["adaptive_action"] == "simpler"
    assert body["next_question"]["kind"] == "simpler"
    assert body["next_question"]["topic"] == question["topic"]


def test_cannot_answer_same_question_twice(client, setup_payload):
    session = client.post("/api/interviews", json=setup_payload).json()
    question = session["questions"][0]
    payload = {"question_id": question["id"], "answer_text": "I do not know."}
    assert client.post(f"/api/interviews/{session['id']}/answers", json=payload).status_code == 200
    assert client.post(f"/api/interviews/{session['id']}/answers", json=payload).status_code == 409


def test_finish_without_answers_is_rejected(client, setup_payload):
    session = client.post("/api/interviews", json=setup_payload).json()
    response = client.post(f"/api/interviews/{session['id']}/complete")
    assert response.status_code == 400


def test_ai_failure_falls_back_to_demo(client, setup_payload, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-test")

    def broken_call(prompt):
        raise ai_service.AIServiceError("Gemini rate limit reached.")

    monkeypatch.setattr(ai_service, "_call_gemini", broken_call)

    response = client.post("/api/interviews", json=setup_payload)
    assert response.status_code == 201
    body = response.json()
    assert body["ai_source"] == "fallback"
    assert "rate limit" in body["warning"]
    assert len(body["questions"]) == 3

    question = body["questions"][0]
    answer = client.post(
        f"/api/interviews/{body['id']}/answers",
        json={"question_id": question["id"], "answer_text": "I would explain it with an example."},
    )
    assert answer.status_code == 200
    assert answer.json()["evaluation"]["source"] == "fallback"



def test_domain_is_optional_and_defaults_to_role(client):
    response = client.post(
        "/api/interviews",
        json={
            "role": "Data Scientist",
            "experience_level": "Fresher",
            "interview_type": "Technical",
            "num_questions": 3,
        },
    )
    assert response.status_code == 201
    assert response.json()["domain"] == "Data Scientist"


def test_ai_works_out_field_from_role(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key-for-test")

    def fake_call(prompt):
        return {
            "field": "Computer Science (Data Science)",
            "questions": [
                {"text": "What is the bias-variance trade-off?", "topic": "Machine Learning", "difficulty": "medium"},
                {"text": "Explain normalization in a database.", "topic": "DBMS", "difficulty": "easy"},
                {"text": "What is the time complexity of binary search?", "topic": "Algorithms", "difficulty": "easy"},
            ],
        }

    monkeypatch.setattr(ai_service, "_call_gemini", fake_call)

    response = client.post(
        "/api/interviews",
        json={
            "role": "Data Scientist",
            "experience_level": "Fresher",
            "interview_type": "Technical",
            "num_questions": 3,
        },
    )
    body = response.json()
    assert body["ai_source"] == "gemini"
    assert body["domain"] == "Computer Science (Data Science)"
    assert [q["topic"] for q in body["questions"]] == ["Machine Learning", "DBMS", "Algorithms"]