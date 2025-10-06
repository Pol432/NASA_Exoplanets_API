# tests/api/api_v1/test_feedback_endpoints.py
import pytest
import types
import pytest
from fastapi.testclient import TestClient
from app.main import app

# ======= AJUSTA ESTOS DICCIONARIOS A TUS SCHEMAS =======
# Deben coincidir con ResearcherFeedbackResponse, FeedbackConsensus, ResearcherStats, etc.
MINIMAL_FEEDBACK_RESPONSE = {
    "id": 1,
    "candidate_id": 1001,
    "researcher_id": 42,
    "label": "candidate",            # <--- ajusta (ej. "confirmed" / "false_positive" / etc.)
    "confidence": 0.87,              # <--- ajusta si existe ese campo
    "comments": "Looks promising",   # <--- ajusta
    # agrega/borra campos según tu ResearcherFeedbackResponse
}

MINIMAL_CONSENSUS_RESPONSE = {
    "candidate_id": 1001,
    "consensus_score": 0.72,         # <--- ajusta a las claves de FeedbackConsensus
    "n_votes": 5                     # <--- ajusta
}

MINIMAL_RESEARCHER_STATS = {
    "researcher_id": 42,
    "total_feedback": 7,             # <--- ajusta a las claves de ResearcherStats
    "avg_confidence": 0.81           # <--- ajusta
}
# ========================================================


class FakeFeedbackService:
    """
    Fake que “emula” app.services.feedback_service.FeedbackService
    Cada método devuelve datos mínimos válidos para tus response_model.
    Modifica según tus schemas.
    """
    def __init__(self, db):
        self.db = db
        # flags para verificar que se llamó con lo esperado (opcionales)
        self._called = {}

    def create_feedback(self, feedback_data, researcher_id):
        self._called['create_feedback'] = (feedback_data, researcher_id)
        # devuelve lo que exige ResearcherFeedbackResponse
        return {**MINIMAL_FEEDBACK_RESPONSE, "researcher_id": researcher_id}

    def get_feedback_by_candidate(self, candidate_id):
        self._called['get_feedback_by_candidate'] = (candidate_id,)
        return [MINIMAL_FEEDBACK_RESPONSE]

    def get_feedback_by_researcher(self, researcher_id, skip, limit):
        self._called['get_feedback_by_researcher'] = (researcher_id, skip, limit)
        return [MINIMAL_FEEDBACK_RESPONSE]

    def update_feedback(self, feedback_id, feedback_update, researcher_id):
        self._called['update_feedback'] = (feedback_id, feedback_update, researcher_id)
        return {**MINIMAL_FEEDBACK_RESPONSE, "id": feedback_id, "researcher_id": researcher_id}

    def delete_feedback(self, feedback_id, researcher_id):
        self._called['delete_feedback'] = (feedback_id, researcher_id)
        return None

    def calculate_consensus_score(self, candidate_id):
        self._called['calculate_consensus_score'] = (candidate_id,)
        # el endpoint arma FeedbackConsensus(candidate_id=..., **consensus_data)
        return {k: v for k, v in MINIMAL_CONSENSUS_RESPONSE.items() if k != "candidate_id"}

    def get_researcher_statistics(self, researcher_id):
        self._called['get_researcher_statistics'] = (researcher_id,)
        # el endpoint arma ResearcherStats(researcher_id=..., **stats_data)
        return {k: v for k, v in MINIMAL_RESEARCHER_STATS.items() if k != "researcher_id"}

    def get_feedback_by_id(self, feedback_id):
        self._called['get_feedback_by_id'] = (feedback_id,)
        if feedback_id == 404:
            return None
        return {**MINIMAL_FEEDBACK_RESPONSE, "id": feedback_id}


@pytest.fixture(autouse=True)
def patch_feedback_service(monkeypatch):
    """
    Reemplaza FeedbackService en el módulo del router:
    app.api.api_v1.endpoints.feedback.FeedbackService -> FakeFeedbackService
    """
    import app.api.api_v1.endpoints.feedback as feedback_ep
    monkeypatch.setattr(feedback_ep, "FeedbackService", FakeFeedbackService)
    yield

@pytest.fixture
def client():
    """Siempre un TestClient real, no un Mock."""
    return TestClient(app)

def test_submit_feedback_201(client):
    payload = {
        # ===== AJUSTA ESTO A ResearcherFeedbackCreate =====
        "candidate_id": 1001,
        "label": "candidate",
        "confidence": 0.9,
        "comments": "auto test"
        # ================================================
    }
    res = client.post("/api/v1/feedback/submit", json=payload)
    assert res.status_code == 201
    body = res.json()
    # checks mínimos (ajusta claves)
    assert body["candidate_id"] == 1001


def test_get_candidate_feedback(client):
    res = client.get("/api/v1/feedback/candidate/1001")
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list)
    assert body and body[0]["candidate_id"] == 1001


def test_get_my_feedback(client):
    res = client.get("/api/v1/feedback/my-feedback?skip=0&limit=50")
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list)


def test_update_feedback(client):
    payload = {
        # ===== AJUSTA ESTO A ResearcherFeedbackUpdate =====
        "label": "confirmed",
        "confidence": 0.95,
        "comments": "updated comment"
        # ================================================
    }
    res = client.put("/api/v1/feedback/1", json=payload)
    assert res.status_code == 200
    assert res.json()["id"] == 1


def test_delete_feedback(client):
    res = client.delete("/api/v1/feedback/1")
    assert res.status_code == 200
    assert res.json()["message"] == "Feedback deleted successfully"


def test_get_consensus_score(client):
    res = client.get("/api/v1/feedback/consensus/1001")
    assert res.status_code == 200
    body = res.json()
    # Debe contener candidate_id y los campos de tu FeedbackConsensus
    assert body["candidate_id"] == 1001


def test_get_researcher_stats(client):
    res = client.get("/api/v1/feedback/researcher/42/stats")
    assert res.status_code == 200
    assert res.json()["researcher_id"] == 42


def test_get_my_stats(client):
    res = client.get("/api/v1/feedback/my-stats")
    assert res.status_code == 200
    assert res.json()["researcher_id"] == 42


def test_get_feedback_by_id_200(client):
    res = client.get("/api/v1/feedback/1")
    assert res.status_code == 200
    assert res.json()["id"] == 1


def test_get_feedback_by_id_404(client):
    res = client.get("/api/v1/feedback/404")
    assert res.status_code == 404
    assert res.json()["detail"] == "Feedback not found"
