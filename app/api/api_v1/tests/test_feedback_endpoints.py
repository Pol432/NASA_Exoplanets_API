from fastapi import status
from app.api.api_v1.endpoints import feedback as feedback_router_module
BASE = "/api/v1/feedback"  # <- forzado

def test_submit_feedback_201(client, overrides):
    res = client.post(f"{BASE}/submit", json=payload_create())
    assert res.status_code == status.HTTP_201_CREATED

def payload_create():
    return {
        "candidate_id": 42,      # ← Ajusta si tu ResearcherFeedbackCreate exige otras llaves
        "comment": "Muy buen candidato",
        "score": 0.93
    }

def payload_update():
    return {
        "comment": "Actualizado",
        "score": 0.81
    }

def test_submit_feedback_201(client, overrides, base_path):
    res = client.post(f"{base_path}/submit", json=payload_create())
    assert res.status_code == status.HTTP_201_CREATED
    body = res.json()
    assert body["candidate_id"] == 42
    assert "id" in body
    assert ("create_feedback", payload_create(), 111) in feedback_router_module._spy.calls

def test_get_candidate_feedback_200(client, overrides, base_path):
    res = client.get(f"{base_path}/candidate/77")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert isinstance(data, list) and len(data) >= 1
    assert data[0]["candidate_id"] == 77
    assert ("get_feedback_by_candidate", 77) in feedback_router_module._spy.calls

def test_get_my_feedback_200(client, overrides, base_path):
    res = client.get(f"{base_path}/my-feedback?skip=5&limit=10")
    assert res.status_code == status.HTTP_200_OK
    assert ("get_feedback_by_researcher", 111, 5, 10) in feedback_router_module._spy.calls

def test_update_feedback_200(client, overrides, base_path):
    res = client.put(f"{base_path}/123", json=payload_update())
    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    assert body["id"] == 123
    assert body["comment"] == "Actualizado"
    assert ("update_feedback", 123, payload_update(), 111) in feedback_router_module._spy.calls

def test_delete_feedback_200(client, overrides, base_path):
    res = client.delete(f"{base_path}/999")
    assert res.status_code == status.HTTP_200_OK
    assert res.json()["message"].lower().startswith("feedback deleted")
    assert ("delete_feedback", 999, 111) in feedback_router_module._spy.calls

def test_get_consensus_200(client, overrides, base_path):
    res = client.get(f"{base_path}/consensus/55")
    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    assert body["candidate_id"] == 55
    assert "score" in body and "votes" in body
    assert ("calculate_consensus_score", 55) in feedback_router_module._spy.calls

def test_get_researcher_stats_200(client, overrides, base_path):
    res = client.get(f"{base_path}/researcher/222/stats")
    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    assert body["researcher_id"] == 222
    assert "total" in body and "avg_score" in body
    assert ("get_researcher_statistics", 222) in feedback_router_module._spy.calls

def test_get_my_stats_200(client, overrides, base_path):
    res = client.get(f"{base_path}/my-stats")
    assert res.status_code == status.HTTP_200_OK
    body = res.json()
    assert body["researcher_id"] == 111
    assert ("get_researcher_statistics", 111) in feedback_router_module._spy.calls

def test_get_feedback_by_id_200_y_404(client, overrides, base_path, monkeypatch):
    spy = feedback_router_module._spy

    def _ok(feedback_id):
        spy.calls.append(("get_feedback_by_id", feedback_id))
        return {"id": feedback_id, "candidate_id": 42, "researcher_id": 111, "comment": "x", "score": 0.5}

    def _none(feedback_id):
        spy.calls.append(("get_feedback_by_id", feedback_id))
        return None

    monkeypatch.setattr(spy, "get_feedback_by_id", _ok, raising=False)
    r1 = client.get(f"{base_path}/101")
    assert r1.status_code == 200
    assert r1.json()["id"] == 101

    monkeypatch.setattr(spy, "get_feedback_by_id", _none, raising=False)
    r2 = client.get(f"{base_path}/404")
    assert r2.status_code == 404
