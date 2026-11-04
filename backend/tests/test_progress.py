def test_progress_is_empty_at_start(client):
    body = client.get("/api/progress").json()
    assert body["total_sessions"] == 0
    assert body["average_score"] is None
    assert body["sessions"] == []

    roadmap = client.get("/api/progress/roadmap").json()
    assert roadmap["items"] == []
    assert roadmap["message"]


def test_demo_seed_populates_progress(client):
    assert client.post("/api/history/demo-seed").json() == {"created": 4}

    body = client.get("/api/progress").json()
    assert body["total_sessions"] == 4
    assert body["completed_sessions"] == 4
    assert len(body["sessions"]) == 4
    assert body["topics"]
    assert 0 <= body["average_score"] <= 100
    assert body["improvement"] > 0  # seeded sessions improve over time


def test_roadmap_is_prioritized_weakest_first(client):
    client.post("/api/history/demo-seed")
    items = client.get("/api/progress/roadmap").json()["items"]
    assert items
    assert [item["priority"] for item in items] == list(range(1, len(items) + 1))
    averages = [item["average_score"] for item in items]
    assert averages == sorted(averages)
    assert all(item["practice_questions"] for item in items)
    assert all(item["study_focus"] for item in items)


def test_delete_all_removes_everything(client):
    client.post("/api/history/demo-seed")
    assert client.delete("/api/history").json() == {"deleted": 4}
    assert client.get("/api/history").json() == []
    assert client.get("/api/progress").json()["total_sessions"] == 0


def test_delete_single_session(client):
    client.post("/api/history/demo-seed")
    first_id = client.get("/api/history").json()[0]["id"]
    assert client.delete(f"/api/history/{first_id}").status_code == 200
    assert client.delete(f"/api/history/{first_id}").status_code == 404
    assert len(client.get("/api/history").json()) == 3