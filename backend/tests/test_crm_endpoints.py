import pytest
from fastapi.testclient import TestClient

from app.main import app

ADMIN_EMAIL = "charanjeet.s7730@gmail.com"
ADMIN_PASSWORD = "123456"


@pytest.fixture(scope="module")
def client():
    with TestClient(app, base_url="http://localhost") as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers(client):
    res = client.post("/api/v1/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert res.status_code == 200, res.text
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_login_returns_token(auth_headers):
    assert auth_headers["Authorization"].startswith("Bearer ")


def test_lead_lifecycle(client, auth_headers):
    create = client.post(
        "/api/v1/leads",
        json={"name": "Pytest Lead", "company": "Pytest Co", "source": "manual", "value": 500},
        headers=auth_headers,
    )
    assert create.status_code == 201, create.text
    lead = create.json()
    assert lead["status"] == "new"
    lead_id = lead["id"]

    listing = client.get("/api/v1/leads", headers=auth_headers)
    assert listing.status_code == 200
    assert any(l["id"] == lead_id for l in listing.json()["leads"])

    patch = client.patch(f"/api/v1/leads/{lead_id}", json={"status": "qualified"}, headers=auth_headers)
    assert patch.status_code == 200
    assert patch.json()["status"] == "qualified"

    events = client.get(f"/api/v1/leads/{lead_id}/events", headers=auth_headers)
    assert events.status_code == 200
    event_types = [e["type"] for e in events.json()["events"]]
    assert "created" in event_types
    assert "status_changed" in event_types

    delete = client.delete(f"/api/v1/leads/{lead_id}", headers=auth_headers)
    assert delete.status_code == 200
    assert delete.json()["success"] is True


def test_lead_invalid_source_rejected(client, auth_headers):
    res = client.post("/api/v1/leads", json={"name": "Bad Source", "source": "not_a_real_source"}, headers=auth_headers)
    assert res.status_code == 400


def test_deal_lifecycle(client, auth_headers):
    create = client.post("/api/v1/deals", json={"name": "Pytest Deal", "company": "Pytest Co", "value": 1000}, headers=auth_headers)
    assert create.status_code == 201, create.text
    deal_id = create.json()["id"]
    assert create.json()["stage"] == "lead"

    patch = client.patch(f"/api/v1/deals/{deal_id}", json={"stage": "qualified"}, headers=auth_headers)
    assert patch.status_code == 200
    assert patch.json()["stage"] == "qualified"

    delete = client.delete(f"/api/v1/deals/{deal_id}", headers=auth_headers)
    assert delete.status_code == 200


def test_campaign_lifecycle(client, auth_headers):
    create = client.post("/api/v1/dashboard/campaigns", json={"name": "Pytest Campaign", "channel": "voice"}, headers=auth_headers)
    assert create.status_code == 200, create.text
    campaign_id = create.json()["id"]
    assert create.json()["status"] == "paused"

    toggle = client.patch(f"/api/v1/dashboard/campaigns/{campaign_id}/toggle", headers=auth_headers)
    assert toggle.status_code == 200
    assert toggle.json()["status"] == "running"

    delete = client.delete(f"/api/v1/dashboard/campaigns/{campaign_id}", headers=auth_headers)
    assert delete.status_code == 200


def test_integrations_report_not_configured(client, auth_headers):
    listing = client.get("/api/v1/integrations", headers=auth_headers)
    assert listing.status_code == 200
    channels = {i["channel"]: i for i in listing.json()["integrations"]}
    assert "facebook" in channels
    assert channels["facebook"]["status"] == "not_configured"
    assert "FACEBOOK_APP_ID" in channels["facebook"]["missing_configuration"]

    connect = client.post("/api/v1/integrations/facebook/connect", headers=auth_headers)
    assert connect.status_code == 501
    assert "not configured" in connect.json()["detail"]


def test_dashboard_overview_reflects_real_counts(client, auth_headers):
    before = client.get("/api/v1/dashboard/overview", headers=auth_headers).json()
    probe = client.post("/api/v1/leads", json={"name": "Overview Probe", "source": "manual"}, headers=auth_headers).json()
    try:
        after = client.get("/api/v1/dashboard/overview", headers=auth_headers).json()
        assert after["todayLeads"] == before["todayLeads"] + 1
    finally:
        client.delete(f"/api/v1/leads/{probe['id']}", headers=auth_headers)
