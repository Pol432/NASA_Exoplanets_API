import pytest
from fastapi.testclient import TestClient

# === IMPORTS AJUSTADOS A TU REPO ===
from app.main import app
from app.db.session import get_db
from app.services.auth import get_current_active_user
from app.services import feedback_service as feedback_service_module
from app.api.api_v1.endpoints import feedback as feedback_router_module

# Si tu API está montada como /api/v1 y el router como /feedback:
BASE_PATH_PREFIX = ""  # ← cambia a "" o "/feedback" si te da 404

# ---------- Dummies ----------
class DummyUser:
    def __init__(self, id: int):
        self.id = id

# ---------- Factories para coincidir con tus Schemas ----------
# Ajusta LLAVES si tus Pydantic requieren más campos obligatorios.
def make_feedback_response(*, feedback_id=1, candidate_id=42, researcher_id=111, **extra):
    data = {
        "id": feedback_id,
        "candidate_id": candidate_id,
        "researcher_id": researcher_id,
        "comment": extra.get("comment", "ok"),
        "score": extra.get("score", 0.9),
        # Ejemplos por si tu schema los exige:
        # "created_at": "2025-01-01T00:00:00Z",
        # "updated_at": "2025-01-01T00:00:00Z",
    }
    data.update(extra)
    return data

def make_consensus_dict(*, score=0.75, votes=10, **extra):
    data = {
        "score": score,
        "votes": votes,
        # "label": "likely",
    }
    data.update(extra)
    return data

def make_stats_dict(*, total=5, avg_score=0.66, positives=3, negatives=2, **extra):
    data = {
        "total": total,
        "avg_score": avg_score,
        "positives": positives,
        "negatives": negatives,
    }
    data.update(extra)
    return data

# ---------- Spy del servicio ----------
class SpyFeedbackService:
    def __init__(self, db):
        self.db = db
        self.calls = []

    def create_feedback(self, feedback_data, researcher_id):
        self.calls.append(("create_feedback", feedback_data, researcher_id))
        return make_feedback_response(
            candidate_id=feedback_data.get("candidate_id", 42),
            researcher_id=researcher_id,
            comment=feedback_data.get("comment", "ok"),
            score=feedback_data.get("score", 0.9),
        )

    def get_feedback_by_candidate(self, candidate_id: int):
        self.calls.append(("get_feedback_by_candidate", candidate_id))
        return [make_feedback_response(candidate_id=candidate_id, researcher_id=1, feedback_id=1)]

    def get_feedback_by_researcher(self, researcher_id: int, skip: int, limit: int):
        self.calls.append(("get_feedback_by_researcher", researcher_id, skip, limit))
        return [make_feedback_response(candidate_id=42, researcher_id=researcher_id, feedback_id=1)]

    def update_feedback(self, feedback_id: int, feedback_update, researcher_id: int):
        self.calls.append(("update_feedback", feedback_id, feedback_update, researcher_id))
        return make_feedback_response(
            feedback_id=feedback_id,
            candidate_id=feedback_update.get("candidate_id", 42),
            researcher_id=researcher_id,
            comment=feedback_update.get("comment", "updated"),
            score=feedback_update.get("score", 0.85),
        )

    def delete_feedback(self, feedback_id: int, researcher_id: int):
        self.calls.append(("delete_feedback", feedback_id, researcher_id))
        return True

    def calculate_consensus_score(self, candidate_id: int):
        self.calls.append(("calculate_consensus_score", candidate_id))
        return make_consensus_dict(score=0.75, votes=10)

    def get_researcher_statistics(self, researcher_id: int):
        self.calls.append(("get_researcher_statistics", researcher_id))
        return make_stats_dict(total=5, avg_score=0.66, positives=3, negatives=2)

    def get_feedback_by_id(self, feedback_id: int):
        self.calls.append(("get_feedback_by_id", feedback_id))
        return make_feedback_response(feedback_id=feedback_id, candidate_id=42, researcher_id=111)

@pytest.fixture(scope="session")
def client():
    return TestClient(app)

@pytest.fixture(scope="session")
def base_path():
    return BASE_PATH_PREFIX

@pytest.fixture()
def test_user():
    return DummyUser(id=111)

@pytest.fixture()
def fake_db():
    return object()

@pytest.fixture()
def overrides(client, test_user, fake_db, monkeypatch):
    # 1) Overrides de dependencias
    app.dependency_overrides[get_db] = lambda: fake_db
    app.dependency_overrides[get_current_active_user] = lambda: test_user

    # 2) Parchear la clase FeedbackService por una fábrica que devuelve SIEMPRE la misma instancia-espía
    spy_instance = SpyFeedbackService(fake_db)

    class SpyFactory:
        def __call__(self, db):
            return spy_instance

    monkeypatch.setattr(feedback_service_module, "FeedbackService", SpyFactory(), raising=True)

    # 3) Exponer el espía en el módulo del router para hacer aserciones
    feedback_router_module._spy = spy_instance

    yield

    app.dependency_overrides.clear()
    if hasattr(feedback_router_module, "_spy"):
        delattr(feedback_router_module, "_spy")
